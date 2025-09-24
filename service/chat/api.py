import logging
from functools import wraps
from uuid import UUID

from flask import Blueprint
from flask import session as flask_session
from flask_socketio import emit
from sqlalchemy.orm.attributes import flag_modified

from app import socketio
from auth.auth import UnauthorizedError, socket_auth
from back.session import with_session
from chat.analyst_agent import DataAnalystAgent
from chat.lock import (
    STATUS,
    emit_status,
    set_stop_flag,
)
from chat.tools.database import cancel_query
from models import Conversation, ConversationMessage, Query
from models.catalog import Asset, Term

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


@socketio.on("stop")
@socket_auth_required
@conversation_auth_required
def handle_stop(session, conversation_id: UUID):
    logger.info(
        "Received stop signal for conversation",
        extra={"conversation_id": conversation_id},
    )
    # Stop the query - convert string to UUID for the lock functions
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
        response_data = message.to_dict()

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


@socketio.on("confirmCatalogOperation")
@socket_auth_required
@conversation_auth_required
def handle_confirm_catalog_operation(
    session,
    conversation_id: UUID,
    function_call_id: str,
    updated_proposed: dict | None = None,
):
    """Execute a confirmed catalog operation proposal."""

    conversation = session.query(Conversation).filter_by(id=conversation_id).first()
    if not conversation:
        emit("error", {"message": "Conversation not found"})
        return

    function_message = (
        session.query(ConversationMessage)
        .filter_by(
            conversationId=conversation_id,
            functionCallId=function_call_id,
            role="assistant",
        )
        .first()
    )

    if not function_message or not function_message.functionCall:
        emit("error", {"message": "Catalog operation proposal not found"})
        return

    arguments = function_message.functionCall.get("arguments")
    if not isinstance(arguments, dict):
        arguments = {}
        function_message.functionCall["arguments"] = arguments

    proposal = arguments.get("proposal")

    if not proposal or not isinstance(proposal, dict):
        emit("error", {"message": "Catalog operation proposal missing"})
        return

    if isinstance(updated_proposed, dict):
        proposal["proposed"] = updated_proposed

    entity_raw = proposal.get("entity")
    entity = entity_raw if isinstance(entity_raw, dict) else {}
    entity_type = entity.get("type")
    entity_id = entity.get("id")
    entity_uuid: UUID | None = None

    if entity_id:
        try:
            entity_uuid = UUID(str(entity_id))
        except ValueError:
            emit("error", {"message": "Invalid entity identifier for approval"})
            return

    proposal_status = proposal.get("status")
    is_pending_review = proposal_status == "pending_review"

    if is_pending_review and (not entity_type or entity_uuid is None):
        emit("error", {"message": "Missing entity information for approval"})
        return

    proposed_raw = proposal.get("proposed")
    proposed = proposed_raw if isinstance(proposed_raw, dict) else {}
    operation = proposal.get("operation")

    agent = DataAnalystAgent(session, conversation)
    catalog_tool = agent.agent.tools.get("catalog")
    if catalog_tool is None:
        emit("error", {"message": "Catalog tool not available"})
        return

    try:
        if operation == "update_asset":
            asset_id = entity.get("id")
            if not asset_id:
                emit("error", {"message": "Missing asset identifier for confirmation"})
                return
            description_value = proposed.get("description")
            tags_value = proposed.get("tags")

            proposed = {
                **proposed,
                "description": description_value,
                "tags": tags_value,
            }
            proposal["proposed"] = proposed

            result = catalog_tool.update_asset(
                asset_id=str(asset_id),
                description=description_value,
                tags=tags_value,
                from_response=None,
            )
        elif operation == "upsert_term":
            name = proposed.get("name")
            definition = proposed.get("definition")
            if not name or not definition:
                emit(
                    "error",
                    {"message": "Incomplete term information for confirmation"},
                )
                return
            name_value = name.strip() if isinstance(name, str) else str(name)
            definition_value = proposed.get("definition")
            synonyms_value = proposed.get("synonyms")
            domains_value = proposed.get("business_domains")

            proposed = {
                **proposed,
                "name": name_value,
                "definition": definition_value,
                "synonyms": synonyms_value,
                "business_domains": domains_value,
            }
            proposal["proposed"] = proposed
            result = catalog_tool.upsert_term(
                name=name_value,
                definition=definition_value,
                synonyms=synonyms_value,
                business_domains=domains_value,
                id=entity.get("id"),
                from_response=None,
            )
        else:
            emit("error", {"message": "Unsupported catalog operation"})
            return
    except Exception as exc:
        logger.error(
            "Error executing catalog proposal",
            exc_info=True,
            extra={"error": str(exc)},
        )
        emit("error", {"message": str(exc)})
        session.rollback()
        return

    if is_pending_review and entity_uuid is not None:
        if entity_type == "asset":
            target = session.query(Asset).filter_by(id=entity_uuid).first()
        elif entity_type == "term":
            target = session.query(Term).filter_by(id=entity_uuid).first()
        else:
            target = None

        if target is None:
            emit(
                "error",
                {"message": "Entity not found for approval", "entityId": entity_id},
            )
            session.rollback()
            return

        target.reviewed = True
        session.flush()

    proposal["status"] = "approved" if is_pending_review else "confirmed"
    proposal["reviewed"] = True
    arguments["proposal"] = proposal
    flag_modified(function_message, "functionCall")
    session.flush()
    emit("response", function_message.to_dict())

    response_message = ConversationMessage(
        role="function",
        name=function_message.functionCall.get("name"),
        content=result,
        conversationId=conversation.id,
        functionCallId=function_call_id,
    )
    session.add(response_message)
    session.flush()
    emit("response", response_message.to_dict())

    session.commit()

    agent = DataAnalystAgent(session, conversation)
    for message in agent._run_conversation():
        try:
            session.commit()
        except Exception as e:
            logger.error(
                "Error committing session",
                exc_info=True,
                extra={"error": str(e)},
            )
            session.rollback()
            break
        response_data = message.to_dict()

        credits_remaining = get_last_credits_info()
        if credits_remaining is not None:
            response_data["credits_remaining"] = credits_remaining

        emit("response", response_data)
    session.commit()


@socketio.on("rejectCatalogOperation")
@socket_auth_required
@conversation_auth_required
def handle_reject_catalog_operation(
    session, conversation_id: UUID, function_call_id: str
):
    """Handle user rejection of a catalog proposal."""

    conversation = session.query(Conversation).filter_by(id=conversation_id).first()
    if not conversation:
        emit("error", {"message": "Conversation not found"})
        return

    function_message = (
        session.query(ConversationMessage)
        .filter_by(
            conversationId=conversation_id,
            functionCallId=function_call_id,
            role="assistant",
        )
        .first()
    )

    if not function_message or not function_message.functionCall:
        emit("error", {"message": "Catalog operation proposal not found"})
        return

    arguments = function_message.functionCall.get("arguments")
    if not isinstance(arguments, dict):
        arguments = {}
        function_message.functionCall["arguments"] = arguments

    proposal = arguments.get("proposal")

    if not proposal or not isinstance(proposal, dict):
        emit("error", {"message": "Catalog operation proposal missing"})
        return

    proposal["status"] = "rejected"
    arguments["proposal"] = proposal
    flag_modified(function_message, "functionCall")
    session.flush()
    emit("response", function_message.to_dict())

    response_message = ConversationMessage(
        role="function",
        name=function_message.functionCall.get("name"),
        content="User rejected the catalog operation proposal",
        conversationId=conversation.id,
        functionCallId=function_call_id,
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
    except UnauthorizedError as e:
        emit("error", str(e))
        return False  # Reject the connection

    flask_session.update(
        user=auth_response.user,
        role=auth_response.role,
        organization_id=auth_response.organization_id,
        sealed_session=auth_response.sealed_session,
    )
