import json

import yaml
from autochat.chat import OUTPUT_SIZE_LIMIT
from autochat.model import Message
from autochat.utils import limit_data_size

from back.datalake import DatalakeFactory
from back.models import Database, Query

RESULT_TEMPLATE = """Results {len_sample}/{len_total} rows:
```json
{sample}
```
"""

JSON_OUTPUT_SIZE_LIMIT = int(OUTPUT_SIZE_LIMIT / 2)  # Json is 2x larger than csv

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


class DatabaseTool:
    def __init__(self, session, database: Database):
        self.session = session
        self.database = database
        self.datalake = DatalakeFactory.create(
            self.database.engine,
            **self.database.details,
        )

    def __repr__(self):
        context = "Tables:\n"
        tables_preview = []
        for table in self.database.tables_metadata:
            table_preview = {
                "name": table["name"],
                "schema": table["schema"],
                "columns": [column["name"] for column in table["columns"]],
                "is_view": table["is_view"],
            }
            if table.get("description") is not None:
                description_snippet = (
                    table["description"][:100] + "..."
                    if len(table["description"]) > 100  # type: ignore
                    else table["description"]
                )
                table_preview["description"] = description_snippet
            tables_preview.append(table_preview)

        context += yaml.dump(tables_preview)
        return context

    def sql_query(
        self,
        query: str,
        name: str = "",
        from_response: Message | None = None,
    ):
        """
        Run an SQL query on the database and return the result
        Args:
            query: The SQL query string to be executed. Don't forget to escape this if you use double quote.
            name: The name/title of the query
        """  # noqa: E501
        _query = Query(
            query=name,
            databaseId=self.database.id,
            sql=query,
        )
        self.session.add(_query)
        self.session.commit()

        if from_response:
            # We update the message with the query id
            from_response.query_id = _query.id  # type: ignore

        output, _ = run_sql(self.datalake, query)
        return output
