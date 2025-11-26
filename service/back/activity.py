"""
Activity tracking for catalog assets - audit trails, comments, and agent interactions.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from back.catalog_events import emit_activity_created, emit_activity_status_updated
from models.catalog import ActivityStatus, ActivityType, Asset, AssetActivity

logger = logging.getLogger(__name__)


def _values_equal(old_val, new_val) -> bool:
    """
    Compare two values for equality, handling special cases like lists
    where order should not matter (e.g., tags).
    """
    # Both None or both equal primitives
    if old_val == new_val:
        return True

    # If both are lists, compare as sets (order-independent)
    if isinstance(old_val, list) and isinstance(new_val, list):
        # Handle lists of strings (like tag names)
        try:
            return set(old_val) == set(new_val)
        except TypeError:
            # If items are not hashable, fall back to sorted comparison
            try:
                return sorted(old_val) == sorted(new_val)
            except TypeError:
                # If items are not sortable, use direct comparison
                return old_val == new_val

    return False


def create_activity(
    session: Session,
    asset_id: UUID,
    actor_id: str,
    activity_type: ActivityType | str,
    content: Optional[str] = None,
    changes: Optional[dict] = None,
    conversation_id: Optional[UUID] = None,
    status: Optional[str] = None,
) -> AssetActivity:
    """
    Create a new activity entry for an asset.

    Args:
        session: Database session
        asset_id: UUID of the asset
        actor_id: User ID or "myriade-agent"
        activity_type: Type of activity (from ActivityType enum)
        content: Text content for comments/agent messages
        changes: Structured data for audits: { field, old, new }
        conversation_id: Link to conversation for agent interactions
        status: Status for agent tasks (running, finished, error)

    Returns:
        The created AssetActivity instance
    """
    activity_type_str = (
        activity_type.value
        if isinstance(activity_type, ActivityType)
        else activity_type
    )

    status_str = status.value if isinstance(status, ActivityStatus) else status

    activity = AssetActivity(
        asset_id=asset_id,
        actor_id=actor_id,
        activity_type=activity_type_str,
        content=content,
        changes=changes,
        conversation_id=conversation_id,
        status=status_str,
        created_at=datetime.utcnow(),
    )

    session.add(activity)
    session.flush()

    # Get the asset to find database_id for broadcasting
    asset = session.query(Asset).filter(Asset.id == asset_id).first()
    if asset:
        emit_activity_created(activity, asset.database_id)

    logger.info(
        f"Created activity {activity.id} for asset {asset_id}: {activity_type_str}"
    )

    return activity


def create_audit_trail(
    session: Session,
    asset: Asset,
    actor_id: str,
    old_values: dict,
    new_values: dict,
) -> list[AssetActivity]:
    """
    Create audit trail activities by comparing old and new values.

    Args:
        session: Database session
        asset: The asset being modified
        actor_id: User ID or "myriade-agent"
        old_values: Dict of field names to old values
        new_values: Dict of field names to new values

    Returns:
        List of created AssetActivity instances
    """
    activities = []

    # Map field names to activity types
    field_to_activity_type = {
        "description": ActivityType.DESCRIPTION_UPDATED,
        "tags": ActivityType.TAGS_UPDATED,
        "status": ActivityType.STATUS_UPDATED,
    }

    for field, activity_type in field_to_activity_type.items():
        old_val = old_values.get(field)
        new_val = new_values.get(field)

        # Skip if field not in new_values (not being updated)
        if field not in new_values:
            continue

        # Skip if values are equal (use set comparison for tags to ignore order)
        if _values_equal(old_val, new_val):
            continue

        activity = create_activity(
            session=session,
            asset_id=asset.id,
            actor_id=actor_id,
            activity_type=activity_type,
            changes={
                "field": field,
                "old": old_val,
                "new": new_val,
            },
        )
        activities.append(activity)

    return activities


def create_suggestion_activity(
    session: Session,
    asset: Asset,
    actor_id: str,
    accepted: bool,
    suggestion_type: str = "description",
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
) -> AssetActivity:
    """
    Create activity for AI suggestion acceptance or rejection.

    Args:
        session: Database session
        asset: The asset
        actor_id: User ID who accepted/rejected
        accepted: True if accepted, False if rejected
        suggestion_type: "description" or "tags"
        old_value: Previous value (for accepted suggestions)
        new_value: New value (for accepted suggestions)

    Returns:
        The created AssetActivity instance
    """
    activity_type = (
        ActivityType.SUGGESTION_ACCEPTED
        if accepted
        else ActivityType.SUGGESTION_REJECTED
    )

    changes = {"suggestion_type": suggestion_type}
    if accepted:
        changes["old"] = old_value
        changes["new"] = new_value

    return create_activity(
        session=session,
        asset_id=asset.id,
        actor_id=actor_id,
        activity_type=activity_type,
        changes=changes,
    )


def create_agent_working_activity(
    session: Session,
    asset_id: UUID,
    conversation_id: UUID,
    user_message: Optional[str] = None,
) -> AssetActivity:
    """
    Create "agent working" activity when agent starts processing.

    Args:
        session: Database session
        asset_id: UUID of the asset
        conversation_id: UUID of the conversation
        user_message: Optional user message that triggered the agent

    Returns:
        The created AssetActivity instance
    """
    return create_activity(
        session=session,
        asset_id=asset_id,
        actor_id="myriade-agent",
        activity_type=ActivityType.AGENT_WORKING,
        content=user_message,
        conversation_id=conversation_id,
        status=ActivityStatus.RUNNING,
    )


def update_agent_activity_with_response(
    session: Session,
    activity_id: UUID,
    response_content: str,
) -> Optional[AssetActivity]:
    """
    Update an agent_working activity to agent_message with the response.

    Args:
        session: Database session
        activity_id: UUID of the activity to update
        response_content: The agent's response message

    Returns:
        The updated AssetActivity instance or None if not found
    """
    activity = (
        session.query(AssetActivity).filter(AssetActivity.id == activity_id).first()
    )

    if not activity:
        logger.warning(f"Activity {activity_id} not found for update")
        return None

    activity.activity_type = ActivityType.AGENT_MESSAGE.value
    activity.content = response_content
    session.flush()

    # Broadcast the update
    asset = session.query(Asset).filter(Asset.id == activity.asset_id).first()
    if asset:
        emit_activity_created(activity, asset.database_id)

    logger.info(f"Updated activity {activity_id} to agent_message")

    return activity


def run_agent_for_activity_background(
    conversation_id: UUID,
    activity_id: UUID,
    session_factory,
    sealed_session: str,
):
    """
    Run the agent in a background task for an asset feed conversation.

    Uses socketio.start_background_task to ensure compatibility with
    eventlet/gevent environments used by Flask-SocketIO.

    Args:
        conversation_id: UUID of the conversation
        activity_id: UUID of the agent_working activity to update
        session_factory: Function that returns a new SQLAlchemy session
        sealed_session: The sealed session token for AI proxy authentication
    """
    from flask import current_app

    from app import socketio

    # Capture the app reference while we're still in the request context
    app = current_app._get_current_object()

    def agent_task():
        """The actual agent task that runs in the background."""
        from flask import g

        from chat.analyst_agent import DataAnalystAgent
        from chat.lock import STATUS
        from models import Conversation, ConversationMessage

        # Create a new session for this task
        session: Session = session_factory()

        try:
            # Run within Flask app context and set the sealed_session
            # This is needed for the AI proxy authentication
            with app.app_context():
                # Set the sealed session in Flask's g object for the proxy provider
                g.sealed_session = sealed_session

                # Get the conversation
                conversation = (
                    session.query(Conversation).filter_by(id=conversation_id).first()
                )
                if not conversation:
                    logger.error(f"Conversation {conversation_id} not found")
                    return

                # Get the activity to update
                activity = (
                    session.query(AssetActivity).filter_by(id=activity_id).first()
                )
                if not activity:
                    logger.error(f"Activity {activity_id} not found")
                    return

                # Get asset for broadcasting
                asset = (
                    session.query(Asset).filter(Asset.id == activity.asset_id).first()
                )

                # Create the agent
                # Note: _run_conversation() handles emit_status internally
                agent = DataAnalystAgent(session, conversation)

                # Get the user message (the first message in the conversation)
                user_message = (
                    session.query(ConversationMessage)
                    .filter_by(conversationId=conversation_id, role="user")
                    .order_by(ConversationMessage.createdAt.asc())
                    .first()
                )

                if not user_message:
                    logger.error(
                        f"No user message found in conversation {conversation_id}"
                    )
                    return

                # Process with the agent
                # Note: We call _run_conversation() directly instead of ask()
                # because the user message was already created in the API endpoint.
                # ask() would create a duplicate message.
                last_answer_content = None
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

                    # Emit response to conversation room
                    response_data = message.to_dict_with_linked_models(session)
                    socketio.emit(
                        "response",
                        response_data,
                        to=str(conversation_id),
                    )

                    # Track the last answer message
                    if message.isAnswer and message.content:
                        last_answer_content = message.content

                # Update the agent_working activity status to finished
                activity.status = ActivityStatus.FINISHED.value
                session.commit()

                # Broadcast the status update
                if asset:
                    emit_activity_status_updated(
                        activity.id, asset.database_id, ActivityStatus.FINISHED.value
                    )

                # Post the final answer as a separate agent_message activity
                if last_answer_content and asset:
                    create_activity(
                        session=session,
                        asset_id=activity.asset_id,
                        actor_id="myriade-agent",
                        activity_type=ActivityType.AGENT_MESSAGE,
                        content=last_answer_content,
                        conversation_id=conversation_id,
                    )
                    session.commit()

                # Note: _run_conversation() handles emit_status(CLEAR) internally

                logger.info(
                    f"Agent completed for conversation {conversation_id}, "
                    f"activity {activity_id}"
                )

        except Exception as e:
            logger.error(
                f"Error running agent for activity: {e}",
                exc_info=True,
            )

            # Update activity status to error
            try:
                activity = (
                    session.query(AssetActivity).filter_by(id=activity_id).first()
                )
                if activity:
                    activity.status = ActivityStatus.ERROR.value
                    session.commit()

                    # Broadcast the error status
                    asset = (
                        session.query(Asset)
                        .filter(Asset.id == activity.asset_id)
                        .first()
                    )
                    if asset:
                        emit_activity_status_updated(
                            activity.id, asset.database_id, ActivityStatus.ERROR.value
                        )
            except Exception as status_error:
                logger.error(
                    f"Failed to update activity status to error: {status_error}"
                )
                session.rollback()

            # Emit error status to conversation
            socketio.emit(
                "status",
                {
                    "conversation_id": str(conversation_id),
                    "status": STATUS.ERROR,
                    "error": str(e),
                },
            )
            session.rollback()
        finally:
            session.close()

    # Start the background task using socketio's eventlet-compatible method
    socketio.start_background_task(agent_task)
    logger.info(
        f"Started agent background task for conversation {conversation_id}, activity {activity_id}"
    )
