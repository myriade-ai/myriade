import json
import re


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


def parse_answer_text(text: str):
    """Parse the text in a list of chunks.
    > parse_answer_text("Hello <QUERY:1> and <CHART:2>")
    [{type: "text", content: "Hello"},
     {type: "query", query_id: 1},
     {type: "text", content: " and "},
     {type: "chart", chart_id: 2}]
    """
    chunks = []
    while text:
        if "<QUERY:" in text:
            query_id = int(text.split("<QUERY:")[1].split(">")[0].strip())
            chunks.append({"type": "query", "query_id": query_id})
            text = text.split("<QUERY:")[1].split(">")[1]
        elif "<CHART:" in text:
            chart_id = int(text.split("<CHART:")[1].split(">")[0].strip())
            chunks.append({"type": "chart", "chart_id": chart_id})
            text = text.split("<CHART:")[1].split(">")[1]
        else:
            chunks.append({"type": "text", "content": text})
            text = ""
    return chunks
