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
