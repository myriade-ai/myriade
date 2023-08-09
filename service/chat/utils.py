import csv
import json
import re
from io import StringIO
from turtle import distance

import numpy as np
import openai
from sqlalchemy import and_


def csv_dumps(data):
    # Dumps to CSV, with header row
    if not data:
        return
    header = list(data[0].keys())
    with StringIO() as output:
        writer = csv.DictWriter(output, fieldnames=header)
        writer.writeheader()
        writer.writerows(data)
        output = output.getvalue().strip()
        return output.replace("\r\n", "\n").replace("\r", "\n")


def message_replace_json_block_to_csv(content):
    """
    Transform json block to csv
    Block format: ```format\ncontent```
    """
    json_block_pattern = re.compile(r"```json\n(.*?)\n```", re.DOTALL)
    matches = json_block_pattern.findall(content)
    for match in matches:
        json_data_str = match.strip()
        data = json.loads(json_data_str)
        # Dumps to CSV, with header row
        csv_data_str = csv_dumps(data)
        # Replace ```json\ncontent``` to ```csv\ncontent```
        content = content.replace(
            f"```json\n{match}\n```", f"```csv\n{csv_data_str}\n```"
        )
    return content


def parse_function(text):
    function_pattern = r"(\w+)\((\w+)=([`\"].*?[`\"])\)"
    matches = re.finditer(function_pattern, text, re.DOTALL)

    parsed_functions = []

    for match in matches:
        function_name = match.group(1).strip()
        param_key = match.group(2).strip()
        param_value = match.group(3).strip('`"')

        arguments_dumps = json.dumps({param_key: param_value})
        parsed_function = {"name": function_name, "arguments": arguments_dumps}
        parsed_functions.append(parsed_function)

    return parsed_functions[0]
