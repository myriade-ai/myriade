import json
import os
import typing

import openai
from back.models import ConversationMessage as Message
from back.session import session

# https://platform.openai.com/docs/models/gpt-4
DEFAULT_MODEL = "gpt-4"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)


def parse_chat_template(filename):
    with open(filename) as f:
        string = f.read()

    # split the string by "\n## " to get a list of speaker and message pairs
    pairs = string.split("## ")[1:]

    # split each element of the resulting list by "\n" to separate the speaker and message
    pairs = [pair.split("\n", 1) for pair in pairs]

    # create a list of tuples
    messages = [(pair[0], pair[1].strip()) for pair in pairs]

    instruction = None
    examples = []

    for message in messages:
        # If first message role is a system message, extract the example
        if message[0] == "system" and not instruction:
            instruction = message[1]
        else:
            examples.append(message)
    return instruction, examples


def hashkey(x) -> str:
    """Hash a list of dictionaries"""
    return str(hash(json.dumps(x, sort_keys=True)))


def cache_db(f):
    def wrapper(messages: list[Message]) -> dict:
        from back.models import Prediction

        messages_dict = [m.to_openai_dict() for m in messages]

        """Cache on database Prediction table"""
        key = hashkey(messages_dict)
        prediction = session.query(Prediction).filter_by(params_hash=key).first()
        if prediction:
            return Message(
                **{
                    "role": "assistant",
                    "content": prediction.value,
                }
            )
        else:
            response = f(messages_dict)
            message = response.choices[0].message
            prediction = Prediction(
                prompt=messages_dict[-1]["content"],  # last message is the prompt
                params_hash=key,
                modelName=response.model,
                response=response,
                params=messages_dict,
                output=message["content"],
                value=message["content"],
            )
            session.add(prediction)
            session.commit()
            return message

    return wrapper


def debug(f):
    def wrapper(messages: list[Message]) -> dict:
        last_message = messages[-1]
        if last_message.content.startswith("SQL2"):
            return Message(
                role="assistant",
                content=f'DEBUG MODE (msg: {len(messages)})\n ```sql\nSELECT 1 AS "a", \'lol\' AS "b"```\n```sql\nSELECT 2 AS "a", \'lol2\' AS "b"```',
            )
        elif last_message.content.startswith("SQL"):
            return Message(
                role="assistant",
                content=f'DEBUG MODE (msg: {len(messages)})\n ```sql\nSELECT 1 AS "a", \'lol\' AS "b"```',
            )

        return Message(
            role="assistant",
            content=f"DEBUG MODE (msg: {len(messages)})\nMessage not sent to OpenAI",
        )

    return wrapper


# @debug
@cache_db
def fetch_openai(messages: list[dict]) -> dict:
    return openai.ChatCompletion.create(model=OPENAI_MODEL, messages=messages)


class ChatGPT:
    def __init__(self, instruction=None, examples=[]):
        self.pre_history: list[Message] = []
        self.history: list[Message] = []
        self.instruction: typing.Optional[str] = instruction
        self.examples = examples

        if self.instruction:
            self.pre_history.append(
                Message(**{"role": "system", "content": self.instruction})
            )

        # Simple loop
        for example in self.examples:
            # Herit name from message role
            self.pre_history.append(
                Message(
                    **{
                        "role": "system",
                        "name": "example_" + example[0].strip().lower(),
                        "content": example[1],
                    }
                )
            )

    @property
    def last_message(self):
        if not self.history:
            return None
        return self.history[-1].content

    def reset(self):
        self.history = []

    def load_history(self, messages: list[Message]):
        # Check order of messages (based on createdAt)
        # Oldest first (createdAt ASC)
        messages = sorted(messages, key=lambda x: x.createdAt)
        self.history = [message for message in messages]

    def ask(self, question=None):
        messages = []

        for message in self.pre_history:
            messages.append(message)

        # Add history of conversation
        for message in self.history:
            messages.append(message)

        if question:
            # Add the question
            new_message = Message(**{"role": "user", "content": question})
            messages.append(new_message)
            self.history.append(new_message)  # Add the question to the history

        response = fetch_openai(tuple(messages))
        self.history.append(response)

        return response.content
