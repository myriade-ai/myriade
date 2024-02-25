from back.datalake import DatalakeFactory
from back.models import Conversation, ConversationMessage, Database
from flask import Blueprint, g, jsonify, request
from middleware import user_middleware
from sqlalchemy import and_, or_

api = Blueprint("back_api", __name__)

import dataclasses
from datetime import datetime
from typing import List, Union


def dataclass_to_dict(obj: Union[object, List[object]]) -> Union[dict, List[dict]]:
    if isinstance(obj, list):
        return [dataclass_to_dict(item) for item in obj]

    if dataclasses.is_dataclass(obj):
        data = {}
        for field in dataclasses.fields(obj):
            value = getattr(obj, field.name)
            if isinstance(value, datetime):
                data[field.name] = value.isoformat()
            elif dataclasses.is_dataclass(value) or isinstance(value, list):
                data[field.name] = dataclass_to_dict(value)
            else:
                data[field.name] = value
        return data

    return obj


@api.route("/conversations", methods=["GET"])
@user_middleware
def get_conversations():
    # Filter conversations based on ownerId (userId) OR organisationId
    conversations = (
        g.session.query(Conversation)
        .filter(
            Conversation.ownerId == g.user.id,
        )
        .all()
    )
    return jsonify(conversations)


@api.route("/conversations/<int:conversation_id>", methods=["GET", "PUT"])
@user_middleware
def get_conversation(conversation_id):
    conversation = (
        g.session.query(Conversation)
        .join(ConversationMessage, Conversation.messages, isouter=True)
        .filter(Conversation.id == conversation_id)
        .one()
    )

    if request.method == "PUT":
        # Update conversation name
        conversation.name = request.json["name"]
        g.session.commit()

    # TODO: redesign this to use a single query
    conversation_dict = dataclass_to_dict(conversation)
    conversation_dict["messages"] = dataclass_to_dict(conversation.messages)
    conversation_dict["messages"].sort(key=lambda x: x["id"])
    return jsonify(conversation_dict)


@api.route("/conversations/<int:conversation_id>", methods=["DELETE"])
@user_middleware
def delete_conversation(conversation_id):
    # Delete conversation and all related messages
    g.session.query(ConversationMessage).filter_by(
        conversationId=conversation_id
    ).delete()
    g.session.query(Conversation).filter_by(id=conversation_id).delete()
    g.session.commit()
    return jsonify({"success": True})


@api.route("/databases", methods=["POST"])
@user_middleware
def create_database():
    # Instaniate a new datalake object
    datalake = DatalakeFactory.create(
        request.json["engine"],
        **request.json["details"],
    )
    # Test connection
    datalake.test_connection()

    # Create a new database
    database = Database(
        name=request.json["name"],
        description=request.json["description"],
        _engine=request.json["engine"],
        details=request.json["details"],
        # organisationId=request.json["organisationId"],
        ownerId=g.user.id,
        privacy_mode=request.json["privacy_mode"],
        safe_mode=request.json["safe_mode"],
    )

    database.tables_metadata = datalake.load_metadata()

    g.session.add(database)
    g.session.commit()
    return jsonify(database)


@api.route("/databases/<int:database_id>", methods=["DELETE"])
@user_middleware
def delete_database(database_id):
    # Delete database
    g.session.query(Database).filter_by(id=database_id).delete()
    g.session.commit()
    return jsonify({"success": True})


@api.route("/databases/<int:database_id>", methods=["PUT"])
@user_middleware
def update_database(database_id):
    # Update database
    database = g.session.query(Database).filter_by(id=database_id).first()
    database.name = request.json["name"]
    database.description = request.json["description"]

    # If the engine info has changed, we need to check the connection
    datalake = DatalakeFactory.create(
        request.json["engine"],
        **request.json["details"],
    )
    if (
        database.engine != request.json["engine"]
        or database.details != request.json["details"]
        or database.name != request.json["name"]
    ):
        try:
            datalake.test_connection()
        except Exception as e:
            return jsonify({"message": str(e.args[0])}), 400

    database.tables_metadata = datalake.load_metadata()
    database._engine = request.json["engine"]
    database.details = request.json["details"]
    database.privacy_mode = request.json["privacy_mode"]
    database.safe_mode = request.json["safe_mode"]

    g.session.commit()
    return jsonify(database)


@api.route("/databases", methods=["GET"])
@user_middleware
def get_databases():
    user = getattr(g, "user", None)
    # organisationId = g.organisationId
    # Filter databases based on ownerId (userId) OR organisationId
    databases = (
        g.session.query(Database)
        .filter(Database.ownerId == user.id)
        # .filter(
        #     or_(
        #
        #         Database.organisationId == organisationId
        #     )
        # )
        .all()
    )
    return jsonify(databases)


@api.route("/databases/<int:database_id>/schema", methods=["GET"])
def get_schema(database_id):
    # Filter databases based on user ID and specific database ID
    database = g.session.query(Database).filter_by(id=database_id).first()

    if not database:
        return jsonify({"error": "Database not found"}), 404

    return jsonify(database.tables_metadata)
