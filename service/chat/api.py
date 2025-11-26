import logging
from functools import wraps
from uuid import UUID

from flask import Blueprint
from flask import session as flask_session
from flask_socketio import emit, join_room, leave_room
from pydantic import validate_call

from app import socketio
from auth.auth import OrganizationRestrictedError, UnauthorizedError, socket_auth
from back.session import with_session
from chat.analyst_agent import DataAnalystAgent
from chat.lock import (
    STATUS,
    emit_status,
    set_stop_flag,
)
from chat.tools.database import cancel_query
from models import Conversation, ConversationMessage, Database, Query

api = Blueprint("chat_api", __name__)
logger = logging.getLogger(__name__)


def get_last_credits_info():
    """Get the credits remaining from the last AI call."""
    from chat.proxy_provider import get_last_response_data

    return get_last_response_data("credits_remaining")


def socket_auth_required(f):
    """Decorator to ensure Socket.IO events are authenticated."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Check if user is authenticated via socket_auth
            if "user" not in flask_session:
                emit("error", {"message": "Authentication required"})
                return

            # Ensure sealed_session is available for AI proxy calls
            if "sealed_session" not in flask_session:
                emit("error", {"message": "Session data missing - please reconnect"})
                return

        except Exception:
            emit("error", {"message": "Authentication failed"})
            return
        return f(*args, **kwargs)

    return decorated_function


def conversation_auth_required(f):
    """Decorator to verify user owns the conversation in Socket.IO events."""

    @wraps(f)
    @with_session
    def decorated_function(session, *args, **kwargs):
        # Extract conversation_id from arguments
        conversation_id = None
        if len(args) > 0 and isinstance(args[0], str):
            conversation_id = args[0]
        elif "conversation_id" in kwargs:
            conversation_id = kwargs["conversation_id"]

        if not conversation_id:
            emit("error", {"message": "Conversation ID required"})
            return

        try:
            conversation = (
                session.query(Conversation).filter_by(id=UUID(conversation_id)).first()
            )
            if not conversation:
                emit(
                    "error",
                    {
                        "message": "Conversation not found",
                        "conversationId": conversation_id,
                    },
                )
                return

            # Verify user owns this conversation
            user_id = flask_session["user"].id
            if conversation.ownerId != user_id:
                emit(
                    "error",
                    {"message": "Access denied", "conversationId": conversation_id},
                )
                return

        except Exception:
            emit(
                "error",
                {"message": "Authorization failed", "conversationId": conversation_id},
            )
            return

        return f(session, *args, **kwargs)

    return decorated_function


def database_auth_required(f):
    """Decorator to verify user has access to a database in Socket.IO events."""

    @wraps(f)
    @with_session
    def decorated_function(session, *args, **kwargs):
        database_id_arg = None
        if len(args) > 0 and isinstance(args[0], str):
            database_id_arg = args[0]
        elif "database_id" in kwargs:
            database_id_arg = kwargs["database_id"]

        if not database_id_arg:
            emit("error", {"message": "Database ID required"})
            return

        if "user" not in flask_session:
            emit("error", {"message": "Authentication required"})
            return

        try:
            database_uuid = UUID(str(database_id_arg))
        except (TypeError, ValueError):
            emit("error", {"message": "Invalid database ID"})
            return

        try:
            database = session.query(Database).filter_by(id=database_uuid).first()
            if not database:
                emit(
                    "error",
                    {
                        "message": "Database not found",
                        "databaseId": str(database_uuid),
                    },
                )
                return

            user_id = flask_session["user"].id
            organization_id = flask_session.get("organization_id")
            has_access = (
                database.ownerId == user_id
                or (organization_id and database.organisationId == organization_id)
                or database.public
            )

            if not has_access:
                emit(
                    "error",
                    {"message": "Access denied", "databaseId": str(database_uuid)},
                )
                return
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"Database authorization failed: {exc}", exc_info=True)
            emit(
                "error",
                {
                    "message": "Authorization failed",
                    "databaseId": str(database_uuid),
                },
            )
            return

        kwargs["database_id"] = database_uuid
        # Skip database_id from args if it was passed as first positional argument
        if len(args) > 0 and isinstance(args[0], str):
            remaining_args = args[1:]
        else:
            remaining_args = args
        return f(session, *remaining_args, **kwargs)

    return decorated_function


@socketio.on("stop")
@socket_auth_required
@conversation_auth_required
@validate_call
def handle_stop(session, conversation_id: UUID):
    logger.info(
        "Received stop signal for conversation",
        extra={"conversation_id": conversation_id},
    )
    set_stop_flag(conversation_id)
    emit_status(conversation_id, STATUS.TO_STOP)


@socketio.on("ask")
@socket_auth_required
@conversation_auth_required
def handle_ask(session, conversation_id: UUID, question: str):
    conversation = session.query(Conversation).filter_by(id=conversation_id).first()

    agent = DataAnalystAgent(
        session,
        conversation,
    )
    for message in agent.ask(question):
        # We need to commit the session to save the message
        try:
            session.commit()
        except Exception as e:
            logger.error(
                "Error committing session", exc_info=True, extra={"error": str(e)}
            )
            session.rollback()
            # We break the loop to avoid sending the message
            break
        response_data = message.to_dict_with_linked_models(session)

        # Include credits info if available from proxy
        credits_remaining = get_last_credits_info()
        if credits_remaining is not None:
            response_data["credits_remaining"] = credits_remaining

        emit("response", response_data)


@socketio.on("query")
@socket_auth_required
@conversation_auth_required
def handle_query(
    session,
    query,
    conversation_id: UUID | None = None,
):
    conversation = session.query(Conversation).filter_by(id=conversation_id).first()
    agent = DataAnalystAgent(
        session,
        conversation,
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
    message = user_message.to_agentlys_message()
    content = agent.agent.tools["database"].sql_query(query, from_response=message)
    user_message.queryId = message.query_id
    # Update the message with the linked query
    session.add(user_message)
    session.flush()
    # We re-emit the user message to update the query id
    emit("response", user_message.to_dict())

    # Display the response
    result_message = ConversationMessage(
        role="function",
        name="sql_query",
        content=content,
        conversationId=agent.conversation.id,
        isAnswer=True,
    )

    session.add(result_message)
    session.flush()
    emit("response", result_message.to_dict())


@socketio.on("confirmWriteOperation")
@socket_auth_required
@conversation_auth_required
def handle_confirm_write_operation(session, conversation_id: UUID, query_id: UUID):
    """
    Handle user approval of a write operation.
    """
    # Get conversation message from function call
    functionCallMessage = (
        session.query(ConversationMessage)
        .filter_by(queryId=query_id, role="assistant")
        .first()
    )
    if not functionCallMessage:
        emit("error", {"message": "Operation message not found"})
        return

    conversation = (
        session.query(Conversation)
        .filter_by(id=functionCallMessage.conversationId)
        .first()
    )
    agent = DataAnalystAgent(session, conversation)
    database_tool = agent.agent.tools["database"]

    # Execute the confirmed write operation
    result, success = database_tool._execute_confirmed_query(query_id)

    # Refresh the session to see the updated query
    session.flush()  # Ensure all changes are written to the database
    query = session.query(Query).filter_by(id=query_id).first()
    session.refresh(query)  # Refresh the object from the database

    emit("queryUpdated", query.to_dict())

    # Create a response message with the result
    response_message = ConversationMessage(
        role="function",
        name="sql_query",
        content=result,
        conversationId=conversation.id,
        queryId=query_id,
        functionCallId=functionCallMessage.functionCallId,
    )
    session.add(response_message)
    session.flush()

    emit("response", response_message.to_dict())

    session.commit()
    agent = DataAnalystAgent(session, conversation)
    for message in agent._run_conversation():
        # We need to commit the session to save the message
        try:
            session.commit()
        except Exception as e:
            logger.error(
                "Error committing session", exc_info=True, extra={"error": str(e)}
            )
            session.rollback()
            # We break the loop to avoid sending the message
            break
        response_data = message.to_dict()

        # Include credits info if available from proxy
        credits_remaining = get_last_credits_info()
        if credits_remaining is not None:
            response_data["credits_remaining"] = credits_remaining

        emit("response", response_data)
    session.commit()


@socketio.on("rejectWriteOperation")
@socket_auth_required
@conversation_auth_required
def handle_reject_write_operation(session, conversation_id: UUID, query_id: UUID):
    """
    Handle user cancellation of a write operation.
    """
    # Get conversation message from function call
    functionCallMessage = (
        session.query(ConversationMessage)
        .filter_by(queryId=query_id, role="assistant")
        .first()
    )
    conversation = (
        session.query(Conversation)
        .filter_by(id=functionCallMessage.conversationId)
        .first()
    )
    # Cancel the write operation
    query = cancel_query(session, query_id)
    emit("queryUpdated", query.to_dict())

    # Create a response message indicating cancellation
    response_message = ConversationMessage(
        role="function",
        name="sql_query",
        content="User didn't confirmed the write operation",
        conversationId=conversation.id,
        queryId=query_id,
        functionCallId=functionCallMessage.functionCallId,
    )
    session.add(response_message)
    session.flush()
    emit("response", response_message.to_dict())
    session.commit()


@socketio.on("regenerateFromMessage")
@socket_auth_required
@conversation_auth_required
def handle_regenerate_from_message(
    session, conversation_id, message_id, message_content=None
):
    """
    Regenerate the conversation from a specific message
    Delete all messages after the message_id and regenerate the conversation
    If the message is from the assistant, delete it
    If the message is from the user, regenerate the conversation from the next message
    """
    # if message_content is not None, it means the user has edited the message
    if message_content is not None:
        message = (
            session.query(ConversationMessage).filter_by(id=UUID(message_id)).first()
        )
        message.content = message_content
        try:
            session.commit()
        except Exception as e:
            logger.error(
                "Error committing session", exc_info=True, extra={"error": str(e)}
            )
            session.rollback()
            # We return to avoid sending the message
            return
        response_data = message.to_dict()

        # Include credits info if available from proxy
        credits_remaining = get_last_credits_info()
        if credits_remaining is not None:
            response_data["credits_remaining"] = credits_remaining

        emit("response", response_data)

    # Clear all messages after the message_id, from the conversation
    selected_message = (
        session.query(ConversationMessage).filter_by(id=UUID(message_id)).first()
    )
    messages = (
        session.query(ConversationMessage)
        .filter(
            ConversationMessage.createdAt > selected_message.createdAt,
            ConversationMessage.conversationId == UUID(conversation_id),
        )
        .all()
    )
    deleted_message_ids = []
    for message in messages:
        deleted_message_ids.append(message.id)
        session.delete(message)

    # Also, if the message is from the assistant, delete it
    message = (
        session.query(ConversationMessage)
        .filter_by(id=UUID(message_id), conversationId=UUID(conversation_id))
        .first()
    )
    if message.role == "assistant":
        deleted_message_ids.append(message.id)
        session.delete(message)

    try:
        # Delete the messages
        session.commit()
    except Exception as e:
        logger.error("Error committing session", exc_info=True, extra={"error": str(e)})
        session.rollback()
        # We return to avoid sending the message
        return
    for message_id in deleted_message_ids:
        emit("delete-message", str(message_id))

    conversation = (
        session.query(Conversation).filter_by(id=UUID(conversation_id)).first()
    )

    # Regenerate the conversation
    agent = DataAnalystAgent(
        session,
        conversation,
    )
    for message in agent._run_conversation():
        try:
            session.commit()
        except Exception as e:
            logger.error(
                "Error committing session", exc_info=True, extra={"error": str(e)}
            )
            session.rollback()
            # We return to avoid sending the message
            break
        response_data = message.to_dict()

        # Include credits info if available from proxy
        credits_remaining = get_last_credits_info()
        if credits_remaining is not None:
            response_data["credits_remaining"] = credits_remaining

        emit("response", response_data)


@socketio.on("connect")
def on_connect():
    # This is where you would initialize your session
    # or any other per-connection resources.
    try:
        auth_response = socket_auth()
    except OrganizationRestrictedError:
        emit("error", {"type": "ORGANIZATION_RESTRICTED"})
        return False  # Reject the connection
    except UnauthorizedError as e:
        emit("error", str(e))
        return False  # Reject the connection

    flask_session.update(
        user=auth_response.user,
        role=auth_response.role,
        organization_id=auth_response.organization_id,
        sealed_session=auth_response.sealed_session,
    )


@socketio.on("join")
@socket_auth_required
def handle_join(conversation_id: str):
    """Join a conversation room to receive real-time updates."""
    logger.info(f"Client joining conversation room: {conversation_id}")
    join_room(conversation_id)


@socketio.on("leave")
@socket_auth_required
def handle_leave(conversation_id: str):
    """Leave a conversation room."""
    logger.info(f"Client leaving conversation room: {conversation_id}")
    leave_room(conversation_id)
