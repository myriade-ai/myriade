import json

import yaml
from autochat.chat import OUTPUT_SIZE_LIMIT
from autochat.model import Message
from autochat.utils import limit_data_size

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


def wrap_sql_result(rows, count):
    # We start by limiting the number of rows to 20.
    rows = rows[:20]
    # Then we take every row until the total size is less than JSON_OUTPUT_SIZE_LIMIT
    results_limited = limit_data_size(rows, character_limit=JSON_OUTPUT_SIZE_LIMIT)
    results_dumps = json.dumps(results_limited, default=str)

    # Send the result back to the chatbot as the new question
    execution_response = RESULT_TEMPLATE.format(
        sample=results_dumps,
        len_sample=len(results_limited),
        len_total=count,
    )
    return execution_response, True


def wrap_sql_error(error):
    execution_response = ERROR_TEMPLATE.format(error=str(error))
    return execution_response, False


class DatabaseTool:
    def __init__(self, session, database: Database):
        self.session = session
        self.database = database
        self.datalake = database.create_datalake()

    def __repr__(self):
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

        context = {
            "DATABASE": {
                "name": self.database.name,
                "engine": self.database.engine,
            },
            "TABLES": tables_preview,
            "MEMORY": self.database.memory,
        }
        return yaml.dump(context)

    def save_to_memory(self, text: str) -> str:
        """
        Add text to the AI's memory
        Args:
            text: The text to add to the memory
        """
        if self.database.memory is None:
            self.database.memory = text
        else:
            self.database.memory += "\n" + text
        self.session.flush()
        return "Memory updated."

    def sql_query(
        self,
        query: str,
        title: str = "",
        from_response: Message | None = None,
    ) -> str:
        """
        Run an SQL query on the database and return the result
        Args:
            query: The SQL query string to be executed. Don't forget to escape this if you use double quote.
            title: The name/title of the query
        """  # noqa: E501
        _query = Query(
            title=title,
            databaseId=self.database.id,
            sql=query,
        )
        self.session.add(_query)
        self.session.flush()

        if from_response:
            # We update the message with the query id
            from_response.query_id = _query.id  # type: ignore

        try:
            rows, count = self.datalake.query(query)
            # We add the result
            _query.rows = rows
            _query.count = count
            result, _ = wrap_sql_result(rows, count)
        except Exception as e:
            _query.exception = str(e)
            result, _ = wrap_sql_error(e)

        self.session.flush()
        return result
