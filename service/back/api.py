import json
import logging
import os
from typing import Any, cast
from uuid import UUID

import anthropic
from autochat import Autochat
from flask import Blueprint, g, jsonify, request
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import true

import telemetry
from back.data_warehouse import ConnectionError, DataWarehouseFactory
from back.utils import (
    apply_privacy_patterns_to_metadata,
    create_database,
    merge_tables_metadata,
)
from chat.proxy_provider import ProxyProvider
from middleware import admin_required, user_middleware
from models import (
    Chart,
    Conversation,
    ConversationMessage,
    Database,
    Project,
    ProjectTables,
    Query,
    UserFavorite,
)
from models.quality import BusinessEntity, Issue

logger = logging.getLogger(__name__)
api = Blueprint("back_api", __name__)

AUTOCHAT_PROVIDER = os.getenv("AUTOCHAT_PROVIDER", "proxy")


def extract_context(session: Session, context_id: str) -> tuple[UUID, UUID | None]:
    """
    Extract the databaseId from the context_id
    context is "project-{projectId}" or "database-{databaseId}"
    """
    if context_id.startswith("project-"):
        project_id = context_id.removeprefix("project-")
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            raise ValueError(f"Project with id {project_id} not found")
        return project.databaseId, project.id
    elif context_id.startswith("database-"):
        database_id = context_id.removeprefix("database-")
        return UUID(database_id), None
    else:
        raise ValueError(f"Invalid context_id: {context_id}")


@api.route("/conversations", methods=["POST"])
@user_middleware
def create_conversation():
    if not request.json:
        return jsonify({"message": "No JSON data provided"}), 400
    context_id = request.json.get("contextId")
    if not context_id:
        return jsonify({"message": "contextId is required"}), 400
    database_id, project_id = extract_context(g.session, context_id)
    new_conversation = Conversation(
        databaseId=database_id,
        ownerId=g.user.id,
        projectId=project_id,
    )
    g.session.add(new_conversation)
    g.session.flush()
    return jsonify(new_conversation.to_dict())


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
            and_(
                Conversation.databaseId == database_id,
                Conversation.projectId == project_id,
            )
        )
    conversations = query.all()
    conversations_dict = [conversation.to_dict() for conversation in conversations]
    return jsonify(conversations_dict)


@api.route("/conversations/<uuid:conversation_id>", methods=["GET", "PUT"])
@user_middleware
def get_conversation(conversation_id: UUID):
    conversation = (
        g.session.query(Conversation)
        .join(ConversationMessage, Conversation.messages, isouter=True)
        .filter(Conversation.id == conversation_id)
        .one()
    )

    # Verify user owns this conversation or that it's in the same organisation
    user_owns_conversation = conversation.ownerId == g.user.id
    user_in_same_org = (
        g.organization_id is not None
        and conversation.database.organisationId == g.organization_id
    )

    if not (user_owns_conversation or user_in_same_org):
        return jsonify({"error": "Access denied"}), 403

    if request.method == "PUT":
        # Only allow updates if user owns the conversation
        if not user_owns_conversation:
            return jsonify({"error": "Cannot modify conversations you don't own"}), 403

        # Update conversation name
        conversation.name = request.json["name"]
        g.session.flush()

    # TODO: redesign this to use a single query
    conversation_dict = conversation.to_dict()
    conversation_dict["messages"] = [m.to_dict() for m in conversation.messages]
    conversation_dict["messages"].sort(key=lambda x: x["createdAt"])
    return jsonify(conversation_dict)


@api.route("/conversations/<uuid:conversation_id>", methods=["DELETE"])
@user_middleware
def delete_conversation(conversation_id: UUID):
    # Verify user owns this conversation before deletion
    conversation = g.session.query(Conversation).filter_by(id=conversation_id).first()
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    if conversation.ownerId != g.user.id:
        return jsonify({"error": "Access denied"}), 403

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
def create_database_route():
    data = request.get_json()

    try:
        # Instantiate a new data_warehouse object
        data_warehouse = DataWarehouseFactory.create(
            data["engine"],
            **data["details"],
        )
        data_warehouse.test_connection()
    except ConnectionError as e:
        return jsonify({"message": str(e.args[0])}), 400

    # Create a new database
    database = create_database(
        name=data["name"],
        description=data.get("description", ""),
        engine=data["engine"],
        details=data["details"],
        organisation_id=g.organisation.id if g.organisation else None,
        owner_id=g.user.id,
        public=False,
        write_mode=data["write_mode"],
        dbt_catalog=data["dbt_catalog"],
        dbt_manifest=data["dbt_manifest"],
    )

    g.session.add(database)
    g.session.flush()

    return jsonify(database.to_dict())


@api.route("/databases/test-connection", methods=["POST"])
@user_middleware
def test_database_connection():
    """Test database connection without creating the database."""
    data = request.get_json()

    try:
        # Instantiate a new data_warehouse object
        data_warehouse = DataWarehouseFactory.create(
            data["engine"],
            **data["details"],
        )
        data_warehouse.test_connection()
        return jsonify({"success": True, "message": "Connection successful"})
    except ConnectionError as e:
        return jsonify({"success": False, "message": str(e)}), 400


@api.route("/databases/<uuid:database_id>", methods=["DELETE"])
@user_middleware
@admin_required
def delete_database(database_id: UUID):
    # Delete database
    database = (
        g.session.query(Database)
        .filter_by(id=database_id, ownerId=g.user.id)
        .filter(
            or_(
                Database.organisationId == g.organization_id,
                Database.ownerId == g.user.id,
            )
        )
        .first()
    )
    if not database:
        return jsonify({"error": "Database not found"}), 404

    g.session.delete(database)
    g.session.flush()
    return jsonify({"success": True})


@api.route("/databases/<uuid:database_id>", methods=["PUT"])
@user_middleware
def update_database(database_id: UUID):
    data = request.get_json()

    # Update database
    database = g.session.query(Database).filter_by(id=database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    # Verify user has access to update this database
    if database.ownerId != g.user.id and database.organisationId != g.organization_id:
        return jsonify({"error": "Access denied"}), 403

    database.name = data["name"]
    database.description = data["description"]
    if g.organization_id:
        database.organisationId = g.organization_id

    try:
        # If the engine info has changed, we need to check the connection
        data_warehouse = DataWarehouseFactory.create(
            data["engine"],
            **data["details"],
        )
        if database.engine != data["engine"] or database.details != data["details"]:
            data_warehouse.test_connection()
    except ConnectionError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    new_meta = data_warehouse.load_metadata()
    merged_metadata = cast(
        Any, merge_tables_metadata(database.tables_metadata, new_meta)
    )  # type: ignore[attr-defined]
    database.tables_metadata = merged_metadata
    database.engine = data["engine"]
    database.details = data["details"]
    database.write_mode = data["write_mode"]
    database.dbt_catalog = data["dbt_catalog"]
    database.dbt_manifest = data["dbt_manifest"]

    # Persist the updated metadata (re-assign to mark field as modified)
    database.tables_metadata = database.tables_metadata  # type: ignore[attr-defined]
    g.session.flush()

    return jsonify(database.to_dict())


@api.route("/databases", methods=["GET"])
@user_middleware
def get_databases():
    databases_query = (
        g.session.query(Database)
        .filter(
            or_(
                Database.organisationId == g.organization_id
                if g.organization_id is not None
                else False,
                Database.ownerId == g.user.id,
                Database.public == true(),
            )
        )
        .all()
    )
    # Convert each Database object to its dictionary representation
    databases_list = [db.to_dict() for db in databases_query]
    return jsonify(databases_list)


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

    if AUTOCHAT_PROVIDER == "proxy":
        provider = ProxyProvider
    else:
        provider = AUTOCHAT_PROVIDER

    questionAssistant = Autochat(
        provider=provider,
        context=json.dumps(context),
        use_tools_only=True,
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
    try:
        message = questionAssistant.ask(
            prompt,
        )
    except Exception as e:
        logger.error(f"Error asking question: {e}")
        if isinstance(e, anthropic.APIStatusError) and e.status_code == 402:
            return jsonify({"message": "SUBSCRIPTION_REQUIRED"}), 402
        return jsonify({"message": "Error asking question"}), 500

    response_dict = message.function_call["arguments"]
    response_values = list(response_dict.values())
    return jsonify(response_values)


@api.route("/databases/<uuid:database_id>/schema", methods=["GET"])
@user_middleware
def get_schema(database_id: UUID):
    # Filter databases based on user ID and specific database ID
    database = g.session.query(Database).filter_by(id=database_id).first()

    if not database:
        return jsonify({"error": "Database not found"}), 404

    # Verify user has access to this database
    if (
        database.ownerId != g.user.id
        and database.organisationId != g.organization_id
        and not database.public
    ):
        return jsonify({"error": "Access denied"}), 403

    return jsonify(database.tables_metadata)


@api.route("/server-info", methods=["GET"])
def get_server_info():
    """Get the server IP address to guide the user who needs to whitelist"""
    import requests

    response = requests.get("https://api.ipify.org", timeout=5)
    return jsonify({"ip": response.text.strip()})


@api.route("/version", methods=["GET"])
def get_version():
    """Get the application version and check for updates"""
    current_version = telemetry.get_current_version()
    latest_version = None

    # Check for latest version if we should (throttled)
    if telemetry.should_check_version():
        latest_version = telemetry.get_latest_version()
    else:
        # Use cached version if available
        latest_version = telemetry.get_cached_latest_version()

    has_update = latest_version and latest_version != current_version

    return jsonify(
        {
            "version": current_version,
            "latest": latest_version,
            "hasUpdate": has_update,
        }
    )


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
    projects_dict = [project.to_dict() for project in projects]
    return jsonify(projects_dict)


# Get specific project
@api.route("/projects/<uuid:project_id>", methods=["GET"])
@user_middleware
def get_project(project_id: UUID):
    project = (
        g.session.query(Project)
        # .join(ProjectTables, Project.tables, isouter=True)
        .filter_by(id=project_id)
        .first()
    )

    # # Verify user access
    if project.creatorId != g.user.id and project.organisationId != g.organization_id:
        return jsonify({"error": "Access denied"}), 403

    project_dict = project.to_dict()
    project_dict["tables"] = [table.to_dict() for table in project.tables]
    return jsonify(project_dict)


# Create, update, delete projects
@api.route("/projects", methods=["POST"])
@user_middleware
def create_project():
    data = request.get_json()
    required_fields = ["name", "description", "databaseId"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    new_project = Project(
        **{field: data[field] for field in required_fields if field != "databaseId"},
        databaseId=UUID(data["databaseId"]),
    )
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
    return jsonify(new_project.to_dict())


@api.route("/projects/<uuid:project_id>", methods=["PUT"])
@user_middleware
def update_project(project_id: UUID):
    data = request.get_json()
    project = g.session.query(Project).filter_by(id=project_id).first()
    if not project:
        return jsonify({"error": "Project not found"}), 404

    # Verify user has access to update this project
    if project.creatorId != g.user.id and project.organisationId != g.organization_id:
        return jsonify({"error": "Access denied"}), 403

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


@api.route("/projects/<uuid:project_id>", methods=["DELETE"])
@user_middleware
def delete_project(project_id: UUID):
    project = g.session.query(Project).filter_by(id=project_id).first()
    if not project:
        return jsonify({"error": "Project not found"}), 404

    # Verify user has access to delete this project
    if project.creatorId != g.user.id and project.organisationId != g.organization_id:
        return jsonify({"error": "Access denied"}), 403

    g.session.delete(project)
    g.session.flush()
    return jsonify({"message": "Project deleted successfully"})


@api.route("/databases/<uuid:database_id>/privacy", methods=["PUT"])
@user_middleware
def update_database_privacy(database_id: UUID):
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


@api.route("/query/<uuid:query_id>/favorite", methods=["POST"])
@user_middleware
def toggle_query_favorite(query_id: UUID):
    """Toggle favorite status for a query for the current user"""
    query = g.session.query(Query).filter(Query.id == query_id).first()
    if not query:
        return jsonify({"error": "Query not found"}), 404

    # Verify user has access to the query's database
    database = g.session.query(Database).filter_by(id=query.databaseId).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    if (
        database.ownerId != g.user.id
        and database.organisationId != g.organization_id
        and not database.public
    ):
        return jsonify({"error": "Access denied"}), 403

    favorite = (
        g.session.query(UserFavorite)
        .filter(UserFavorite.user_id == g.user.id, UserFavorite.query_id == query_id)
        .first()
    )

    if favorite:
        g.session.delete(favorite)
        g.session.flush()
        is_favorite = False
    else:
        favorite = UserFavorite(user_id=g.user.id, query_id=query_id)
        g.session.add(favorite)
        g.session.flush()
        is_favorite = True

    return jsonify({"success": True, "is_favorite": is_favorite})


@api.route("/chart/<uuid:chart_id>", methods=["GET"])
@user_middleware
def get_chart(chart_id: UUID):
    chart = g.session.query(Chart).filter(Chart.id == chart_id).first()
    if not chart:
        return jsonify({"error": "Chart not found"}), 404

    # Verify user has access to this chart
    if (
        chart.query.database.ownerId != g.user.id
        and chart.query.database.organisationId != g.organization_id
        and not chart.query.database.public
    ):
        return jsonify({"error": "Access denied"}), 403

    chart_dict = chart.to_dict()
    # Add is_favorite to chart
    chart_dict["is_favorite"] = (
        g.session.query(UserFavorite)
        .filter(UserFavorite.user_id == g.user.id, UserFavorite.chart_id == chart_id)
        .first()
        is not None
    )

    return jsonify(chart_dict)


@api.route("/chart/<uuid:chart_id>/favorite", methods=["POST"])
@user_middleware
def toggle_chart_favorite(chart_id: UUID):
    """Toggle favorite status for a chart for the current user"""
    chart = g.session.query(Chart).filter(Chart.id == chart_id).first()
    if not chart:
        return jsonify({"error": "Chart not found"}), 404

    # Verify user has access to the chart's database via query relationship
    if (
        chart.query.database.ownerId != g.user.id
        and chart.query.database.organisationId != g.organization_id
        and not chart.query.database.public
    ):
        return jsonify({"error": "Access denied"}), 403

    favorite = (
        g.session.query(UserFavorite)
        .filter(UserFavorite.user_id == g.user.id, UserFavorite.chart_id == chart_id)
        .first()
    )

    if favorite:
        g.session.delete(favorite)
        g.session.flush()
        is_favorite = False
    else:
        favorite = UserFavorite(user_id=g.user.id, chart_id=chart_id)
        g.session.add(favorite)
        g.session.flush()
        is_favorite = True

    return jsonify({"success": True, "is_favorite": is_favorite})


@api.route("/favorites", methods=["GET"])
@user_middleware
def get_favorites():
    context_id = request.args.get("contextId")
    database_id, _ = extract_context(g.session, context_id)
    """Get all favorited queries and charts for the current user"""
    query_favorites = (
        g.session.query(Query)
        .join(UserFavorite, UserFavorite.query_id == Query.id)
        .filter(
            UserFavorite.user_id == g.user.id,
            Query.rows.isnot(None),
            Query.exception.is_(None),
            Query.databaseId == database_id,
        )
        .all()
    )

    chart_favorites = (
        g.session.query(Chart)
        .join(UserFavorite, UserFavorite.chart_id == Chart.id)
        .join(Query, Query.id == Chart.queryId)
        .filter(UserFavorite.user_id == g.user.id, Query.databaseId == database_id)
        .all()
    )
    queries = [query.to_dict() for query in query_favorites]
    charts = [chart.to_dict() for chart in chart_favorites]
    return jsonify({"queries": queries, "charts": charts})


@api.route("/databases/<uuid:database_id>/privacy/auto", methods=["POST"])
@user_middleware
def auto_update_database_privacy(database_id: UUID):
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
    apply_privacy_patterns_to_metadata(database.tables_metadata)

    # Persist the updated metadata (re-assign to mark field as modified)
    database.tables_metadata = database.tables_metadata  # type: ignore[attr-defined]
    g.session.flush()

    return jsonify({"success": True, "tables_metadata": database.tables_metadata})


@api.route("/business-entities", methods=["GET"])
@user_middleware
def get_business_entities():
    context_id = request.args.get("contextId")
    database_id, project_id = extract_context(g.session, context_id)

    # Verify user has access to the database through organization or ownership
    database = g.session.query(Database).filter_by(id=database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    if (
        database.ownerId != g.user.id
        and database.organisationId != g.organization_id
        and not database.public
    ):
        return jsonify({"error": "Access denied"}), 403

    # Query business entities with proper database access validation
    query = (
        g.session.query(BusinessEntity)
        .join(Database, BusinessEntity.database_id == Database.id)
        .filter(
            BusinessEntity.database_id == database_id,
            or_(
                Database.organisationId == g.organization_id
                if g.organization_id is not None
                else False,
                Database.ownerId == g.user.id,
                Database.public == true(),
            ),
        )
    )

    if project_id:
        # Additional filter for project-specific entities if needed
        # Note: BusinessEntity model doesn't have project_id field based on the schema
        # This filter may need to be adjusted based on actual relationships
        pass

    business_entities = query.all()
    return jsonify(business_entities)


@api.route("/issues", methods=["GET"])
@user_middleware
def get_issues():
    context_id = request.args.get("contextId")
    database_id, _ = extract_context(g.session, context_id)

    # Verify user has access to the database through organization or ownership
    database = g.session.query(Database).filter_by(id=database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    if (
        database.ownerId != g.user.id
        and database.organisationId != g.organization_id
        and not database.public
    ):
        return jsonify({"error": "Access denied"}), 403

    # Query issues with proper database access validation
    query = (
        g.session.query(Issue)
        .join(Database, Issue.database_id == Database.id)
        .filter(
            Issue.database_id == database_id,
            or_(
                Database.organisationId == g.organization_id
                if g.organization_id is not None
                else False,
                Database.ownerId == g.user.id,
                Database.public == true(),
            ),
        )
    )

    issues = query.all()
    return jsonify(issues)
