import os

import nest_asyncio
import yaml
from autochat import Autochat, Message
from autochat.chat import StopLoopException

from back.models import Chart, Conversation, ConversationMessage, Query
from chat.dbt_utils import DBT
from chat.lock import STATUS, StopException, emit_status
from chat.notes import Notes
from chat.tools.database import DatabaseTool
from chat.tools.echarts import EchartsTool
from chat.tools.workspace import WorkspaceTool
from chat.utils import parse_answer_text

# Workaround because of eventlet doesn't support loop in loop ?
nest_asyncio.apply()

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
        self.datalake = self.conversation.database.create_datalake()
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

        chatbot.simple_response_callback = lambda response: Message(
            role="user",
            content="Only messages from 'answer' function call are\
            visible to the user. Use it to answer the user.",
        )

        chatbot.add_tool(
            DatabaseTool(self.session, self.conversation.database), "database"
        )
        chatbot.add_function(self.save_to_memory)
        chatbot.add_function(self.submit)
        chatbot.add_function(self.answer)
        chatbot.add_function(self.ask_user)
        chatbot.add_tool(WorkspaceTool(self.session, self.conversation.id), "workspace")
        chatbot.add_tool(
            EchartsTool(self.session, self.conversation.database),
            "echarts",
        )
        if self.dbt:
            chatbot.add_tool(self.dbt, self.conversation.database.name)
        if self.conversation.project:
            notes = Notes(self.session, chatbot, self.conversation.project)
            chatbot.add_tool(notes, "Notes")

        if self.model:
            chatbot.model = self.model

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
        queryId: int,
    ):
        """
        Give the final response from the user demand/query
        Args:
            queryId: The id of the query to execute
        """  # noqa: E501
        query = self.session.query(Query).filter_by(id=queryId).first()
        if not query:
            raise ValueError(f"Query with id {queryId} not found")
        # We update the message with the query id
        from_response.query_id = query.id
        from_response.isAnswer = True
        raise StopLoopException("We want to stop after submitting")

    def ask_user(self, question: str, from_response: Message):
        """
        Ask the user a question. Use it to ask for confirmation, for ambiguous queries,\
        etc.
        Use it only when it strictly necessary.
        Args:
            question: The question to ask the user
        """
        from_response.isAnswer = True  # TODO: is answer is not the correct termilogy
        raise StopLoopException("We want the user to answer")

    def answer(
        self,
        text: str,
        from_response: Message,
    ):
        """
        Give the final response from the user demand/query as a text.
        You can insert a query in the text using the <QUERY:{query_id}> tag.
        You can insert a chart in the text using the <CHART:{chart_id}> tag.
        Replace {query_id} and {chart_id} with the actual query id and chart id.
        You can only insert one query and one chart per message.
        Show the query only if the user asked for it.
        Show the chart only if the user asked for it or if that make sense to have it.
        """

        chunks = parse_answer_text(text)
        # Check query_id & chart_id
        for chunk in chunks:
            if chunk["type"] == "query":
                # extract the query id from the text
                query_id = chunk["query_id"]
                query = (
                    self.session.query(Query)
                    .join(ConversationMessage, Query.conversation_messages)
                    .filter(
                        Query.id == query_id,
                        ConversationMessage.conversationId == self.conversation.id,
                    )
                    .first()
                )
                if not query:
                    raise ValueError(
                        f"Query with id {query_id} not found in this conversation"
                    )

            if chunk["type"] == "chart":
                # extract the chart id from the text
                chart_id = chunk["chart_id"]
                # verify chart exists and belongs to this conversation
                chart = (
                    self.session.query(Chart)
                    .join(ConversationMessage, Chart.conversation_messages)
                    .filter(
                        Chart.id == chart_id,
                        ConversationMessage.conversationId == self.conversation.id,
                    )
                    .first()
                )
                if not chart:
                    raise ValueError(
                        f"Chart with id {chart_id} not found in this conversation"
                    )

        from_response.isAnswer = True
        raise StopLoopException("We want to stop after submitting")

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
            import traceback

            traceback.print_exc()
            raise

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
