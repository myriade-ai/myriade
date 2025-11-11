import json
from uuid import UUID

from sqlalchemy.orm import Session

from models import Chart, ConversationMessage, Query


class WorkspaceTool:
    def __init__(self, session: Session, conversation_id: UUID):
        self.session = session
        self.conversation_id = conversation_id
        self.conversation_queries = []

    def __repr__(self):
        self.conversation_queries = (
            self.session.query(Query)
            .join(ConversationMessage, Query.conversation_messages)
            .filter(ConversationMessage.conversationId == self.conversation_id)
            .filter(Query.rows.isnot(None))
            .filter(Query.exception.is_(None))
            .all()
        )
        context = "Queries:\n"
        for query in self.conversation_queries:
            context += f"Query {query.id}: {query.title}\n"

        self.conversation_charts = (
            self.session.query(Chart)
            .join(ConversationMessage, Chart.conversation_messages)
            .filter(ConversationMessage.conversationId == self.conversation_id)
            .all()
        )
        context += "Charts:\n"
        for chart in self.conversation_charts:
            try:
                title = chart.config["title"]["text"]  # type: ignore
            except (AttributeError, KeyError, TypeError):
                title = "Untitled"
            context += f"Chart {chart.id}: {title}\n"
        return context

    def get_query(self, query_id: str) -> str:
        """
        Get details of a query by its ID.
        Returns the query SQL, title, and results if available.
        Args:
            query_id: The UUID of the query to retrieve
        """
        try:
            query_uuid = UUID(query_id)
        except ValueError:
            return f"Invalid query ID format: {query_id}"

        # Verify the query belongs to this conversation
        query = (
            self.session.query(Query)
            .join(ConversationMessage, Query.conversation_messages)
            .filter(
                Query.id == query_uuid,
                ConversationMessage.conversationId == self.conversation_id,
            )
            .first()
        )

        if not query:
            return f"Query with ID {query_id} not found in this conversation"

        result = {
            "id": str(query.id),
            "title": query.title,
            "sql": query.sql,
            "status": query.status,
        }

        # Include results if available
        if query.rows is not None:
            result["row_count"] = query.count
            result["columns"] = query.columns
            # Include a sample of rows (first 5)
            result["sample_rows"] = query.rows[:5] if query.rows else []
        elif query.exception:
            result["error"] = query.exception

        return json.dumps(result, indent=2)

    def run_query_by_id(self, query_id: str) -> str:
        """
        Execute an existing query by its ID and return the results.
        This will re-run the SQL query and return fresh results.
        Args:
            query_id: The UUID of the query to execute
        """
        try:
            query_uuid = UUID(query_id)
        except ValueError:
            return f"Invalid query ID format: {query_id}"

        # Verify the query belongs to this conversation
        query = (
            self.session.query(Query)
            .join(ConversationMessage, Query.conversation_messages)
            .filter(
                Query.id == query_uuid,
                ConversationMessage.conversationId == self.conversation_id,
            )
            .first()
        )

        if not query:
            return f"Query with ID {query_id} not found in this conversation"

        if not query.sql:
            return f"Query {query_id} has no SQL to execute"

        # Import here to avoid circular dependency
        from back.data_warehouse import DataWarehouseFactory

        try:
            # Get the database from the query
            database = query.database
            data_warehouse = DataWarehouseFactory.create(
                database.engine, **database.details
            )
            data_warehouse.write_mode = database.write_mode

            # Execute the query
            rows, count, columns = data_warehouse.query(
                query.sql, role="llm", skip_confirmation=True
            )

            # Format the results similar to DatabaseTool.sql_query
            from chat.tools.database import wrap_sql_result

            result_text, _ = wrap_sql_result(rows, count, columns)
            return result_text

        except Exception as e:
            return f"Error executing query {query_id}: {str(e)}"
