from app import socketio
from flask import Blueprint
from flask_socketio import emit

from back.models import ConversationMessage, Project
from back.session import Session
from chat.datachat import DatabaseChat
from chat.lock import (
    STATUS,
    conversation_stop_flags,
    emit_status,
    handle_stop_flag,
    stop_flag_lock,
)

api = Blueprint("chat_api", __name__)
socket_session = None

@socketio.on("stop")
def handle_stop(conversation_id):
    print("Received stop signal for conversation_id", conversation_id)
    # Stop the query
    with stop_flag_lock:
        if conversation_id in conversation_stop_flags:
            conversation_stop_flags[conversation_id] = True
            emit_status(conversation_id, STATUS.TO_STOP)

        else:
            print(
                f"No active 'ask' process found for conversation_id {conversation_id}"
            )


def extract_context(context_id):
    """
    Extract the databaseId from the context_id
    context is "project-{projectId}" or "database-{databaseId}"
    """
    if context_id.startswith("project-"):
        project_id = int(context_id.split("-")[1])
        project = socket_session.query(Project).filter_by(id=project_id).first()
        return project.databaseId, project_id
    elif context_id.startswith("database-"):
        return int(context_id.split("-")[1]), None


@socketio.on("ask")
@handle_stop_flag
def handle_ask(question, conversation_id=None, context_id=None):
    database_id, project_id = extract_context(context_id)
    iterator = DatabaseChat(
        socket_session,
        database_id,
        conversation_id,
        conversation_stop_flags,
        project_id=project_id,
    ).ask(question)
    for message in iterator:
        emit("response", message.to_dict())


@socketio.on("query")
@handle_stop_flag
def handle_query(query, conversation_id=None, context_id=None):
    database_id, project_id = extract_context(context_id)
    chat = DatabaseChat(
        socket_session,
        database_id,
        conversation_id,
        conversation_stop_flags,
        project_id=project_id,
    )

    user_message = ConversationMessage(
        role="user",
        functionCall={
            "name": "SQL_QUERY",
            "arguments": {
                "query": query,
            },
        },
        conversationId=chat.conversation.id,
    )
    socket_session.add(user_message)
    socket_session.commit()
    emit("response", user_message.to_dict())
    # Run the SQL
    message = user_message.to_autochat_message()
    content = chat.sql_query(query, from_response=message)
    user_message.queryId = message.query_id
    # Update the message with the linked query
    socket_session.add(user_message)
    emit("response", user_message.to_dict())

    # Display the response
    message = ConversationMessage(
        role="function",
        name="SQL_QUERY",
        content=content,
        conversationId=chat.conversation.id,
    )
    socket_session.add(message)
    socket_session.commit()
    emit("response", message.to_dict())


@socketio.on("regenerateFromMessage")
@handle_stop_flag
def handle_regenerate_from_message(message_id, conversation_id=None, context_id=None):
    """
    Regenerate the conversation from a specific message
    Delete all messages after the message_id and regenerate the conversation
    If the message is from the assistant, delete it
    If the message is from the user, regenerate the conversation from the next message
    """
    database_id, project_id = extract_context(context_id)
    chat = DatabaseChat(
        socket_session,
        database_id,
        conversation_id,
        conversation_stop_flags,
        project_id=project_id,
    )
    # Clear all messages after the message_id
    messages = (
        socket_session.query(ConversationMessage)
        .filter(ConversationMessage.id > message_id)
        .all()
    )
    for message in messages:
        emit("delete-message", message.id)
        socket_session.delete(message)
    # Also, if the message is from the assistant, delete it

    message = socket_session.query(ConversationMessage).filter_by(id=message_id).first()
    if message.role == "assistant":
        emit("delete-message", message.id)
        socket_session.delete(message)

    socket_session.commit()
    # Regenerate the conversation
    for message in chat._run_conversation():
        print("MESSAGE", message.to_dict())
        emit("response", message.to_dict())


@socketio.on("connect")
def on_connect():
    # This is where you would initialize your session
    # or any other per-connection resources.
    global socket_session
    socket_session = Session()


@socketio.on("disconnect")
def on_disconnect():
    # Cleanup: Close or remove any resources you initialized on connect
    socket_session.close()