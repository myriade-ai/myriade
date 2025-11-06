"""
In-memory sync state management.

This module provides thread-safe storage for database sync operations state.
The state is kept in memory only and cleared immediately after sync completion.
"""

import logging
from datetime import datetime
from threading import Lock
from typing import Dict, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

# Thread-safe in-memory storage for active sync states
_active_syncs: Dict[str, dict] = {}
_lock = Lock()


def set_sync_state(
    database_id: UUID,
    status: str,
    progress: int,
    error: Optional[str] = None,
) -> None:
    """
    Set the sync state for a database (thread-safe).

    Args:
        database_id: UUID of the database
        status: Sync status ('idle', 'syncing', 'completed', 'failed')
        progress: Progress percentage (0-100)
        error: Optional error message if status is 'failed'
    """
    db_id_str = str(database_id)

    with _lock:
        _active_syncs[db_id_str] = {
            "sync_status": status,
            "sync_progress": progress,
            "sync_error": error,
            "updated_at": datetime.utcnow().isoformat(),
        }

    logger.debug(
        f"Sync state updated for database {db_id_str}: "
        f"status={status}, progress={progress}%"
    )


def get_sync_state(database_id: UUID) -> dict:
    """
    Get the sync state for a database (thread-safe).

    Args:
        database_id: UUID of the database

    Returns:
        Dict with sync_status, sync_progress, sync_error, updated_at.
        Returns idle state if no active sync found.
    """
    db_id_str = str(database_id)

    with _lock:
        state = _active_syncs.get(db_id_str)

    if state:
        return state
    else:
        # Return default idle state
        return {
            "sync_status": "idle",
            "sync_progress": 0,
            "sync_error": None,
            "updated_at": None,
        }


def clear_sync_state(database_id: UUID) -> None:
    """
    Clear the sync state for a database (thread-safe).

    Called when sync completes (success or failure) to clean up memory.

    Args:
        database_id: UUID of the database
    """
    db_id_str = str(database_id)

    with _lock:
        if db_id_str in _active_syncs:
            del _active_syncs[db_id_str]
            logger.debug(f"Sync state cleared for database {db_id_str}")


def get_all_active_syncs() -> Dict[str, dict]:
    """
    Get all active syncs (for debugging/monitoring).

    Returns:
        Dict mapping database_id -> sync state
    """
    with _lock:
        return dict(_active_syncs)
