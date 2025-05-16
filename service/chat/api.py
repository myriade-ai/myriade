from flask import Blueprint
from flask import session as flask_session
from flask_socketio import emit
from sqlalchemy.orm import Session

from app import socketio
from auth.auth import UnauthorizedError, socket_auth
from back.session import db_session
from chat.datachat import DatabaseChat
from chat.lock import STATUS, conversation_stop_flags, emit_status, stop_flag_lock
from models import Conversation, ConversationMessage, Project

api = Blueprint("chat_api", __name__)


@socketio.on("stop")
def handle_stop(conversation_id):
    print("Received stop signal for conversation_id", conversation_id)
    # Stop the query
    with stop_flag_lock:
        conversation_stop_flags[conversation_id] = True
        emit_status(conversation_id, STATUS.TO_STOP)


def extract_context(session: Session, context_id) -> tuple[int, int]:
    """
    Extract the databaseId from the context_id
    context is "project-{projectId}" or "database-{databaseId}"
    """
    if context_id.startswith("project-"):
        project_id = int(context_id.split("-")[1])
        project = session.query(Project).filter_by(id=project_id).first()
        return project.databaseId, project_id
    elif context_id.startswith("database-"):
        return int(context_id.split("-")[1]), None
    else:
        raise ValueError(f"Invalid context_id: {context_id}")


@socketio.on("ask")
def handle_ask(question, conversation_id=None, context_id=None):
    # We reset stop flag if the user sent a new request
    conversation_stop_flags.pop(conversation_id, None)

    with db_session() as session:
        # Extract database_id and project_id from the context
        database_id, project_id = extract_context(session, context_id)
        # Handle normal questions (not editing)
        agent = DatabaseChat(
            session,
            database_id,
            conversation_id,
            conversation_stop_flags,
            user_id=flask_session["user"].id,
            project_id=project_id,
        )
        for message in agent.ask(question):
            # We need to commit the session to save the message
            session.commit()
            emit("response", message.to_dict(session))


@socketio.on("query")
def handle_query(query, conversation_id=None, context_id=None):
    # We reset stop flag if the user sent a new request
    conversation_stop_flags.pop(conversation_id, None)

    with db_session() as session:
        database_id, project_id = extract_context(session, context_id)
        chat = DatabaseChat(
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
            conversationId=chat.conversation.id,
        )
        session.add(user_message)
        session.commit()
        emit("response", user_message.to_dict(session))
        # Run the SQL
        message = user_message.to_autochat_message()
        content = chat.chatbot.tools["database"].sql_query(query, from_response=message)
        user_message.queryId = message.query_id
        # Update the message with the linked query
        session.add(user_message)
        session.flush()

        # Display the response
        message = ConversationMessage(
            role="function",
            name="sql_query",
            content=content,
            conversationId=chat.conversation.id,
            isAnswer=True,
        )
        session.add(message)
        session.commit()
        emit("response", user_message.to_dict(session))
        emit("response", message.to_dict(session))


@socketio.on("regenerateFromMessage")
def handle_regenerate_from_message(conversation_id, message_id, message_content=None):
    """
    Regenerate the conversation from a specific message
    Delete all messages after the message_id and regenerate the conversation
    If the message is from the assistant, delete it
    If the message is from the user, regenerate the conversation from the next message
    """
    # We reset stop flag if the user sent a new request
    conversation_stop_flags.pop(conversation_id, None)

    with db_session() as session:
        conversation = session.query(Conversation).filter_by(id=conversation_id).first()

        # if message_content is not None, it means the user has edited the message
        if message_content is not None:
            message = (
                session.query(ConversationMessage).filter_by(id=message_id).first()
            )
            message.content = message_content
            session.commit()
            emit("response", message.to_dict(session))

        database_id = conversation.databaseId
        project_id = conversation.projectId
        chat = DatabaseChat(
            session,
            database_id,
            conversation_id,
            conversation_stop_flags,
            project_id=project_id,
        )
        # Clear all messages after the message_id, from the conversation
        messages = (
            session.query(ConversationMessage)
            .filter(
                ConversationMessage.id > message_id,
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

        session.commit()
        for message_id in deleted_message_ids:
            emit("delete-message", message_id)

        # Regenerate the conversation
        for message in chat._run_conversation():
            session.commit()
            emit("response", message.to_dict(session))


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
