import json

MAX_DATA_SIZE = 4000  # Maximum size of the data to return

RESULT_TEMPLATE = """Results {len_sample}/{len_total} rows:
```json
{sample}
```
"""


ERROR_TEMPLATE = """An error occurred while executing the SQL query:
```error
{error}
```
Please correct the query and try again.
"""


def run_sql(connection, sql):
    try:
        # Assuming you have a Database instance named 'database'
        # TODO: switch to logger
        # print("Executing SQL query: {}".format(sql))
        rows = connection.query(sql)
    except Exception as e:
        # If there's an error executing the query, inform the user
        execution_response = ERROR_TEMPLATE.format(error=str(e))
        return execution_response, False
    else:
        # Take every row until the total size is less than 1000 characters
        results_limited = []
        total_size = 0
        for row in rows:
            results_limited.append(row)
            total_size += len(json.dumps(row, default=str))
            if total_size > MAX_DATA_SIZE:
                break

        # Display in JSON
        results_dumps = json.dumps(results_limited, default=str)

        # Send the result back to chat_gpt as the new question
        execution_response = RESULT_TEMPLATE.format(
            sample=results_dumps,
            len_sample=len(results_limited),
            len_total=len(rows),
        )
        return execution_response, True


def extract_sql(text):
    import re

    # Define a regular expression pattern to match the SQL query
    pattern = r"```(sql)?(.*?)```"

    # Use the re.findall() function to extract all matches of the pattern
    matches = re.findall(pattern, text, re.DOTALL)

    try:
        # Return all matches
        return [match[1].strip() for match in matches if match[0] == "sql"]
    except IndexError:
        pass
