from uuid import UUID

from flask import Blueprint
from flask import session as flask_session
from flask_socketio import emit
from sqlalchemy.orm import Session

from app import socketio
from auth.auth import UnauthorizedError, socket_auth
from back.session import with_session
from chat.analyst_agent import DataAnalystAgent
from chat.lock import STATUS, conversation_stop_flags, emit_status, stop_flag_lock
from models import Conversation, ConversationMessage, Project

api = Blueprint("chat_api", __name__)


@socketio.on("stop")
def handle_stop(conversation_id: str):
    print("Received stop signal for conversation_id", conversation_id)
    # Stop the query
    with stop_flag_lock:
        conversation_stop_flags[conversation_id] = True
        emit_status(conversation_id, STATUS.TO_STOP)


def extract_context(session: Session, context_id: str) -> tuple[UUID, UUID | None]:
    """
    Extract the databaseId from the context_id
    context is "project-{projectId}" or "database-{databaseId}"
    """
    if context_id.startswith("project-"):
        project_id = context_id.removeprefix("project-")
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            raise ValueError(f"Project with id {project_id} not found")
        return project.databaseId, project.id
    elif context_id.startswith("database-"):
        database_id = context_id.removeprefix("database-")
        return UUID(database_id), None
    else:
        raise ValueError(f"Invalid context_id: {context_id}")


@socketio.on("ask")
@with_session
def handle_ask(
    session, question, conversation_id: str | None = None, context_id: str | None = None
):
    # We reset stop flag if the user sent a new request
    conversation_stop_flags.pop(conversation_id, None)

    # Extract database_id and project_id from the context
    database_id, project_id = extract_context(session, context_id)
    # Handle normal questions (not editing)
    agent = DataAnalystAgent(
        session,
        database_id,
        conversation_id,
        conversation_stop_flags,
        user_id=flask_session["user"].id,
        project_id=project_id,
    )
    for message in agent.ask(question):
        # We need to commit the session to save the message
        try:
            session.commit()
        except Exception as e:
            print(f"Error committing session: {e}")
            session.rollback()
            # We break the loop to avoid sending the message
            break
        emit("response", message.to_dict())


@socketio.on("query")
@with_session
def handle_query(session, query, conversation_id=None, context_id=None):
    # We reset stop flag if the user sent a new request
    conversation_stop_flags.pop(conversation_id, None)

    database_id, project_id = extract_context(session, context_id)
    agent = DataAnalystAgent(
        session,
        database_id,
        conversation_id,
        conversation_stop_flags,
        project_id=project_id,
    )

    user_message = ConversationMessage(
        role="user",
        functionCall={
            "name": "sql_query",
            "arguments": {
                "query": query,
            },
        },
        conversationId=agent.conversation.id,
    )
    session.add(user_message)
    emit("response", user_message.to_dict())
    # Run the SQL
    message = user_message.to_autochat_message()
    content = agent.chatbot.tools["database"].sql_query(query, from_response=message)
    user_message.queryId = message.query_id
    # Update the message with the linked query
    session.add(user_message)
    session.flush()

    # Display the response
    message = ConversationMessage(
        role="function",
        name="sql_query",
        content=content,
        conversationId=agent.conversation.id,
        isAnswer=True,
    )
    session.add(message)
    session.flush()
    emit("response", user_message.to_dict())
    emit("response", message.to_dict())


@socketio.on("regenerateFromMessage")
@with_session
def handle_regenerate_from_message(
    session, conversation_id, message_id, message_content=None
):
    """
    Regenerate the conversation from a specific message
    Delete all messages after the message_id and regenerate the conversation
    If the message is from the assistant, delete it
    If the message is from the user, regenerate the conversation from the next message
    """
    # We reset stop flag if the user sent a new request
    conversation_stop_flags.pop(conversation_id, None)

    conversation = session.query(Conversation).filter_by(id=conversation_id).first()

    # if message_content is not None, it means the user has edited the message
    if message_content is not None:
        message = session.query(ConversationMessage).filter_by(id=message_id).first()
        message.content = message_content
        try:
            session.commit()
        except Exception as e:
            print(f"Error committing session: {e}")
            session.rollback()
            # We return to avoid sending the message
            return
        emit("response", message.to_dict())

    database_id = conversation.databaseId
    project_id = conversation.projectId

    # Clear all messages after the message_id, from the conversation
    selected_message = (
        session.query(ConversationMessage).filter_by(id=message_id).first()
    )
    messages = (
        session.query(ConversationMessage)
        .filter(
            ConversationMessage.createdAt > selected_message.createdAt,
            ConversationMessage.conversationId == conversation_id,
        )
        .all()
    )
    deleted_message_ids = []
    for message in messages:
        deleted_message_ids.append(message.id)
        session.delete(message)

    # Also, if the message is from the assistant, delete it
    message = session.query(ConversationMessage).filter_by(id=message_id).first()
    if message.role == "assistant":
        deleted_message_ids.append(message.id)
        session.delete(message)

    try:
        # Delete the messages
        session.commit()
    except Exception as e:
        print(f"Error committing session: {e}")
        session.rollback()
        # We return to avoid sending the message
        return
    for message_id in deleted_message_ids:
        emit("delete-message", str(message_id))

    # Regenerate the conversation
    agent = DataAnalystAgent(
        session,
        database_id,
        conversation_id,
        conversation_stop_flags,
        project_id=project_id,
    )
    for message in agent._run_conversation():
        try:
            session.commit()
        except Exception as e:
            print(f"Error committing session: {e}")
            session.rollback()
            # We return to avoid sending the message
            break
        emit("response", message.to_dict())


@socketio.on("connect")
def on_connect():
    # This is where you would initialize your session
    # or any other per-connection resources.
    try:
        auth_response = socket_auth()
    except UnauthorizedError as e:
        emit("error", str(e))
        return False  # Reject the connection

    flask_session.update(
        user=auth_response.user,
        role=auth_response.role,
        organization_id=auth_response.organization_id,
    )
