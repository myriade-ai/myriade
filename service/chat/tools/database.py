import json
import uuid
from datetime import datetime

import yaml
from agentlys.chat import OUTPUT_SIZE_LIMIT, StopLoopException
from agentlys.model import Message
from agentlys.utils import limit_data_size

from back.data_warehouse import AbstractDatabase, WriteOperationError
from models import Database, Query

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
    results_dumps = json.dumps(results_limited)

    # Send the result back to the chatbot as the new question
    execution_response = RESULT_TEMPLATE.format(
        sample=results_dumps,
        len_sample=len(results_limited),
        len_total=count,
    )
    return execution_response, True


def wrap_sql_error(error):
    return ERROR_TEMPLATE.format(error=str(error))


def cancel_query(session, query_id: uuid.UUID) -> Query:
    """
    Cancel a query

    Args:
        query_id: The ID of the query to cancel
    Returns:
        success
    """
    # Find the query
    _query = session.query(Query).filter_by(id=query_id).first()
    if not _query:
        raise Exception("Query not found")

    # Verify this is a pending confirmation or running query
    if _query.status not in ["pending_confirmation"]:
        raise Exception("Query cannot be cancelled in current state")

    # Set status to cancelled
    _query.status = "cancelled"
    session.flush()

    return _query


class DatabaseTool:
    def __init__(self, session, database: Database, data_warehouse: AbstractDatabase):
        self.session = session
        self.database = database
        self.data_warehouse = data_warehouse

    def __repr__(self):
        tables_preview = []
        for table in self.data_warehouse.tables_metadata:
            table_preview = {
                "name": table["name"],
                "schema": table["schema"],
                "columns": [column["name"] for column in table["columns"]],
                "table_type": table["table_type"],
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
        Run an SQL query on the database and return the result.
        If the query is a write operation and the configuration is set to "ask for confirmation", the user will be asked to confirm the query.
        You will only get sample (~20 rows) of the result. You won't get the full result.
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
            rows, count = self.data_warehouse.query(query, role="llm")
            # We add the result and mark as completed
            _query.rows = rows
            _query.count = count
            _query.status = "completed"
            _query.completed_at = datetime.utcnow()
            result, _ = wrap_sql_result(rows, count)
        except WriteOperationError as e:
            # Handle write operation that requires confirmation
            # Set query status to pending confirmation and store operation type
            _query.status = "pending_confirmation"
            _query.operation_type = e.operation_type
            # Stop the agent execution and wait for user confirmation
            raise StopLoopException("Waiting for write operation confirmation") from e
        except Exception as e:
            _query.exception = str(e)
            _query.status = "failed"
            _query.completed_at = datetime.utcnow()
            result = wrap_sql_error(e)
        finally:
            self.session.flush()

        return result

    # Private method because it's used by the API not by the chatbot
    def _execute_confirmed_query(self, query_id: uuid.UUID) -> tuple[str, bool]:
        """
        Execute a query.

        Args:
            query_id: The ID of the query to execute

        Returns:
            Tuple of (result_message, success)
        """

        try:
            # Find the query
            _query = self.session.query(Query).filter_by(id=query_id).first()
            if not _query:
                return "Query not found", False

            # Verify this is a pending confirmation
            if _query.status != "pending_confirmation":
                return "Query is not pending confirmation", False

            # Set status to running and start execution
            _query.status = "running"
            _query.started_at = datetime.utcnow()
            self.session.flush()

            # Execute the query using unprotected method to bypass write protection
            rows, count = self.data_warehouse.query(
                _query.sql, role="llm", skip_confirmation=True
            )

            # Update the query with results
            _query.rows = rows
            _query.count = count
            _query.status = "completed"
            _query.completed_at = datetime.utcnow()
            _query.exception = None  # Clear the pending confirmation status

            # For write operations, check if we got results or successful exec
            if rows is None or (isinstance(rows, list) and len(rows) == 0):
                # This is a write operation that doesn't return rows
                result = f"✅ Query executed successfully ({count} rows)."
                success = True
            else:
                # This returned actual data
                result, success = wrap_sql_result(rows, count)
            return result, success
        except Exception as e:
            # Update query with error
            _query.exception = str(e)
            _query.status = "failed"
            _query.completed_at = datetime.utcnow()
            self.session.flush()
            return wrap_sql_error(e), False
        finally:
            self.session.flush()
