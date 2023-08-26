# TODO: Here we should tell if the message should be displayed or not ?? Could be done at compilation time !
import copy
import json
import re

from back.datalake import DatalakeFactory
from back.models import Conversation, ConversationMessage, Query
from chat.chatgpt import ChatGPT, parse_chat_template
from chat.lock import StopException
from chat.memory_utils import find_closest_embeddings
from chat.sql_utils import run_sql

MAX_DATA_SIZE = 4000  # Maximum size of the data to return
CONVERSATION_MAX_ATTEMPT = 10  # Number of exchange the AI can do before giving up


response = """
Previous queries:

{% for query in queries %}
>>> Query: Show pits stop duration distribution for year 2020
```sql
{{SQL}}
```
{% endfor %}
"""


class DatabaseChat:
    """
    ChatGPT with a database
    Intercept the exchange so if there is SQL in the conversion, it's executed,
    and the result is sent back to the AI. (unless there is "DONE" in the response)
    If there is a MEMORY_SEARCH() query, we intercept end send back proximate queries
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
    def chat_gpt(self):
        instruction, examples = parse_chat_template("chat/chat_template.txt")
        chat_gpt = ChatGPT(
            session=self.session,
            instruction=instruction,
            examples=examples,
            context=f"In {self.conversation.database.engine} database",
            conversation_id=self.conversation.id,
        )

        chat_gpt.load_history(self.conversation.messages)
        return chat_gpt

    def _run_conversation(self):
        for attempt in range(CONVERSATION_MAX_ATTEMPT):
            # Check if the user has stopped the query
            self.query_stop_flag()

            response = self.chat_gpt.ask()

            if response.done or not response.functionCall:
                """
                If the answer does not contain a query (SQL, Memory), we assume it's either:
                - The final answer
                - A question to the user
                """
                yield response
                return

            function_name = response.functionCall["name"]
            function_arguments = response.functionCall["arguments"]

            if function_name == "SQL_QUERY":
                sql_query = function_arguments["query"].strip()
                query_name = function_arguments["name"].strip()
                query = self.save_query(query_name, sql_query, response)
                response.query_id = query.id
                response.display = False
                yield response

                output, _ = run_sql(self.datalake, sql_query)
                message = ConversationMessage(
                    role="system",
                    display=False,
                    content=output,
                    conversationId=self.conversation.id,
                )
                self.session.add(message)
                self.session.commit()
                yield message
            elif function_name == "MEMORY_SEARCH":
                memory_search = function_arguments["search"]
                response.display = False
                yield response

                # TODO: implement
                close_queries = find_closest_embeddings(self.session, memory_search, 3)
                # output = f"response to: {memory_search}"
                output = f"{len(close_queries)} results\n" + "\n".join(
                    [f"- {q}" for q in close_queries]
                )

                message = ConversationMessage(
                    role="system",
                    display=False,
                    content=output,
                    conversationId=self.conversation.id,
                )
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

    def save_query(
        self, query_name: str, sql_query: str, message: ConversationMessage
    ) -> Query:
        query = Query(
            query=query_name,
            databaseId=message.conversation.databaseId,
            validatedSQL=sql_query,
        )
        # Update message with queryId
        self.session.add(query)
        self.session.commit()
        message.queryId = query.id
        self.session.add(message)
        self.session.commit()
        return query
