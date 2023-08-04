import json
import os
import typing

import openai
from back.models import ConversationMessage
from back.session import session
from chat.utils import parse_function

# https://platform.openai.com/docs/models/gpt-4
DEFAULT_MODEL = "gpt-4"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

# Read functions in ./functions/**.json
FUNCTIONS = []
for filename in os.listdir("./chat/functions"):
    with open("./chat/functions/" + filename) as f:
        FUNCTIONS.append(json.load(f))


def parse_chat_template(filename):
    with open(filename) as f:
        string = f.read()

    # split the string by "\n## " to get a list of speaker and message pairs
    pairs = string.split("## ")[1:]

    # split each element of the resulting list by "\n" to separate the speaker and message
    pairs = [pair.split("\n", 1) for pair in pairs]

    # create a list of tuples
    messages = [(pair[0], pair[1].strip()) for pair in pairs]

    examples = []
    instruction = None
    for ind, message in enumerate(messages):
        # If first message role is a system message, extract the example
        if ind == 0 and message[0] == "system":
            instruction = message[1]
        else:
            role = message[0].strip().lower()
            message = message[1]

            if message.startswith("> "):
                # If message start with "> " then it's a function call
                examples.append(
                    {
                        "role": role,
                        "function_call": {**parse_function(message)},
                    }
                )
            else:
                examples.append(
                    {
                        "role": role,
                        "content": message,
                    }
                )
    return instruction, examples


def hashkey(x) -> str:
    """Hash a list of dictionaries"""
    return str(hash(json.dumps(x, sort_keys=True)))


def cache_db(f):
    def wrapper(messages: list[ConversationMessage]) -> ConversationMessage:
        from back.models import Prediction

        messages_dict = [m.to_openai_dict() for m in messages]

        """Cache on database Prediction table"""
        key = hashkey(messages_dict)
        prediction = session.query(Prediction).filter_by(params_hash=key).first()
        if prediction:
            return ConversationMessage(**prediction.value)
        else:
            response = f(messages_dict)
            message = response.choices[0].message
            value = message.to_dict()
            prediction = Prediction(
                prompt=messages_dict[-1]["content"],  # last message is the prompt
                params_hash=key,
                modelName=response.model,
                response=response,
                params=messages_dict,
                output=message["content"],
                value=value,
            )
            session.add(prediction)
            session.commit()
            return ConversationMessage.from_openai_dict(**value)

    return wrapper


@cache_db
def fetch_openai(messages: list[dict]):
    return openai.ChatCompletion.create(
        model=OPENAI_MODEL, messages=messages, functions=FUNCTIONS
    )


class ChatGPT:
    def __init__(self, instruction=None, examples=[]) -> None:
        self.pre_history: list[ConversationMessage] = []
        self.history: list[ConversationMessage] = []
        self.instruction: typing.Optional[str] = instruction
        self.examples = examples

        if self.instruction:
            self.pre_history.append(
                ConversationMessage(**{"role": "system", "content": self.instruction})
            )

        # Simple loop
        for example in self.examples:
            # Herit name from message role

            self.pre_history.append(
                ConversationMessage(
                    **{
                        **example,
                        # "role": "system",
                        "name": "example_" + example["role"],
                    }
                )
            )

    @property
    def last_message(self):
        if not self.history:
            return None
        return self.history[-1].content

    def reset(self):
        self.history: list[ConversationMessage] = []

    def load_history(self, messages: list[ConversationMessage]):
        # Check order of messages (based on createdAt)
        # Oldest first (createdAt ASC)
        messages = sorted(messages, key=lambda x: x.createdAt)
        self.history = [message for message in messages]

    def ask(self, question=None) -> ConversationMessage:
        messages: list[ConversationMessage] = []

        for message in self.pre_history:
            messages.append(message)

        # Add history of conversation
        for message in self.history:
            messages.append(message)

        if question:
            # Add the question
            new_message = ConversationMessage(**{"role": "user", "content": question})
            messages.append(new_message)
            self.history.append(new_message)  # Add the question to the history

        response = fetch_openai(tuple(messages))
        self.history.append(response)

        return response
