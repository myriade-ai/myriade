# TODO: remove commit ?
import json
import os
import typing
from copy import deepcopy

import openai
from back.models import ConversationMessage
from chat.utils import message_replace_json_block_to_csv, parse_function
from flask import g

# https://platform.openai.com/docs/models/gpt-4
DEFAULT_MODEL = "gpt-4"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

# Read functions in ./functions/**.json
FUNCTIONS = []
for filename in os.listdir("./chat/functions"):
    with open("./chat/functions/" + filename) as f:
        FUNCTIONS.append(json.load(f))


def fetch_openai(messages: list[dict]):
    return openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=messages,
        functions=FUNCTIONS,
    )


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


class ChatGPT:
    def __init__(
        self,
        session,
        instruction=None,
        examples=[],
        context=None,
        conversation_id: int = None,
    ) -> None:
        self.session = session
        self.pre_history: list[ConversationMessage] = []
        self.history: list[ConversationMessage] = []
        self.instruction: typing.Optional[str] = instruction
        self.examples = examples
        self.context = context
        # TODO: Should probably build the conversation object here instead of datachat...
        self.conversation_id = conversation_id

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

    def clean_message(self, message: ConversationMessage):
        # TODO: should be in datachat ?
        # If the message content contains "DONE", we remove it
        if message.content and "DONE" in message.content:
            message.content = message.content.replace("DONE", "").strip()
            message.done = True
        self.session.commit()
        return message

    def ask(
        self, message: typing.Union[ConversationMessage, str, None] = None
    ) -> ConversationMessage:
        if message:
            if isinstance(message, str):
                # TODO: remove ?
                # If message is instance of string, then convert to ConversationMessage
                message = ConversationMessage(
                    **{
                        "role": "user",
                        "content": message,
                        "conversationId": self.conversation_id,
                    }
                )

            self.history.append(message)  # Add the question to the history
            # Record the message
            self.session.add(message)
            self.session.commit()

        response = self.fetch_with_cache()
        self.history.append(response)

        # Clean the message, save it to the database and return it
        response = self.clean_message(response)
        response.conversationId = self.conversation_id
        self.session.add(response)
        self.session.commit()
        return response

    def fetch_with_cache(
        self,
    ) -> ConversationMessage:
        from back.models import Prediction

        first_message = self.history[0].to_openai_dict()
        first_message["content"] = self.context + "\n" + first_message["content"]
        messages_dict: list[dict] = (
            [x.to_openai_dict() for x in self.pre_history]
            + [first_message]
            + [x.to_openai_dict() for x in self.history[1:]]
        )
        for message in messages_dict:
            if message["content"]:
                message["content"] = message_replace_json_block_to_csv(
                    message["content"]
                )

        """Cache on database Prediction table"""
        key = hashkey(messages_dict)
        prediction = self.session.query(Prediction).filter_by(params_hash=key).first()
        if prediction:
            return ConversationMessage.from_openai_dict(**prediction.value)
        else:
            response = fetch_openai(messages_dict)
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
            self.session.add(prediction)
            self.session.commit()
            return ConversationMessage.from_openai_dict(**value)
