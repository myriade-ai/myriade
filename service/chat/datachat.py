import copy
import json
import re

from back.datalake import DatalakeFactory
from back.models import Conversation, ConversationMessage, Query
from back.session import session
from chat.chatgpt import ChatGPT, parse_chat_template
from chat.lock import StopException
from chat.sql_utils import extract_sql, run_sql
from chat.utils import message_replace_json_block_to_csv

MAX_DATA_SIZE = 4000  # Maximum size of the data to return
CONVERSATION_MAX_ATTEMPT = 10  # Number of exchange the AI can do before giving up


def extract_memory_query(content):
    """
    >>> extract_memory_query("MEMORY_SEARCH(station)")
    'station'

    >>> extract_memory_query("blabla bla")
    """
    search = re.search(r'MEMORY_SEARCH\("?(.*)"?\)', content)
    if search:
        memory = search.group(1)
        return memory


def save_query(sql_query, message):
    return
    query = Query(
        query="???",
        # databaseId=message.databaseId,
        validatedSQL=sql_query,
        # messageId=message.id,
    )
    session.add(query)
    session.commit()


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

    def __init__(self, database_id, conversation_id=None, stop_flags=None):
        if conversation_id is None:
            # Create conversation object
            self.conversation = self._create_conversation(databaseId=database_id)
        else:
            self.conversation = (
                session.query(Conversation).filter_by(id=conversation_id).first()
            )

        # Add a datalake object to the request
        self.datalake = DatalakeFactory.create(
            self.conversation.database.engine,
            **self.conversation.database.details,
        )
        self.stop_flags = stop_flags

    def _create_conversation(self, databaseId, name=None):
        # Create conversation object
        conversation = Conversation(
            databaseId=databaseId,
            ownerId="local",  # TODO make it dynamic
            name=name,
        )
        session.add(conversation)
        session.commit()
        return conversation

    def _record_message(
        self,
        content: str,
        role: str = "assistant",
        display: bool = True,
        done: bool = False,
        function_call=None,
    ):
        self.query_stop_flag()
        message = {
            "conversation_id": self.conversation.id,
            "content": content,
            "role": role,
            "display": display,
            "done": done,
        }
        if function_call:
            message["function_call"] = function_call

        conversaion_message = ConversationMessage(**message)

        # If this is the first message, we set the conversation as started
        # if not self.conversation.started:
        #     self.conversation.started = True

        session.add(conversaion_message)
        session.commit()
        return message

    def query_stop_flag(self):
        if self.stop_flags.get(str(self.conversation.id)):
            raise StopException("Query stopped by user")

    @property
    def chat_gpt(self):
        instruction, examples = parse_chat_template("chat/chat_template2.txt")
        chat_gpt = ChatGPT(instruction=instruction, examples=examples)

        messages = self.conversation.messages
        # deep copy the messages (to avoid modifying the database object)
        # why it is this: 'message' object has no attribute 'copy'
        messages = [copy.deepcopy(message) for message in messages]
        messages[
            0
        ].content = (
            f"In {self.conversation.database.engine} database, {messages[0].content}"
        )

        for message in messages:
            if message.content:
                message.content = message_replace_json_block_to_csv(message.content)
        chat_gpt.load_history(messages)
        return chat_gpt

    def ask(self, question):
        self._record_message(question, role="user")
        if not self.conversation.name:
            self.conversation.name = question

        for attempt in range(CONVERSATION_MAX_ATTEMPT):
            print(self.stop_flags, self.conversation.id)
            # Check if the user has stopped the query
            self.query_stop_flag()

            response = self.chat_gpt.ask()

            # Check if the response contains "DONE"
            if response.content and "DONE" in response.content:
                content = response.content.replace("DONE", "").strip()
                message = self._record_message(content, done=True)
                yield message
                return message

            if response.functionCall:
                function_call = response.functionCall
                function_name = function_call["name"]
                function_arguments = function_call["arguments"]
                if function_name == "SQL_QUERY":
                    # save_query(sql_query, message)
                    print("function_arguments", function_arguments)
                    function_arguments["query"] = function_arguments["query"].strip()
                    sql_query = function_arguments["query"]
                    message = self._record_message(
                        content=None,
                        function_call=function_call,
                        role="assistant",
                        display=False,
                    )
                    yield message
                    response, _ = run_sql(self.datalake, sql_query)
                    message = self._record_message(
                        content=response, role="system", display=False
                    )
                    yield message
                elif function_name == "MEMORY_SEARCH":
                    print("function_arguments", function_arguments)
                    memory_search = function_arguments["search"]
                    message = self._record_message(
                        content=None,
                        function_call=function_call,
                        role="assistant",
                        display=False,
                    )
                    print("memory_search", memory_search)
                    yield message
                    # response = self.datalake.memory_search(memory_query)
                    response = f"response to {memory_search}"
                    message = self._record_message(
                        content=response, role="system", display=False
                    )
                    yield message
            else:
                """
                If the answer does not contain an query (SQL, Memory), we assume it's either:
                - The final answer
                - A question to the user
                """
                message = self._record_message(response.content, done=True)
                yield message
                return message

    def regenerate_last_message(self):
        # Delete the last message and reask the question
        last_message = self.conversation.messages[-1]
        session.delete(last_message)
        session.commit()
        yield from self.ask(last_message.content)
