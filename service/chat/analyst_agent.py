import datetime
import logging
import os

import nest_asyncio
import yaml
from agentlys import Agentlys, Message
from agentlys.chat import StopLoopException
from agentlys_tools.code_editor import CodeEditor

from app import socketio
from back.utils import get_tables_metadata_from_catalog
from chat.lock import STATUS, StopException, emit_status
from chat.notes import Notes
from chat.proxy_provider import ProxyProvider
from chat.tools.catalog import CatalogTool
from chat.tools.database import DatabaseTool
from chat.tools.dbt import DBT
from chat.tools.echarts import EchartsTool
from chat.tools.quality import SemanticModel
from chat.tools.workspace import WorkspaceTool
from chat.utils import parse_answer_text
from models import Chart, Conversation, ConversationMessage, Query

logger = logging.getLogger(__name__)

# Workaround because of eventlet doesn't support loop in loop ?
nest_asyncio.apply()

AGENTLYS_PROVIDER = os.getenv("AGENTLYS_PROVIDER", "proxy")


def think(thought: str) -> None:
    """
    Think about the task at hand. It helps to reflect or decompose the situation.
    Args:
        thought: A thought to think about.
    """


def get_date() -> str:
    """
    Get the current date as a string.
    Returns:
        the current date string in YYYY-MM-DD format
    """
    return datetime.datetime.now().strftime("%Y-%m-%d")


def ask_user(question: str, from_response: Message):
    """
    Ask the user a question. Use it to ask for confirmation, for ambiguous queries,\
    etc.
    Use it only when it strictly necessary.
    Args:
        question: The question to ask the user
    """
    from_response.isAnswer = True  # TODO: is answer is not the correct termilogy
    raise StopLoopException("We want the user to answer")


class DataAnalystAgent:
    """
    Chatbot assistant with a database, execute functions.
    """

    def __init__(
        self,
        session,
        conversation: Conversation,
        model=None,
    ):
        self.session = session
        self.conversation = conversation

        # Handle custom proxy provider

        logger.info(
            "AGENTLYS_PROVIDER configured", extra={"provider": AGENTLYS_PROVIDER}
        )

        if AGENTLYS_PROVIDER == "proxy":
            provider = ProxyProvider
        else:
            provider = AGENTLYS_PROVIDER

        self.agent = Agentlys.from_template(
            os.path.join(os.path.dirname(__file__), "..", "chat", "chat_template.txt"),
            provider=provider,
            context=self.context,
            use_tools_only=True,
            model=model,
        )

        self.agent.simple_response_callback = lambda response: Message(
            role="user",
            content="Only messages from 'answer' function call are\
            visible to the user. Use it to answer the user.",
        )

        tables_metadata = get_tables_metadata_from_catalog(
            self.conversation.database.id
        )
        self.agent.add_tool(
            DatabaseTool(self.session, self.conversation.database, tables_metadata),
            "database",
        )
        self.agent.add_function(think)
        self.agent.add_function(get_date)
        self.agent.add_function(self.answer)
        self.agent.add_function(ask_user)
        self.agent.add_tool(
            WorkspaceTool(self.session, self.conversation.id), "workspace"
        )
        self.agent.add_tool(
            EchartsTool(self.session, self.conversation.database),
            "echarts",
        )
        semantic_model = SemanticModel(
            self.session, self.conversation.id, self.conversation.databaseId
        )
        self.agent.add_tool(semantic_model, "semantic_model")
        catalog_tool = CatalogTool(self.session, self.conversation.database)
        self.agent.add_tool(catalog_tool, "catalog")

        if self.conversation.database.dbt_repo_path:
            dbt = DBT(
                catalog=self.conversation.database.dbt_catalog,
                manifest=self.conversation.database.dbt_manifest,
                repo_path=self.conversation.database.dbt_repo_path,
                database_config={
                    "engine": self.conversation.database.engine,
                    "details": self.conversation.database.details,
                },
            )
            self.agent.add_tool(dbt, "dbt")

            code_editor = CodeEditor(
                self.conversation.database.dbt_repo_path,
            )
            self.agent.add_tool(code_editor, "code_editor")

        if self.conversation.project:
            notes = Notes(self.session, self.agent, self.conversation.project)
            self.agent.add_tool(notes, "notes")

    def check_stop_flag(self):
        from chat.lock import check_and_clear_stop_flag

        if check_and_clear_stop_flag(self.conversation.id):
            raise StopException("Query stopped by user")

    @property
    def context(self):
        if self.conversation.project:
            context = {
                "project": {
                    "name": self.conversation.project.name,
                    "description": self.conversation.project.description,
                    "tables": [
                        {"schema": table.schemaName, "table": table.tableName}
                        for table in self.conversation.project.tables
                    ],
                },
            }
            return yaml.dump(context)
        return None

    def answer(
        self,
        text: str,
        from_response: Message,
    ):
        """
        Give the final response from the user demand/query as a text.
        You can insert a query with it's preview result in the text using the <QUERY:{query_id}> tag.
        You can insert a chart in the text using the <CHART:{chart_id}> tag.
        Replace {query_id} and {chart_id} with the actual query id and chart id.
        Show the query / chart only if the user asked for it or if that make sense to have it.
        """  # noqa: E501

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
        raise StopLoopException("We want to stop after answering")

    # TODO: rename...
    def _run_conversation(self):
        emit_status(self.conversation.id, STATUS.RUNNING)
        try:
            messages = (
                self.session.query(ConversationMessage)
                .filter_by(conversationId=self.conversation.id)
                .order_by(ConversationMessage.createdAt)
                .all()
            )
            agentlys_messages = [m.to_agentlys_message() for m in messages]
            self.agent.load_messages(agentlys_messages)
            for m in self.agent.run_conversation():
                self.check_stop_flag()
                # We re-emit the status in case the user has refreshed the page
                emit_status(self.conversation.id, STATUS.RUNNING)
                message = ConversationMessage.from_agentlys_message(m)
                if self.conversation:
                    message.conversationId = self.conversation.id
                self.session.add(message)
                try:
                    self.session.flush()
                except Exception:
                    self.session.rollback()
                    raise
                yield message
            emit_status(self.conversation.id, STATUS.CLEAR)

            # Clear any stop flag since the conversation completed normally
            from chat.lock import clear_stop_flag

            clear_stop_flag(self.conversation.id)
        except StopException:
            emit_status(self.conversation.id, STATUS.CLEAR)
        except Exception as e:
            try:
                if getattr(e, "status_code", None) == 402:
                    # Custom error for subscription required

                    socketio.emit(
                        "error",
                        {
                            "message": "SUBSCRIPTION_REQUIRED",
                            "conversationId": str(self.conversation.id),
                        },
                    )
                    return
                emit_status(self.conversation.id, STATUS.ERROR, e)
            except Exception as status_error:
                # If we can't emit status due to database issues, log it and emit
                logger.error(
                    "Failed to emit error status",
                    exc_info=True,
                    extra={"original_error": str(e), "status_error": str(status_error)},
                )
                emit_status(self.conversation.id, STATUS.ERROR, status_error)
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
            conversation=self.conversation,
        )
        self.session.add(message)
        self.session.flush()
        yield message

        yield from self._run_conversation()
