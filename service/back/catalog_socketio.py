"""
SocketIO event handlers for catalog room management.
"""

import logging
from uuid import UUID

from flask import session as flask_session
from flask_socketio import emit, join_room, leave_room

from app import socketio
from chat.api import database_auth_required

logger = logging.getLogger(__name__)


@socketio.on("catalog:join")
@database_auth_required
def handle_catalog_join(_session, database_id: UUID, **_):
    """Join a database-specific catalog room for real-time updates."""
    try:
        room = f"catalog:database:{database_id}"
        join_room(room)

        logger.info(
            "User %s joined catalog room %s",
            flask_session["user"].id,
            room,
        )

        # Emit only to the requesting socket
        emit(
            "catalog:joined",
            {"database_id": str(database_id), "room": room},
        )
    except Exception as e:
        logger.error(f"Error joining catalog room: {e}", exc_info=True)
        # Emit error only to the requesting socket
        emit("catalog:error", {"message": str(e)})


@socketio.on("catalog:leave")
@database_auth_required
def handle_catalog_leave(_session, database_id: UUID, **_):
    """Leave a database-specific catalog room."""
    try:
        room = f"catalog:database:{database_id}"
        leave_room(room)

        logger.info(
            "User %s left catalog room %s",
            flask_session["user"].id,
            room,
        )

        # Emit only to the requesting socket
        emit("catalog:left", {"database_id": str(database_id)})
    except Exception as e:
        logger.error(f"Error leaving catalog room: {e}", exc_info=True)
        # Emit error only to the requesting socket
        emit("catalog:error", {"message": str(e)})
