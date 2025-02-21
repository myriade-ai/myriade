import io
import json
import os

import requests
import yaml
from autochat import Autochat, Message
from autochat.chat import StopLoopException
from PIL import Image as PILImage

from back.datalake import DatalakeFactory
from back.models import Conversation, ConversationMessage, Query
from chat.dbt_utils import DBT
from chat.lock import StopException
from chat.notes import Notes
from chat.render import render_chart
from chat.sql_utils import run_sql

# Load functions from a predefined path, independent of the current working directory

FUNCTIONS = {}
functions_path = os.path.join(os.path.dirname(__file__), "functions")
for filename in os.listdir(functions_path):
    with open(os.path.join(functions_path, filename)) as f:
        FUNCTIONS[filename[:-5]] = json.load(f)

AUTOCHAT_PROVIDER = os.getenv("AUTOCHAT_PROVIDER", "openai")


def python_transform(code, result):
    # Create a local namespace for execution
    local_namespace = {"result": result}

    # Compile the code object once for better performance
    code_obj = compile(code, "<string>", "exec")

    # Execute the data_preprocessing code
    exec(code_obj, {}, local_namespace)

    # Retrieve the processed result
    return local_namespace.get("processed_result")


def fetch_chart_code_sample(chart_type: str) -> str:
    return requests.get(
        f"https://www.fusioncharts.com/dev/portal/attribute/{chart_type.lower()}/code"
    ).json()["json"]


class DatabaseChat:
    """
    Chatbot assistant with a database, execute functions.
    - SQL_QUERY: execute sql query and return the result (size limited)
    - SAVE_TO_MEMORY: save any text to memory
    - PLOT_WIDGET: plot a widget
    """

    def __init__(
        self,
        session,
        database_id,
        conversation_id=None,
        stop_flags=None,
        model=None,
        project_id=None,
        user_id=None,
    ):
        self.session = session
        if conversation_id is None:
            # Create conversation object
            self.conversation = self._create_conversation(
                databaseId=database_id, project_id=project_id, user_id=user_id
            )
        else:
            self.conversation = (
                self.session.query(Conversation).filter_by(id=conversation_id).first()
            )

        # Add a datalake object to the request
        self.datalake = DatalakeFactory.create(
            self.conversation.database.engine,
            **self.conversation.database.details,
        )
        if stop_flags is None:
            self.stop_flags = {}
        else:
            self.stop_flags = stop_flags
        self.model = model

        self.dbt = None
        if self.conversation.database.dbt_catalog:
            self.dbt = DBT(
                catalog=self.conversation.database.dbt_catalog,
                manifest=self.conversation.database.dbt_manifest,
            )

    def __del__(self):
        # On destruct, close the engine
        if hasattr(self, "datalake"):
            self.datalake.dispose()

    def _create_conversation(self, databaseId, name=None, project_id=None, user_id=None):
        # Create conversation object
        conversation = Conversation(
            databaseId=databaseId,
            ownerId=user_id,
            name=name,
            projectId=project_id,
        )
        self.session.add(conversation)
        self.session.commit()
        return conversation

    def check_stop_flag(self):
        if self.stop_flags.get(str(self.conversation.id)):
            raise StopException("Query stopped by user")

    @property
    def context(self):
        context = {
            "DATABASE": {
                "name": self.conversation.database.name,
                "engine": self.conversation.database.engine,
            },
            "MEMORY": self.conversation.database.memory,
        }
        if self.conversation.project:
            context["PROJECT"] = {
                "name": self.conversation.project.name,
                "description": self.conversation.project.description,
                "tables": [
                    {"schema": table.schemaName, "table": table.tableName}
                    for table in self.conversation.project.tables
                ],
            }

        return yaml.dump(context)

    @property
    def chatbot(self):
        messages = [m.to_autochat_message() for m in self.conversation.messages]
        chatbot = Autochat.from_template(
            os.path.join(os.path.dirname(__file__), "..", "chat", "chat_template.txt"),
            provider=AUTOCHAT_PROVIDER,
            context=self.context,
            messages=messages,
        )
        chatbot.add_function(self.sql_query, FUNCTIONS["SQL_QUERY"])
        chatbot.add_function(self.save_to_memory, FUNCTIONS["SAVE_TO_MEMORY"])
        chatbot.add_function(self.plot_widget, FUNCTIONS["PLOT_WIDGET"])
        chatbot.add_function(self.submit, FUNCTIONS["SUBMIT"])
        if self.dbt:
            chatbot.add_function(self.dbt.fetch_model_list)
            chatbot.add_function(self.dbt.search_models)
            chatbot.add_function(self.dbt.fetch_model)
        if self.conversation.project:
            notes = Notes(self.session, chatbot, self.conversation.project)
            chatbot.add_tool(notes, "Notes")

        if self.model:
            chatbot.model = self.model

        def message_is_answer(function_call, function_response):
            if function_call.content:
                return function_call.content.startswith("<ANSWER>")
            return False

        chatbot.should_pause_conversation = message_is_answer
        return chatbot

    def sql_query(
        self, query: str = "", name: str = None, from_response: Message = None
    ):
        _query = Query(
            query=name,
            databaseId=self.conversation.databaseId,
            sql=query,
        )
        self.session.add(_query)
        self.session.commit()

        if from_response:
            # We update the message with the query id
            from_response.query_id = _query.id

        output, _ = run_sql(self.datalake, query)
        return output

    def save_to_memory(self, text: str):
        if self.conversation.database.memory is None:
            self.conversation.database.memory = text
        else:
            self.conversation.database.memory += "\n" + text
        self.session.commit()

    def submit(self, query: str = "", name: str = None, from_response: Message = None):
        _query = Query(
            query=name,
            databaseId=self.conversation.databaseId,
            sql=query,
        )
        self.session.add(_query)
        self.session.commit()

        # We update the message with the query id
        from_response.query_id = _query.id
        raise StopLoopException("We want to stop after submitting")
        return

    def plot_widget(
        self,
        caption: str,
        outputType: str,
        sql: str,
        params: dict = None,
        data_preprocessing: str = None,
        from_response: Message = None,
    ):
        """TODO: add verification on the widget parameters and the sql query"""
        # Execute SQL query
        rows, _ = self.datalake.query(sql)

        if data_preprocessing:
            # Fields can be "data", "categories", "dataset", ..
            data_fields = python_transform(data_preprocessing, rows)
            if isinstance(data_fields, list):
                data_fields = {"data": data_fields}

        # Generate FusionCharts configuration
        chart_config = {
            "type": outputType.lower(),
            "renderAt": "chart-container",
            "width": "100%",
            "height": "400",
            "dataFormat": "json",
            "dataSource": {
                "chart": {
                    "caption": caption,
                    **params,
                    "theme": "fusion",
                },
                **data_fields,
            },
        }

        sample_code = fetch_chart_code_sample(outputType.lower())
        chart_image_bytes = render_chart(chart_config)
        image = PILImage.open(io.BytesIO(chart_image_bytes))
        return Message(
            name="PLOT_WIDGET",
            role="function",
            content=f"# chart_config\n{json.dumps(chart_config)}\n\n# sample_code for {outputType}\n{sample_code}",
            function_call_id=from_response.function_call_id,
            data=chart_config,
            image=image,
        )

    def _run_conversation(self):
        # Message
        messages = [m.to_autochat_message() for m in self.conversation.messages]
        self.chatbot.load_messages(messages)
        for m in self.chatbot.run_conversation():
            self.check_stop_flag()
            message = ConversationMessage.from_autochat_message(m)
            message.conversationId = self.conversation.id
            self.session.add(message)
            self.session.commit()
            yield message

    def ask(self, question: str):
        if not self.conversation.name:
            self.conversation.name = question

        # If message is instance of string, then convert to ConversationMessage
        message = ConversationMessage(
            role="user",
            content=question,
            conversationId=self.conversation.id,
        )
        self.session.add(message)
        self.session.commit()
        yield message

        yield from self._run_conversation()
