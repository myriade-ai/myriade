import json
import os

import yaml
from autochat import ChatGPT, Message, StopLoopException
from back.datalake import DatalakeFactory
from back.models import Conversation, ConversationMessage, Query
from chat.lock import StopException
from chat.memory_utils import find_closest_embeddings
from chat.sql_utils import run_sql

MAX_DATA_SIZE = 4000  # Maximum size of the data to return

# Read functions in ./functions/**.json
FUNCTIONS = {}
for filename in os.listdir("./chat/functions"):
    with open("./chat/functions/" + filename) as f:
        FUNCTIONS[filename[:-5]] = json.load(f)


class DatabaseChat:
    """
    ChatGPT with a database, execute functions.
    - SQL_QUERY: execute sql query and return the result (size limited)
    - SAVE_TO_MEMORY: save any text to memory
    - PLOT_WIDGET: plot a widget
    """

    def __init__(self, session, database_id, conversation_id=None, stop_flags=None):
        self.session = session
        if conversation_id is None:
            # Create conversation object
            self.conversation = self._create_conversation(databaseId=database_id)
        else:
            self.conversation = (
                self.session.query(Conversation).filter_by(id=conversation_id).first()
            )

        # Add a datalake object to the request
        self.datalake = DatalakeFactory.create(
            self.conversation.database.engine,
            **self.conversation.database.details,
        )
        self.stop_flags = stop_flags

    def __del__(self):
        # On destruct, close the engine
        self.datalake.dispose()

    def _create_conversation(self, databaseId, name=None):
        # Create conversation object
        conversation = Conversation(
            databaseId=databaseId,
            ownerId="admin",  # TODO make it dynamic
            name=name,
        )
        self.session.add(conversation)
        self.session.commit()
        return conversation

    def query_stop_flag(self):
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
        return yaml.dump(context)

    @property
    def chat_gpt(self):
        chat_gpt = ChatGPT.from_template(
            "chat/chat_template.txt",
        )
        chat_gpt.context = self.context
        chat_gpt.add_function(self.sql_query, FUNCTIONS["SQL_QUERY"])
        chat_gpt.add_function(self.save_to_memory, FUNCTIONS["SAVE_TO_MEMORY"])
        chat_gpt.add_function(self.plot_widget, FUNCTIONS["PLOT_WIDGET"])

        messages = [
            Message(**m.to_autochat_message()) for m in self.conversation.messages
        ]
        chat_gpt.load_history(messages)
        return chat_gpt

    def sql_query(self, query: str, name: str = None, from_response: Message = None):
        _query = Query(
            query=name,
            databaseId=self.conversation.databaseId,
            validatedSQL=query,
        )
        self.session.add(_query)
        self.session.commit()

        # We update the message with the query id
        from_response.query_id = _query.id

        output, _ = run_sql(self.datalake, query)
        return output

    def save_to_memory(self, text: str, **kwargs):
        if self.conversation.database.memory is None:
            self.conversation.database.memory = text
        else:
            self.conversation.database.memory += "\n" + text
        self.session.commit()

    def plot_widget(
        self, title: str, outputType: str, sql: str, params: dict = None, **kwargs
    ):
        """TODO: add verification on the widget parameters and the sql query"""
        raise StopLoopException("We want to stop after the widget")
        return

    def _run_conversation(self):
        # Message
        messages = [
            Message(**m.to_autochat_message()) for m in self.conversation.messages
        ]
        self.chat_gpt.load_history(messages)
        for m in self.chat_gpt.run_conversation():
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
