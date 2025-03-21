from sqlalchemy.orm import Session

from back.models import ConversationMessage, Query


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
            .all()
        )
        context = "Queries:\n"
        for query in self.conversation_queries:
            print(query)
            context += f"Query {query.id}: {query.sql}\n"
        return context
