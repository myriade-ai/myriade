"""
SocketIO event handlers for catalog room management.
"""

import logging

from flask import session as flask_session
from flask_socketio import emit, join_room, leave_room

from app import socketio
from chat.api import context_auth_required

logger = logging.getLogger(__name__)


@socketio.on("catalog:join")
@context_auth_required
def handle_catalog_join(_session, context_id: str, *, database_id, **_):
    """
    Join a catalog room for real-time updates.

    Args:
        context_id: Either "database-{id}" or "project-{id}"
        database_id: Extracted and injected by context_auth_required (keyword-only)
    """
    try:
        room = f"catalog:database:{database_id}"
        join_room(room)

        logger.info(
            f"User {flask_session['user'].id} joined catalog room {room} "
            f"for context {context_id}"
        )

        # Emit only to the requesting socket
        emit(
            "catalog:joined",
            {
                "context_id": context_id,
                "room": room,
            },
        )
    except Exception as e:
        logger.error(f"Error joining catalog room: {e}", exc_info=True)
        # Emit error only to the requesting socket
        emit("catalog:error", {"message": str(e)})


@socketio.on("catalog:leave")
@context_auth_required
def handle_catalog_leave(_session, context_id: str, *, database_id, **_):
    """Leave a catalog room.

    Args:
        context_id: Either "database-{id}" or "project-{id}"
        database_id: Extracted and injected by context_auth_required (keyword-only)
    """
    try:
        room = f"catalog:database:{database_id}"
        leave_room(room)

        logger.info(
            f"User {flask_session['user'].id} left catalog room {room} "
            f"for context {context_id}"
        )

        # Emit only to the requesting socket
        emit("catalog:left", {"context_id": context_id})
    except Exception as e:
        logger.error(f"Error leaving catalog room: {e}", exc_info=True)
        # Emit error only to the requesting socket
        emit("catalog:error", {"message": str(e)})
