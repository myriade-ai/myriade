from sqlalchemy.orm import Session

from models import Chart, ConversationMessage, Query


class WorkspaceTool:
    def __init__(self, session: Session, conversation_id: int):
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
            .filter(Query.is_favorite)
            .all()
        )
        context = "Queries:\n"
        for query in self.conversation_queries:
            context += f"Query {query.id}: {query.title}\n"

        self.conversation_charts = (
            self.session.query(Chart)
            .join(ConversationMessage, Chart.conversation_messages)
            .filter(ConversationMessage.conversationId == self.conversation_id)
            .filter(Chart.is_favorite)
            .all()
        )
        context += "Charts:\n"
        for chart in self.conversation_charts:
            # TODO: should display the chart image instead of the config?
            try:
                title = chart.config["title"]["text"]
                context += f"Chart {chart.id}: {title}\n"
            except KeyError:
                # We don't want to add broken Chart here
                pass
        return context
