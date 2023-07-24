from threading import Lock

from back.models import User, format_to_camel_case
from back.session import session
from chat.datachat import DatabaseChat
from chat.lock import (
    STATUS,
    conversation_stop_flags,
    emit_status,
    handle_stop_flag,
    stop_flag_lock,
)
from flask import Blueprint
from flask_socketio import emit

api = Blueprint("chat_api", __name__)

from app import socketio

MAX_DATA_SIZE = 4000  # Maximum size of the data to return
CONVERSATION_MAX_ATTEMPT = 10  # Number of attempts to ask the ai before giving up


def user_has_access(user_id: int, database_id: int) -> bool:
    """
    Check if a user has access to a specific database.

    :param user_id: The ID of the user.
    :param database_id: The ID of the database.
    :return: True if the user has access, False otherwise.
    """
    user = session.query(User).filter_by(id=user_id).first()

    if not user:
        return False

    # Assuming you have a many-to-many relationship between User and Database models
    # Replace 'user_databases' with the appropriate attribute name from your User model
    accessible_databases = [db.id for db in user.user_databases]

    return database_id in accessible_databases


@socketio.on("stop")
def handle_stop(conversation_id):
    print("Received stop signal for conversation_id", conversation_id)
    # Stop the query
    with stop_flag_lock:
        if conversation_id in conversation_stop_flags:
            conversation_stop_flags[conversation_id] = True
            emit_status(conversation_id, STATUS.TO_STOP)

        else:
            print(
                f"No active 'ask' process found for conversation_id {conversation_id}"
            )


@socketio.on("ask")
@handle_stop_flag
def handle_ask(question, conversation_id=None, database_id=None):
    iterator = DatabaseChat(database_id, conversation_id, conversation_stop_flags).ask(
        question
    )
    for message in iterator:
        message = format_to_camel_case(**message)
        emit("response", message)


@socketio.on("regenerate")
@handle_stop_flag
def handle_regenerate(_, conversation_id=None, database_id=None):
    # get conversation_id from the database
    # conversation = session.query(Conversation).filter_by(id=conversation_id).first()
    iterator = DatabaseChat(
        database_id, conversation_id, conversation_stop_flags
    ).regenerate_last_message()
    for message in iterator:
        message = format_to_camel_case(**message)
        emit("response", message)
