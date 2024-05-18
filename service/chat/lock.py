from threading import Lock

from flask_socketio import emit

conversation_stop_flags = {}
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


def handle_stop_flag(func):
    """
    Decorator that handles the stop flag for a conversation.
    Work like this:
    - When a 'ask' event is received, we create a stop flag for the conversation
    - When a 'stop' event is received, we set the stop flag to True
    - When the query is done, we remove the stop flag
    """

    def wrapper(*args, **kwargs):
        # Extract the conversation_id from the arguments
        conversation_id = args[1] or "new"

        # with stop_flag_lock:
        #     # Avoid running the same query twice
        #     if conversation_id in conversation_stop_flags:
        #         # We re-emit the running status to the client
        #         if conversation_stop_flags[conversation_id]:
        #             emit_status(conversation_id, STATUS.TO_STOP)
        #         else:
        #             emit_status(conversation_id, STATUS.RUNNING)
        #         return

        # with stop_flag_lock:
        #     # Remove the stop flag
        #     del conversation_stop_flags[conversation_id]
        #     emit_status(conversation_id, STATUS.RUNNING)

        conversation_stop_flags[conversation_id] = False
        emit_status(conversation_id, STATUS.RUNNING)
        try:
            res = func(*args, **kwargs)
        except StopException:
            emit_status(conversation_id, STATUS.CLEAR)
        except Exception as e:
            emit_status(conversation_id, STATUS.ERROR, e)
            raise e
        else:
            emit_status(conversation_id, STATUS.CLEAR)
        finally:
            with stop_flag_lock:
                # Remove the stop flag
                del conversation_stop_flags[conversation_id]

        return res

    return wrapper
