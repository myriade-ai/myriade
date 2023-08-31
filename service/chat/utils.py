import csv
import json
import re
from io import StringIO


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
    # Match function name and its optional arguments
    match = re.search(r">\s*(\w+)(?:\(([^>]+)\))?\s*$", text, re.DOTALL)
    if not match:
        raise ValueError(f"Invalid function call: {text}")

    function_name = match.group(1)
    arguments_text = match.group(2) if match.group(2) else ""

    # Split the arguments into key-value pairs
    arg_pairs = re.findall(r'(\w+)="([^"]+)"', arguments_text)
    additional_arg = re.search(r"(\w+)=```(.*?)```", arguments_text, re.DOTALL)
    if additional_arg:
        # Remove extra indentation from multi-line arguments
        content = "\n".join(
            [
                line.strip()
                for line in additional_arg.group(2).splitlines()
                if line.strip()
            ]
        )
        arg_pairs.append((additional_arg.group(1), content))

    arguments = {key: value for key, value in arg_pairs}

    result = {"name": function_name, "arguments": json.dumps(arguments)}
    return result
