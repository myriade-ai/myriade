from threading import Lock

from flask_socketio import emit

conversation_stop_flags: dict[str, bool] = {}
stop_flag_lock = Lock()


class StopException(Exception):
    pass


class STATUS:
    RUNNING = "running"
    CLEAR = "clear"
    TO_STOP = "to_stop"
    ERROR = "error"


def check_and_clear_stop_flag(conversation_id: str) -> bool:
    """Thread-safe check and clear of stop flag for a conversation.

    Returns:
        True if stop flag was set (and has been cleared), False otherwise
    """
    with stop_flag_lock:
        if conversation_stop_flags.get(conversation_id):
            del conversation_stop_flags[conversation_id]
            return True
        return False


def set_stop_flag(conversation_id: str) -> None:
    """Thread-safe setting of stop flag for a conversation."""
    with stop_flag_lock:
        conversation_stop_flags[conversation_id] = True


def clear_stop_flag(conversation_id: str) -> None:
    """Thread-safe clearing of stop flag for a conversation."""
    with stop_flag_lock:
        conversation_stop_flags.pop(conversation_id, None)


def emit_status(conversation_id, status, error=None):
    emit(
        "status",
        {
            "conversation_id": str(conversation_id),
            "status": status,
            "error": str(error),
        },
    )
