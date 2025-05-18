import dataclasses
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast
from uuid import UUID

from flask import Blueprint, g, jsonify, request
from sqlalchemy import or_

from back.datalake import ConnectionError, DatalakeFactory
from back.privacy import PRIVACY_PATTERNS
from chat.api import extract_context
from middleware import admin_required, user_middleware
from models import Conversation, ConversationMessage, Database, Project, ProjectTables
from models.quality import BusinessEntity, Issue

api = Blueprint("back_api", __name__)

AUTOCHAT_PROVIDER = os.getenv("AUTOCHAT_PROVIDER", "openai")


def dataclass_to_dict(obj: Union[object, List[object]]) -> Union[dict, List[dict]]:
    if isinstance(obj, list):
        return [dataclass_to_dict(item) for item in obj]

    if dataclasses.is_dataclass(obj):
        data = {}
        for field in dataclasses.fields(obj):
            value = getattr(obj, field.name)
            if isinstance(value, datetime):
                data[field.name] = value.isoformat()
            elif isinstance(value, UUID):
                data[field.name] = str(value)
            elif dataclasses.is_dataclass(value) or isinstance(value, list):
                data[field.name] = dataclass_to_dict(value)
            else:
                data[field.name] = value
        return data

    return obj


@api.route("/conversations", methods=["GET"])
@user_middleware
def get_conversations():
    context_id = request.args.get("contextId")
    query = g.session.query(Conversation).filter(
        Conversation.ownerId == g.user.id,
    )
    if context_id:
        database_id, project_id = extract_context(g.session, context_id)
        query = query.filter(
            or_(
                Conversation.databaseId == database_id,
                Conversation.projectId == project_id,
            )
        )
    conversations = query.all()
    conversations_dict = [
        dataclass_to_dict(conversation) for conversation in conversations
    ]
    return jsonify(conversations_dict)


@api.route("/conversations/<conversation_id>", methods=["GET", "PUT"])
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
        g.session.flush()

    # TODO: redesign this to use a single query
    conversation_dict = dataclass_to_dict(conversation)
    conversation_dict["messages"] = [
        m.to_dict(g.session) for m in conversation.messages
    ]
    conversation_dict["messages"].sort(key=lambda x: x["createdAt"])
    return jsonify(conversation_dict)


@api.route("/conversations/<conversation_id>", methods=["DELETE"])
@user_middleware
def delete_conversation(conversation_id):
    # Delete conversation and all related messages
    g.session.query(ConversationMessage).filter_by(
        conversationId=conversation_id
    ).delete()
    g.session.query(Conversation).filter_by(id=conversation_id).delete()
    g.session.flush()
    return jsonify({"success": True})


@api.route("/databases", methods=["POST"])
@user_middleware
@admin_required
def create_database():
    data = request.get_json()

    try:
        # Instantiate a new datalake object
        datalake = DatalakeFactory.create(
            data["engine"],
            **data["details"],
        )
        datalake.test_connection()
    except ConnectionError as e:
        return jsonify({"message": str(e.args[0])}), 400

    # Create a new database
    database = Database(
        name=data["name"],
        description=data["description"],
        _engine=data["engine"],
        details=data["details"],
        organisationId=g.organisation.id,
        ownerId=g.user.id,
        safe_mode=data["safe_mode"],
        dbt_catalog=data["dbt_catalog"],
        dbt_manifest=data["dbt_manifest"],
    )

    updated_tables_metadata = datalake.load_metadata()
    # Merge with none (fresh create); adds empty privacy maps, then auto privacy scan
    merged_metadata = cast(Any, _merge_tables_metadata(None, updated_tables_metadata))  # type: ignore[attr-defined]
    database.tables_metadata = cast(  # type: ignore[attr-defined]
        Any, _apply_privacy_patterns_to_metadata(merged_metadata)
    )

    g.session.add(database)
    g.session.flush()

    return jsonify(database)


@api.route("/databases/<database_id>", methods=["DELETE"])
@user_middleware
@admin_required
def delete_database(database_id):
    # Delete database
    g.session.query(Database).filter_by(id=database_id).delete()
    g.session.flush()
    return jsonify({"success": True})


@api.route("/databases/<database_id>", methods=["PUT"])
@user_middleware
def update_database(database_id):
    data = request.get_json()

    # Update database
    database = g.session.query(Database).filter_by(id=database_id).first()
    database.name = data["name"]
    database.description = data["description"]
    database.organisationId = g.organization_id

    # If the engine info has changed, we need to check the connection
    datalake = DatalakeFactory.create(
        data["engine"],
        **data["details"],
    )
    if (
        database.engine != data["engine"]
        or database.details != data["details"]
        or database.name != data["name"]
    ):
        try:
            datalake.test_connection()
        except Exception as e:
            return jsonify({"message": str(e)}), 400

    new_meta = datalake.load_metadata()
    merged_metadata = cast(
        Any, _merge_tables_metadata(database.tables_metadata, new_meta)
    )  # type: ignore[attr-defined]
    database.tables_metadata = cast(  # type: ignore[attr-defined]
        Any, _apply_privacy_patterns_to_metadata(merged_metadata)
    )
    database._engine = data["engine"]
    database.details = data["details"]
    database.safe_mode = data["safe_mode"]
    database.dbt_catalog = data["dbt_catalog"]
    database.dbt_manifest = data["dbt_manifest"]

    # Persist the updated metadata (re-assign to mark field as modified)
    database.tables_metadata = database.tables_metadata  # type: ignore[attr-defined]
    g.session.flush()

    return jsonify(database)


@api.route("/databases", methods=["GET"])
@user_middleware
def get_databases():
    databases = (
        g.session.query(Database)
        .filter(
            or_(
                Database.organisationId == g.organization_id
                if g.organization_id is not None
                else False,
                Database.ownerId == g.user.id,
            )
        )
        .all()
    )
    return jsonify(databases)


@api.route("/contexts/<string:context_id>/questions", methods=["GET"])
@user_middleware
def get_questions(context_id):
    # Get the preferred language from Accept-Language header
    user_language = request.headers.get("Accept-Language")

    # context is "project-{projectId}" or "database-{databaseId}"
    database_id, project_id = extract_context(g.session, context_id)
    database = g.session.query(Database).filter_by(id=database_id).first()

    # If project, filter database.tables_metadata with project.tables
    tables_metadata = database.tables_metadata

    if project_id:
        project = g.session.query(Project).filter_by(id=project_id).first()
        if not project:
            raise ValueError(f"Project with id {project_id} not found")
        tables_metadata = [
            # if any (name match tableName and schema match schemaName)
            # in project.tables
            table_metadata
            for table_metadata in tables_metadata
            if any(
                table_metadata["name"] == project_table.tableName
                and table_metadata["schema"] == project_table.schemaName
                for project_table in project.tables
            )
        ]
        context = (
            "# Project Name: "
            + project.name
            + "\n# Database Name: "
            + database.name
            + "\n# Database Description: "
            + database.description
            + "\n# Tables: "
            + str(tables_metadata)
        )
    else:
        context = (
            "# Name: "
            + database.name
            + "\n# Description: "
            + database.description
            + "\n# Tables: "
            + str(tables_metadata)
        )

    from autochat import Autochat

    questionAssistant = Autochat(
        provider=AUTOCHAT_PROVIDER, context=json.dumps(context)
    )
    # TODO: if exist ; add database.memory, dbt.catalog, dbt.manifest

    def questions(question1: str, question2: str, question3: str):
        pass

    questionAssistant.add_function(questions)

    prompt = (
        "Generate 3 business questions about different topics that the user "
        + "can ask based on the context (database schema, past conversations, etc)"
        + f"\nDo it in the user preferred language (Accept-Language: {user_language})"
    )
    message = questionAssistant.ask(
        prompt,
        tool_choice={"type": "tool", "name": "questions"},  # anthropic specific
    )
    response_dict = message.function_call["arguments"]
    response_values = list(response_dict.values())
    return jsonify(response_values)


@api.route("/databases/<database_id>/schema", methods=["GET"])
@user_middleware
def get_schema(database_id):
    # Filter databases based on user ID and specific database ID
    database = g.session.query(Database).filter_by(id=database_id).first()

    if not database:
        return jsonify({"error": "Database not found"}), 404

    return jsonify(database.tables_metadata)


@api.route("/server-info", methods=["GET"])
def get_server_info():
    """Get the server IP address to guide the user who needs to whitelist"""
    import requests

    response = requests.get("https://api.ipify.org", timeout=5)
    return jsonify({"ip": response.text.strip()})


@api.route("/version", methods=["GET"])
def get_version():
    """Get the application version"""
    try:
        # Read version directly from pyproject.toml
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"

        # Simple parsing to extract the version
        with open(pyproject_path, "r") as f:
            for line in f:
                if line.strip().startswith("version = "):
                    # Extract version from the line (format: version = "0.1.0")
                    version = line.strip().split("=")[1].strip().strip('"')
                    return jsonify({"version": version})

        # If version not found in the file
        return jsonify({"error": "Version information not available"}), 500
    except Exception as e:
        # Return error if version information is not available
        return jsonify({"error": f"Version information not available: {str(e)}"}), 500


# Get all projects of the user or it's organisation
@api.route("/projects", methods=["GET"])
@user_middleware
def get_projects():
    projects = (
        g.session.query(Project)
        .filter(
            or_(
                Project.creatorId == g.user.id,
                Project.organisationId == g.organization_id
                if g.organization_id is not None
                else False,
            )
        )
        .all()
    )

    return jsonify(projects)


# Get specific project
@api.route("/projects/<project_id>", methods=["GET"])
@user_middleware
def get_project(project_id):
    project = (
        g.session.query(Project)
        # .join(ProjectTables, Project.tables, isouter=True)
        .filter_by(id=project_id)
        .first()
    )

    # # Verify user access
    if project.creatorId != g.user.id and project.organisationId != g.organization_id:
        return jsonify({"error": "Access denied"}), 403

    project_dict = dataclass_to_dict(project)
    project_dict["tables"] = dataclass_to_dict(project.tables)
    return jsonify(project_dict)


# Create, update, delete projects
@api.route("/projects", methods=["POST"])
@user_middleware
def create_project():
    data = request.get_json()
    required_fields = ["name", "description", "databaseId"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    new_project = Project(**{field: data[field] for field in required_fields})
    new_project.creatorId = g.user.id
    new_project.organisationId = g.organization_id

    # Handle creation of ProjectTables
    if "tables" in data:
        new_project.tables = [
            ProjectTables(
                databaseName=table.get("databaseName"),
                schemaName=table.get("schemaName"),
                tableName=table.get("tableName"),
            )
            for table in data["tables"]
        ]

    g.session.add(new_project)
    g.session.flush()
    return jsonify(new_project)


@api.route("/projects/<project_id>", methods=["PUT"])
@user_middleware
def update_project(project_id):
    data = request.get_json()
    project = g.session.query(Project).filter_by(id=project_id).first()
    # update name, description or tables
    project.name = data.get("name")
    project.organisationId = g.organization_id
    project.description = data.get("description")
    project.databaseId = data.get("databaseId")
    project.tables = [
        ProjectTables(
            projectId=project_id,
            databaseName=table.get("databaseName"),
            schemaName=table.get("schemaName"),
            tableName=table.get("tableName"),
        )
        for table in data.get("tables", [])
    ]
    g.session.flush()
    return "ok"


@api.route("/projects/<project_id>", methods=["DELETE"])
@user_middleware
def delete_project(project_id):
    project = g.session.query(Project).filter_by(id=project_id).first()
    g.session.delete(project)
    g.session.flush()
    return jsonify({"message": "Project deleted successfully"})


@api.route("/databases/<database_id>/privacy", methods=["PUT"])
@user_middleware
def update_database_privacy(database_id):
    """Update privacy configuration (tables_metadata) for a database."""
    database = g.session.query(Database).filter_by(id=database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    # Verify user has access (owner or organisation match)
    if database.ownerId != g.user.id and database.organisationId != g.organization_id:
        return jsonify({"error": "Access denied"}), 403

    payload = request.get_json()
    if not isinstance(payload, list):
        return jsonify({"error": "Invalid payload"}), 400

    # Persist the whole tables_metadata JSON (list of tables with columns + privacy)
    database.tables_metadata = payload
    g.session.flush()

    return jsonify({"success": True})


@api.route("/databases/<database_id>/privacy/auto", methods=["POST"])
@user_middleware
def auto_update_database_privacy(database_id):
    """Auto-detect sensitive columns based on PRIVACY_PATTERNS and update privacy maps.

    For every column whose name matches one of the regexes defined in
    PRIVACY_PATTERNS and that currently has *no* specific LLM privacy setting
    (or is marked as Visible/Default), set the LLM provider privacy to
    "Encrypted". The updated `tables_metadata` JSON structure is then
    persisted back to the database row.
    """

    database = g.session.query(Database).filter_by(id=database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    # Verify user has access (owner or organisation match)
    if database.ownerId != g.user.id and database.organisationId != g.organization_id:
        return jsonify({"error": "Access denied"}), 403

    if not database.tables_metadata:
        return jsonify({"error": "No metadata found for this database"}), 400

    # Apply the same logic used at creation/update time
    _apply_privacy_patterns_to_metadata(database.tables_metadata)

    # Persist the updated metadata (re-assign to mark field as modified)
    database.tables_metadata = database.tables_metadata  # type: ignore[attr-defined]
    g.session.flush()

    return jsonify({"success": True, "tables_metadata": database.tables_metadata})


# Helper to merge existing privacy settings with freshly fetched metadata


def _merge_tables_metadata(
    existing: Optional[List[Dict[str, Any]]], new: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Return `new` tables list enriched with privacy maps from `existing`.

    If a table/column already has a privacy map in `existing`, keep it.
    Tables not present in the datalake anymore are discarded.
    """

    existing_lookup = {}
    if existing:
        for t in existing:
            existing_lookup[(t.get("schema"), t["name"])] = t

    merged: List[Dict[str, Any]] = []
    for t in new:
        key = (t.get("schema"), t["name"])
        previous = existing_lookup.get(key)
        # Build columns preserving privacy if available
        merged_columns: List[Dict[str, Any]] = []
        for col in t["columns"]:
            # find same column in previous
            prev_col_priv = {}
            if previous:
                for pc in previous.get("columns", []):
                    if pc["name"] == col["name"]:
                        prev_col_priv = pc.get("privacy", {})
                        break
            merged_columns.append(
                {
                    **col,
                    "privacy": prev_col_priv.copy(),
                }
            )
        merged.append({**t, "columns": merged_columns})

    return merged


def _apply_privacy_patterns_to_metadata(
    metadata: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Return the *same* list of tables with LLM privacy updated using PRIVACY_PATTERNS.

    For every column whose name matches one of the regexes in ``PRIVACY_PATTERNS`` and
    whose current LLM privacy is *not* one of ("Masked", "Redacted", "Encrypted"), we
    set it to ``Encrypted``.

    The function mutates the provided ``metadata`` list in place and also returns it
    for convenience so callers can do::

        database.tables_metadata = _apply_privacy_patterns_to_metadata(metadata)
    """

    for table in metadata:
        for column in table.get("columns", []):
            col_name: str = column.get("name", "")
            privacy_map: Dict[str, str] = column.get("privacy", {}) or {}

            llm_setting = privacy_map.get("llm")
            # Skip if already protected
            if llm_setting in {"Masked", "Redacted", "Encrypted"}:
                continue

            for pattern in PRIVACY_PATTERNS.values():
                try:
                    if re.search(pattern, col_name):
                        privacy_map["llm"] = "Encrypted"
                        column["privacy"] = privacy_map
                        # No need to test further patterns for this column
                        break
                except re.error:
                    # Malformed regex should never happen, but ignore if it does
                    continue

    return metadata


@api.route("/business-entities", methods=["GET"])
@user_middleware
def get_business_entities():
    context_id = request.args.get("contextId")
    query = g.session.query(BusinessEntity)

    database_id, project_id = extract_context(g.session, context_id)
    if project_id:
        query = query.filter(BusinessEntity.project_id == project_id)
    else:
        query = query.filter(BusinessEntity.database_id == database_id)

    business_entities = query.all()
    return jsonify(business_entities)


@api.route("/issues", methods=["GET"])
@user_middleware
def get_issues():
    query = g.session.query(Issue)
    context_id = request.args.get("contextId")

    database_id, _ = extract_context(g.session, context_id)
    query = query.filter(Issue.database_id == database_id)

    issues = query.all()
    return jsonify(issues)
