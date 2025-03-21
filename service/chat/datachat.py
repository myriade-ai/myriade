import os

import yaml
from autochat import Autochat, Message
from autochat.chat import StopLoopException

from back.datalake import DatalakeFactory
from back.models import Conversation, ConversationMessage, Query
from chat.dbt_utils import DBT
from chat.lock import STATUS, StopException, emit_status
from chat.notes import Notes
from chat.tools.database import DatabaseTool
from chat.tools.workspace import WorkspaceTool

AUTOCHAT_PROVIDER = os.getenv("AUTOCHAT_PROVIDER", "openai")


class DatabaseChat:
    """
    Chatbot assistant with a database, execute functions.
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
        if (
            self.conversation.database.dbt_catalog
            and self.conversation.database.dbt_manifest
        ):
            self.dbt = DBT(
                catalog=self.conversation.database.dbt_catalog,
                manifest=self.conversation.database.dbt_manifest,
            )

    def __del__(self):
        # On destruct, close the engine
        if hasattr(self, "datalake"):
            self.datalake.dispose()

    def _create_conversation(
        self, databaseId, name=None, project_id=None, user_id=None
    ):
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
            del self.stop_flags[str(self.conversation.id)]  # Remove the stop flag
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
        chatbot.add_tool(
            DatabaseTool(self.session, self.conversation.database), "database"
        )
        chatbot.add_function(self.save_to_memory)
        chatbot.add_function(self.submit)
        chatbot.add_tool(WorkspaceTool(self.session, self.conversation.id), "workspace")
        chatbot.add_function(self.render_echarts)
        if self.dbt:
            chatbot.add_tool(self.dbt, self.conversation.database.name)
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

    def save_to_memory(self, text: str):
        """
        Add a text to the AI's memory
        Args:
            text: The text to add to the memory
        """
        if self.conversation.database.memory is None:
            self.conversation.database.memory = text
        else:
            self.conversation.database.memory += "\n" + text
        self.session.commit()

    def submit(
        self,
        from_response: Message,
        query: str,
        name: str | None = None,
    ):
        """
        Give the final response from the user demand/query
        Args:
            query: The SQL query string to be executed. Don't forget to escape this if you use double quote.
            name: The name/title of the query. 'SQL' only for now
        """  # noqa: E501
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

    def render_echarts(
        self,
        chart_options: dict,
        sql: str,
        from_response: Message | None = None,
    ):
        """
        Display a chart (using Echarts 4).
        Provide the chart_options without the "dataset" parameter
        We will SQL result to fill the dataset.source automatically
        Don't forget to Map from Data to Charts (series.encode)
        Don't use specific color in the chart_options unless the user asked for it
        When creating bar charts with ECharts, make sure to set the correct axis types.
        For categorical data (like driver names) use 'category' type on the x-axis when displaying bars vertically, or on the y-axis when displaying bars horizontally.
        For numerical data (like wins or points) use 'value' type on the corresponding axis.
        Also verify that the encode properties correctly map your data fields to the appropriate axes ('x' for categories, 'y' for values in vertical bar charts; reversed in horizontal bar charts).
        Args:
            chart_options: The options of the chart
            sql: The SQL query to execute
        """  # noqa: E501
        # Execute SQL query
        rows, _ = self.datalake.query(sql)

        # Fill the dataset
        chart_options["dataset"] = {
            "source": rows,
        }
        from_response.isAnswer = True
        # We want to stop after rendering the chart
        raise StopLoopException("We want to stop after rendering the chart")

    def _run_conversation(self):
        emit_status(self.conversation.id, STATUS.RUNNING)
        try:
            messages = [m.to_autochat_message() for m in self.conversation.messages]
            self.chatbot.load_messages(messages)
            for m in self.chatbot.run_conversation():
                self.check_stop_flag()
                # We re-emit the status in case the user has refreshed the page
                emit_status(self.conversation.id, STATUS.RUNNING)
                message = ConversationMessage.from_autochat_message(m)
                message.conversationId = self.conversation.id
                self.session.add(message)
                self.session.commit()
                yield message
            emit_status(self.conversation.id, STATUS.CLEAR)
        except Exception as e:
            emit_status(self.conversation.id, STATUS.ERROR, e)
            raise e

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
