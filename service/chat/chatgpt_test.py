import json
import re

from chat.chatgpt import ChatGPT, parse_chat_template
from chat.utils import parse_function

instruction, examples = parse_chat_template("chat/chat_template2.txt")
print(json.dumps(examples, indent=4))
chat_gpt = ChatGPT(instruction=instruction, examples=examples)
print(chat_gpt.pre_history)

text = """> MEMORY_SEARCH(search="station san jose installed 2012")"""

parsed = {
    "name": "MEMORY_SEARCH",
    "arguments": {"search": "station san jose installed 2012"},
}

print(parse_function(text))
assert parse_function(text) == parsed

text = """
> SQL_QUERY(query=```
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
```)
"""

parsed = {
    "name": "SQL_QUERY",
    "arguments": {
        "query": "\nSELECT table_schema, table_name\nFROM information_schema.tables\nWHERE table_schema NOT IN ('pg_catalog', 'information_schema')\n",
    },
}


print(parse_function(text))
assert parse_function(text) == parsed
