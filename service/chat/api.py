from functools import wraps
from uuid import UUID

from flask import Blueprint
from flask import session as flask_session
from flask_socketio import emit

from app import socketio
from auth.auth import UnauthorizedError, socket_auth
from back.session import with_session
from chat.analyst_agent import DataAnalystAgent
from chat.lock import STATUS, clear_stop_flag, emit_status, set_stop_flag
from models import Conversation, ConversationMessage, User

api = Blueprint("chat_api", __name__)


def check_subscription_required(session):
    """Check if user has an active subscription or credits for the request."""
    # Get user from session using flask session
    user_id = flask_session["user"].id
    user = session.query(User).filter(User.id == user_id).first()

    # If user has active subscription, allow access
    if user.has_active_subscription:
        return True

    # Check if user has credits for free trial
    if user.credits > 0:
        return True

    return False


def consume_user_credit(session, conversation_id):
    """Decrement user credits if they're using free trial."""
    user_id = flask_session["user"].id
    user = session.query(User).filter(User.id == user_id).first()

    if not user or user.has_active_subscription:
        return  # No need to consume credits for subscribed users

    # Check if this is a public database (free to use)
    if conversation_id:
        try:
            conversation = (
                session.query(Conversation).filter_by(id=UUID(conversation_id)).first()
            )
            if conversation and conversation.database.public:
                return  # No need to consume credits for public databases
        except Exception:
            pass

    # Decrement credits if user has any
    if user.credits > 0:
        user.credits -= 1
        session.commit()


def socket_auth_required(f):
    """Decorator to ensure Socket.IO events are authenticated."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Check if user is authenticated via socket_auth
            if "user" not in flask_session:
                emit("error", {"message": "Authentication required"})
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


@socketio.on("stop")
@socket_auth_required
@conversation_auth_required
def handle_stop(session, conversation_id: str):
    print("Received stop signal for conversation_id", conversation_id)
    # Stop the query
    set_stop_flag(conversation_id)
    emit_status(conversation_id, STATUS.TO_STOP)


@socketio.on("ask")
@socket_auth_required
@conversation_auth_required
def handle_ask(session, conversation_id, question):
    # Check subscription requirement
    if not check_subscription_required(session):
        emit(
            "error",
            {"message": "SUBSCRIPTION_REQUIRED", "conversationId": conversation_id},
        )
        return

    # Consume credit if user is on free trial
    consume_user_credit(session, conversation_id)

    # We reset stop flag if the user sent a new request
    clear_stop_flag(conversation_id)

    conversation = (
        session.query(Conversation).filter_by(id=UUID(conversation_id)).first()
    )

    agent = DataAnalystAgent(
        session,
        conversation,
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
@socket_auth_required
@conversation_auth_required
def handle_query(
    session,
    query,
    conversation_id=None,
):
    # Check subscription requirement
    if not check_subscription_required(session):
        emit(
            "error",
            {"message": "SUBSCRIPTION_REQUIRED", "conversationId": conversation_id},
        )
        return

    # Consume credit if user is on free trial
    consume_user_credit(session, conversation_id)

    # We reset stop flag if the user sent a new request
    clear_stop_flag(conversation_id)

    conversation = (
        session.query(Conversation).filter_by(id=UUID(conversation_id)).first()
    )
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
    if not check_subscription_required(session):
        emit(
            "error",
            {"message": "SUBSCRIPTION_REQUIRED", "conversationId": conversation_id},
        )
        return

    # Consume credit if user is on free trial
    consume_user_credit(session, conversation_id)

    # We reset stop flag if the user sent a new request
    clear_stop_flag(conversation_id)

    # if message_content is not None, it means the user has edited the message
    if message_content is not None:
        message = (
            session.query(ConversationMessage).filter_by(id=UUID(message_id)).first()
        )
        message.content = message_content
        try:
            session.commit()
        except Exception as e:
            print(f"Error committing session: {e}")
            session.rollback()
            # We return to avoid sending the message
            return
        emit("response", message.to_dict())

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
        print(f"Error committing session: {e}")
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
