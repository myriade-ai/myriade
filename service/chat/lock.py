from threading import Lock

from flask_socketio import emit

conversation_stop_flags: dict[int, bool] = {}
stop_flag_lock = Lock()


class StopException(Exception):
    pass


class STATUS:
    RUNNING = "running"
    CLEAR = "clear"
    TO_STOP = "to_stop"
    ERROR = "error"


def emit_status(conversation_id, status, error=None):
    emit(
        "status",
        {"conversation_id": conversation_id, "status": status, "error": str(error)},
    )
