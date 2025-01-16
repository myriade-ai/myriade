import json

from autochat.chat import OUTPUT_SIZE_LIMIT
from autochat.utils import limit_data_size

RESULT_TEMPLATE = """Results {len_sample}/{len_total} rows:
```json
{sample}
```
"""

JSON_OUTPUT_SIZE_LIMIT = OUTPUT_SIZE_LIMIT / 2  # Json is 2x larger than csv

ERROR_TEMPLATE = """An error occurred while executing the SQL query:
```error
{error}
```Please correct the query and try again.
"""


def run_sql(connection, sql):
    try:
        # Assuming you have a Database instance named 'database'
        # TODO: switch to logger
        # print("Executing SQL query: {}".format(sql))
        rows, count = connection.query(sql)
    except Exception as e:
        # If there's an error executing the query, inform the user
        execution_response = ERROR_TEMPLATE.format(error=str(e))
        return execution_response, False
    else:
        # Take every row until the total size is less than JSON_OUTPUT_SIZE_LIMIT
        results_limited = limit_data_size(rows, character_limit=JSON_OUTPUT_SIZE_LIMIT)
        results_dumps = json.dumps(results_limited, default=str)

        # Send the result back to the chatbot as the new question
        execution_response = RESULT_TEMPLATE.format(
            sample=results_dumps,
            len_sample=len(results_limited),
            len_total=count,
        )
        return execution_response, True
