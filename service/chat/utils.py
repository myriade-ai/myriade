import csv
import json
import re
from io import StringIO
from turtle import distance

import numpy as np
import openai
from back.models import Query
from back.session import session
from sqlalchemy import and_


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


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


def generate_embedding(string):
    response = openai.Embedding.create(input=string, model="text-embedding-ada-002")
    # len => 1536
    embedding = response["data"][0]["embedding"]
    return embedding


def find_closest_embeddings(query, top_n=5):
    query_embedding = generate_embedding(query)

    queries = session.query(Query).filter(
        and_(
            Query.databaseId == 131,
            Query.query != "???",
            Query.embedding != None,  # Add this condition
            Query.validatedSQL != None,  # Add this condition
        )
    )

    print("Total queries: ", queries.count())

    # Fetch the top_n closest values to the query embedding
    # Should be at least 80% similar
    closest_queries = []
    for q in queries:
        distance = cosine_similarity(query_embedding, q.embedding)
        if distance > 0.8:
            closest_queries.append((q, distance))

    # Sort by distance
    closest_queries.sort(key=lambda x: x[1], reverse=True)

    # Return the top_n matches
    closest_queries = closest_queries[:top_n]

    return [q[0] for q in closest_queries]


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
