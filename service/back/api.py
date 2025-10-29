import json
import logging
import os
from uuid import UUID

import anthropic
from agentlys import Agentlys
from flask import Blueprint, g, jsonify, request
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, contains_eager, joinedload, selectinload
from sqlalchemy.sql.expression import true

import telemetry
from back.background_sync import run_metadata_sync_background
from back.catalog_events import (
    emit_asset_updated,
    emit_tag_deleted,
    emit_tag_updated,
)
from back.data_warehouse import ConnectionError, DataWarehouseFactory
from back.dbt_repository import (
    DBTRepositoryError,
    generate_dbt_docs,
    validate_dbt_repo,
)
from back.session import get_db_session
from back.utils import (
    create_database,
    get_provider_metadata_for_asset,
    get_tables_metadata_from_catalog,
    update_catalog_privacy,
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
from models.catalog import Asset, AssetTag, ColumnFacet, TableFacet, Term
from models.quality import BusinessEntity, Issue

logger = logging.getLogger(__name__)
api = Blueprint("back_api", __name__)

AGENTLYS_PROVIDER = os.getenv("AGENTLYS_PROVIDER", "proxy")


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
    conversation_dict["messages"] = [
        m.to_dict_with_linked_models(g.session) for m in conversation.messages
    ]
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
    """Create a new database and sync its metadata to the catalog."""
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
        dbt_catalog=data.get("dbt_catalog"),
        dbt_manifest=data.get("dbt_manifest"),
        dbt_repo_path=data.get("dbt_repo_path"),
    )

    g.session.add(database)
    g.session.flush()

    # IMPORTANT: Commit the database before starting background thread
    # The background thread needs to be able to query the database record
    g.session.commit()

    # Start background sync for initial metadata load
    run_metadata_sync_background(
        database_id=database.id,
        session_factory=get_db_session,
    )

    # Return immediately - metadata sync runs in background
    database_dict = database.to_dict(exclude=["dbt_catalog", "dbt_manifest"])
    database_dict["sync_status"] = "syncing"
    database_dict["sync_progress"] = 0
    return jsonify(database_dict)


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
    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
    ):
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

    # Update database fields
    database.engine = data["engine"]
    database.details = data["details"]
    database.write_mode = data["write_mode"]
    database.dbt_catalog = data.get("dbt_catalog")
    database.dbt_manifest = data.get("dbt_manifest")
    database.dbt_repo_path = data.get("dbt_repo_path")

    g.session.flush()

    # IMPORTANT: Commit the database before starting background thread
    # The background thread needs to be able to query the database record
    g.session.commit()

    run_metadata_sync_background(
        database_id=database.id,
        session_factory=get_db_session,
    )

    # Return immediately - metadata sync runs in background
    database_dict = database.to_dict(exclude=["dbt_catalog", "dbt_manifest"])
    database_dict["sync_status"] = "syncing"
    database_dict["sync_progress"] = 0
    return jsonify(database_dict)


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
    # Exclude large dbt fields that aren't needed in the list view
    databases_list = [
        db.to_dict(exclude=["dbt_catalog", "dbt_manifest"]) for db in databases_query
    ]
    return jsonify(databases_list)


@api.route("/contexts/<string:context_id>/questions", methods=["GET"])
@user_middleware
def get_questions(context_id):
    """Get the preferred language: organization language
    takes precedence over user language
    """
    user_language = (
        g.organisation.language
        if g.organisation and g.organisation.language
        else request.headers.get("Accept-Language")
    )

    # context is "project-{projectId}" or "database-{databaseId}"
    database_id, project_id = extract_context(g.session, context_id)
    database = g.session.query(Database).filter_by(id=database_id).first()

    tables_metadata = get_tables_metadata_from_catalog(database.id)

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

    if AGENTLYS_PROVIDER == "proxy":
        provider = ProxyProvider
    else:
        provider = AGENTLYS_PROVIDER

    questionAssistant = Agentlys(
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
    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
        or database.public
    ):
        return jsonify({"error": "Access denied"}), 403

    return jsonify(get_tables_metadata_from_catalog(database.id))


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
    if not (
        project.creatorId == g.user.id
        or (
            project.organisationId is not None
            and project.organisationId == g.organization_id
        )
    ):
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
    if not (
        project.creatorId == g.user.id
        or (
            project.organisationId is not None
            and project.organisationId == g.organization_id
        )
    ):
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
    if not (
        project.creatorId == g.user.id
        or (
            project.organisationId is not None
            and project.organisationId == g.organization_id
        )
    ):
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
    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
    ):
        return jsonify({"error": "Access denied"}), 403

    payload = request.get_json()
    if not isinstance(payload, list):
        return jsonify({"error": "Invalid payload"}), 400

    # Update privacy configuration in catalog
    update_catalog_privacy(database.id, payload)
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

    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
        or database.public
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
    if not (
        chart.query.database.ownerId == g.user.id
        or (
            chart.query.database.organisationId is not None
            and chart.query.database.organisationId == g.organization_id
        )
        or chart.query.database.public
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
    if not (
        chart.query.database.ownerId == g.user.id
        or (
            chart.query.database.organisationId is not None
            and chart.query.database.organisationId == g.organization_id
        )
        or chart.query.database.public
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
    # print each query as dict
    print(
        "🚀 ~ file: api.py:407 ~ get_favorites ~ query_favorites:",
        [q.to_dict() for q in query_favorites],
    )

    # Include rows and count for favorite queries since they're needed in the UI
    queries = []
    for query in query_favorites:
        query_dict = query.to_dict()
        query_dict["rows"] = query.rows
        query_dict["count"] = query.count
        queries.append(query_dict)

    charts = [chart.to_dict() for chart in chart_favorites]
    return jsonify({"queries": queries, "charts": charts})


# Catalog API routes
@api.route("/catalogs/<string:context_id>/assets", methods=["GET"])
@user_middleware
def get_catalog_assets(context_id):
    """Get all catalog assets for a context"""

    database_id, _ = extract_context(g.session, context_id)
    database = g.session.query(Database).filter_by(id=database_id).first()

    if not database:
        return jsonify({"error": "Database not found"}), 404

    # Verify user has access
    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
        or database.public
    ):
        return jsonify({"error": "Access denied"}), 403

    # Build query to fetch all assets with both facets
    # Use selectinload for parent_table_asset to avoid N+1 queries on columns
    query = (
        g.session.query(Asset)
        .filter(Asset.database_id == database_id)
        .outerjoin(Asset.table_facet)
        .outerjoin(Asset.column_facet)
        .options(
            contains_eager(Asset.table_facet),
            contains_eager(Asset.column_facet)
            .selectinload(ColumnFacet.parent_table_asset)
            .selectinload(Asset.table_facet),
            selectinload(Asset.asset_tags),
        )
        .order_by(
            Asset.type.desc(),
            TableFacet.schema,
            TableFacet.table_name,
            ColumnFacet.ordinal,
        )
    )

    assets = query.all()

    # Convert to dictionaries with facet data - optimized manual serialization
    result = []

    # Cache database_id string conversion (all assets have same database_id)
    database_id_str = str(database_id)

    # Manual serialization for better performance
    for asset in assets:
        asset_id_str = str(asset.id)

        # Manual serialization for better performance
        asset_dict = {
            "id": asset_id_str,
            "urn": asset.urn,
            "type": asset.type,
            "name": asset.name,
            "description": asset.description,
            "database_id": database_id_str,
            "status": asset.status,
            "ai_suggestion": asset.ai_suggestion,
            "ai_flag_reason": asset.ai_flag_reason,
            "ai_suggested_tags": asset.ai_suggested_tags,
        }

        # Serialize tags (pre-build to avoid repeated list construction)
        tags = asset.asset_tags
        if tags:
            asset_dict["tags"] = [
                {
                    "id": str(tag.id),
                    "name": tag.name,
                    "description": tag.description,
                    "database_id": database_id_str,
                }
                for tag in tags
            ]
        else:
            asset_dict["tags"] = []

        # Add facet-specific data - optimize by reducing attribute access
        asset_type = asset.type
        if asset_type == "TABLE":
            tf = asset.table_facet
            if tf:
                asset_dict["table_facet"] = {
                    "asset_id": asset_id_str,
                    "database_id": database_id_str,
                    "schema": tf.schema,
                    "table_name": tf.table_name,
                    "table_type": tf.table_type,
                }
        elif asset_type == "COLUMN":
            cf = asset.column_facet
            if cf:
                column_facet_dict = {
                    "asset_id": asset_id_str,
                    "parent_table_asset_id": str(cf.parent_table_asset_id),
                    "column_name": cf.column_name,
                    "ordinal": cf.ordinal,
                    "data_type": cf.data_type,
                    "privacy": cf.privacy,
                }

                # Include parent table information for columns
                pta = cf.parent_table_asset
                if pta:
                    ptf = pta.table_facet
                    if ptf:
                        column_facet_dict["parent_table_facet"] = {
                            "asset_id": str(ptf.asset_id),
                            "database_id": database_id_str,
                            "schema": ptf.schema,
                            "table_name": ptf.table_name,
                            "table_type": ptf.table_type,
                        }

                asset_dict["column_facet"] = column_facet_dict

        result.append(asset_dict)

    return jsonify(result)


@api.route("/catalogs/assets/<string:asset_id>", methods=["PATCH"])
@user_middleware
def update_catalog_asset(asset_id: str):
    """Update mutable fields of a catalog asset with validation workflow support."""

    try:
        asset_uuid = UUID(asset_id)
    except ValueError:
        return jsonify({"error": "Invalid asset id"}), 400

    asset = g.session.query(Asset).filter(Asset.id == asset_uuid).first()

    if not asset:
        return jsonify({"error": "Asset not found"}), 404

    data = request.get_json(silent=True) or {}

    # Handle approval workflow actions
    if data.get("approve_suggestion"):
        # User approves AI suggestion - move ai_suggestion to description
        if asset.ai_suggestion:
            asset.description = asset.ai_suggestion
            asset.ai_suggestion = None
            asset.ai_flag_reason = None
            asset.status = "validated"

        # Process suggested tags: link existing tags only
        if asset.ai_suggested_tags:
            asset.asset_tags.clear()
            for tag_name in asset.ai_suggested_tags:  # Now simple strings
                if not tag_name:
                    continue

                # Check if tag exists (case-insensitive)
                tag = (
                    g.session.query(AssetTag)
                    .filter(
                        AssetTag.database_id == asset.database_id,
                        AssetTag.name.ilike(tag_name),
                    )
                    .first()
                )

                # Only link if tag exists (defensive programming)
                if tag:
                    asset.asset_tags.append(tag)
                else:
                    logger.warning(
                        f"Suggested tag '{tag_name}' not found for asset {asset.id}"
                    )

            # Clear suggested tags after processing
            asset.ai_suggested_tags = None

    elif data.get("dismiss_flag"):
        # User dismisses the AI flag - clear AI fields and set status to None
        if asset.status in ["needs_review", "requires_validation"]:
            asset.status = None
            asset.ai_suggestion = None
            asset.ai_flag_reason = None
            asset.ai_suggested_tags = None

    # Standard field updates
    if "name" in data:
        asset.name = data["name"]

    if "description" in data:
        asset.description = data["description"]
        # If user manually edits, mark as validated
        if not data.get("approve_suggestion") and not data.get("reject_suggestion"):
            asset.status = "validated"

    if "tag_ids" in data:
        asset.asset_tags.clear()

        # Add new tag associations
        for tag_id in data["tag_ids"]:
            tag_uuid = UUID(tag_id)
            tag = (
                g.session.query(AssetTag)
                .filter(
                    AssetTag.id == tag_uuid,
                    AssetTag.database_id == asset.database_id,
                )
                .first()
            )
            if tag:
                asset.asset_tags.append(tag)

    g.session.flush()

    # Broadcast real-time update to other users viewing this database
    emit_asset_updated(asset, g.user.id)

    asset_dict = asset.to_dict()
    asset_dict["tags"] = [tag.to_dict() for tag in asset.asset_tags]
    if asset.type == "TABLE" and asset.table_facet:
        asset_dict["table_facet"] = asset.table_facet.to_dict()
    elif asset.type == "COLUMN" and asset.column_facet:
        column_facet_dict = asset.column_facet.to_dict()

        # Include parent table information for columns (same as GET endpoint)
        if (
            asset.column_facet.parent_table_asset
            and asset.column_facet.parent_table_asset.table_facet
        ):
            column_facet_dict["parent_table_facet"] = (
                asset.column_facet.parent_table_asset.table_facet.to_dict()
            )

        asset_dict["column_facet"] = column_facet_dict

    return jsonify(asset_dict)


@api.route("/catalogs/assets/<string:asset_id>/preview", methods=["GET"])
@user_middleware
def get_asset_preview(asset_id: str):
    """Get preview data (~10 random rows) for a table asset"""

    try:
        asset_uuid = UUID(asset_id)
    except ValueError:
        return jsonify({"error": "Invalid asset id"}), 400

    asset = (
        g.session.query(Asset)
        .filter(Asset.id == asset_uuid)
        .options(joinedload(Asset.table_facet))
        .first()
    )

    if not asset:
        return jsonify({"error": "Asset not found"}), 404

    # Only support table assets
    if asset.type != "TABLE":
        return jsonify({"error": "Preview only available for table assets"}), 400

    if not asset.table_facet:
        return jsonify({"error": "Table facet not found"}), 404

    # Get database and verify access
    database = g.session.query(Database).filter_by(id=asset.database_id).first()

    if not database:
        return jsonify({"error": "Database not found"}), 404

    # Verify user has access
    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
        or database.public
    ):
        return jsonify({"error": "Access denied"}), 403

    # Get table details
    schema = asset.table_facet.schema
    table_name = asset.table_facet.table_name

    if not table_name:
        return jsonify({"error": "Table name not found"}), 400

    # Get limit from query params (default 10, max 20)
    limit = min(int(request.args.get("limit", 10)), 20)

    try:
        dw = database.create_data_warehouse()

        # Use the data warehouse's get_sample_data method
        sample_result = dw.get_sample_data(table_name, schema, limit)

        if not sample_result:
            return jsonify({"error": "No sample data available"}), 404

        # Check for error in result
        if "error" in sample_result:
            return jsonify({"error": sample_result["error"]}), 500

        # Return the data in a format compatible with the frontend
        return jsonify(
            {"rows": sample_result["data"], "count": sample_result["sample_size"]}
        )

    except ConnectionError as e:
        return jsonify({"error": f"Connection error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error fetching preview data: {str(e)}")
        return jsonify({"error": f"Failed to fetch preview data: {str(e)}"}), 500


@api.route("/catalogs/assets/<string:asset_id>/sources", methods=["GET"])
@user_middleware
def get_asset_sources(asset_id: str):
    """Get metadata from external sources (DBT, data provider) for an asset"""

    try:
        asset_uuid = UUID(asset_id)
    except ValueError:
        return jsonify({"error": "Invalid asset id"}), 400

    asset = g.session.query(Asset).filter(Asset.id == asset_uuid).first()

    if not asset:
        return jsonify({"error": "Asset not found"}), 404

    # Get database and verify access
    database = g.session.query(Database).filter_by(id=asset.database_id).first()

    if not database:
        return jsonify({"error": "Database not found"}), 404

    # Verify user has access
    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
        or database.public
    ):
        return jsonify({"error": "Access denied"}), 403

    try:
        sources = {}

        dw = database.create_data_warehouse()
        provider_metadata = get_provider_metadata_for_asset(asset, dw, g.session)
        if provider_metadata:
            sources[dw.dialect] = provider_metadata

        return jsonify(sources)

    except ConnectionError as e:
        return jsonify({"error": f"Connection error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error fetching asset sources: {str(e)}")
        return jsonify({"error": f"Failed to fetch asset sources: {str(e)}"}), 500


@api.route("/catalogs/<string:context_id>/terms", methods=["GET"])
@user_middleware
def get_catalog_terms(context_id):
    """Get catalog terms for a context"""
    database_id, _ = extract_context(g.session, context_id)
    database = g.session.query(Database).filter_by(id=database_id).first()

    if not database:
        return jsonify({"error": "Database not found"}), 404

    # Verify user has access
    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
        or database.public
    ):
        return jsonify({"error": "Access denied"}), 403

    limit = int(request.args.get("limit", 50))

    terms = (
        g.session.query(Term).filter(Term.database_id == database_id).limit(limit).all()
    )

    return jsonify([term.to_dict() for term in terms])


@api.route("/catalogs/<string:context_id>/terms", methods=["POST"])
@user_middleware
def create_catalog_term(context_id):
    """Create a new catalog term"""
    database_id, _ = extract_context(g.session, context_id)
    database = g.session.query(Database).filter_by(id=database_id).first()

    if not database:
        return jsonify({"error": "Database not found"}), 404

    # Verify user has access
    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
        or database.public
    ):
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a valid JSON object"}), 400
    required_fields = ["name", "definition"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields: name, definition"}), 400

    # Check if term with same name already exists
    existing_term = (
        g.session.query(Term)
        .filter(Term.database_id == database_id, Term.name.ilike(data["name"]))
        .first()
    )

    if existing_term:
        return jsonify({"error": "Term with this name already exists"}), 409

    new_term = Term(
        name=data["name"],
        definition=data["definition"],
        database_id=database_id,
        synonyms=data.get("synonyms", []),
        business_domains=data.get("business_domains", []),
    )

    g.session.add(new_term)
    g.session.flush()

    return jsonify(new_term.to_dict()), 201


@api.route("/catalogs/terms/<string:term_id>", methods=["PATCH"])
@user_middleware
def update_catalog_term(term_id: str):
    """Update mutable fields of a catalog term."""

    try:
        term_uuid = UUID(term_id)
    except ValueError:
        return jsonify({"error": "Invalid term id"}), 400

    term = g.session.query(Term).filter(Term.id == term_uuid).first()

    if not term:
        return jsonify({"error": "Term not found"}), 404

    data = request.get_json(silent=True) or {}

    if "name" in data:
        term.name = data["name"]

    if "definition" in data:
        term.definition = data["definition"]

    if "synonyms" in data:
        term.synonyms = data["synonyms"]

    if "business_domains" in data:
        term.business_domains = data["business_domains"]

    if "reviewed" in data:
        term.reviewed = data["reviewed"]

    g.session.flush()

    return jsonify(term.to_dict())


@api.route("/catalogs/terms/<string:term_id>", methods=["DELETE"])
@user_middleware
def delete_catalog_term(term_id: str):
    """Delete a catalog term"""
    try:
        term_uuid = UUID(term_id)
    except ValueError:
        return jsonify({"error": "Invalid term id"}), 400

    term = g.session.query(Term).filter(Term.id == term_uuid).first()

    if not term:
        return jsonify({"error": "Term not found"}), 404

    # Verify user has access
    database = g.session.query(Database).filter_by(id=term.database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404
    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
        or database.public
    ):
        return jsonify({"error": "Access denied"}), 403

    g.session.delete(term)
    g.session.flush()

    return jsonify({"success": True})


@api.route("/catalogs/<string:context_id>/tags", methods=["GET"])
@user_middleware
def get_catalog_tags(context_id):
    """Get all available tags for a context"""
    database_id, _ = extract_context(g.session, context_id)
    database = g.session.query(Database).filter_by(id=database_id).first()

    if not database:
        return jsonify({"error": "Database not found"}), 404

    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
        or database.public
    ):
        return jsonify({"error": "Access denied"}), 403

    tags = g.session.query(AssetTag).filter(AssetTag.database_id == database_id).all()

    return jsonify([tag.to_dict() for tag in tags])


@api.route("/catalogs/<string:context_id>/tags", methods=["POST"])
@user_middleware
def create_catalog_tag(context_id):
    """Create a new tag"""
    database_id, _ = extract_context(g.session, context_id)
    database = g.session.query(Database).filter_by(id=database_id).first()

    if not database:
        return jsonify({"error": "Database not found"}), 404

    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
        or database.public
    ):
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a valid JSON object"}), 400

    required_fields = ["name"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required field: name"}), 400

    # Check if tag with same name already exists
    existing_tag = (
        g.session.query(AssetTag)
        .filter(AssetTag.database_id == database_id, AssetTag.name.ilike(data["name"]))
        .first()
    )

    if existing_tag:
        return jsonify({"error": "Tag with this name already exists"}), 409

    new_tag = AssetTag(
        name=data["name"],
        description=data.get("description"),
        database_id=database_id,
    )

    g.session.add(new_tag)
    g.session.flush()

    # Broadcast tag creation to other users viewing this database
    emit_tag_updated(new_tag, g.user.id)

    return jsonify(new_tag.to_dict()), 201


@api.route("/catalogs/tags/<string:tag_id>", methods=["PATCH"])
@user_middleware
def update_catalog_tag(tag_id: str):
    """Update a tag's properties"""
    try:
        tag_uuid = UUID(tag_id)
    except ValueError:
        return jsonify({"error": "Invalid tag id"}), 400

    tag = g.session.query(AssetTag).filter(AssetTag.id == tag_uuid).first()

    if not tag:
        return jsonify({"error": "Tag not found"}), 404

    # Verify user has access
    database = g.session.query(Database).filter_by(id=tag.database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
    ):
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json(silent=True) or {}

    if "name" in data:
        # Check if another tag with this name already exists
        existing_tag = (
            g.session.query(AssetTag)
            .filter(
                AssetTag.database_id == tag.database_id,
                AssetTag.name.ilike(data["name"]),
                AssetTag.id != tag_uuid,
            )
            .first()
        )
        if existing_tag:
            return jsonify({"error": "Tag with this name already exists"}), 409
        tag.name = data["name"]

    if "description" in data:
        tag.description = data["description"]

    g.session.flush()

    # Broadcast tag update to other users viewing this database
    emit_tag_updated(tag, g.user.id)

    return jsonify(tag.to_dict())


@api.route("/catalogs/tags/<string:tag_id>", methods=["DELETE"])
@user_middleware
def delete_catalog_tag(tag_id: str):
    """Delete a tag (removes all associations)"""
    try:
        tag_uuid = UUID(tag_id)
    except ValueError:
        return jsonify({"error": "Invalid tag id"}), 400

    tag = g.session.query(AssetTag).filter(AssetTag.id == tag_uuid).first()

    if not tag:
        return jsonify({"error": "Tag not found"}), 404

    # Verify user has access
    database = g.session.query(Database).filter_by(id=tag.database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
    ):
        return jsonify({"error": "Access denied"}), 403

    g.session.delete(tag)
    g.session.flush()

    # Broadcast tag deletion to other users viewing this database
    emit_tag_deleted(tag_uuid, tag.database_id, g.user.id)

    return jsonify({"success": True})


@api.route("/business-entities", methods=["GET"])
@user_middleware
def get_business_entities():
    context_id = request.args.get("contextId")
    database_id, project_id = extract_context(g.session, context_id)

    # Verify user has access to the database through organization or ownership
    database = g.session.query(Database).filter_by(id=database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
        or database.public
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

    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
        or database.public
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


@api.route("/databases/<uuid:database_id>/validate-dbt-repo", methods=["POST"])
@user_middleware
def validate_dbt_repository(database_id: UUID):
    """Validate that a repository path contains a valid DBT project."""
    database = g.session.query(Database).filter_by(id=database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    # Verify user has access to update this database
    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
    ):
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    repo_path = data.get("repo_path")

    if not repo_path:
        return jsonify({"error": "Repository path is required"}), 400

    try:
        is_valid = validate_dbt_repo(repo_path)
        if is_valid:
            return jsonify({"success": True, "message": "Valid DBT repository"})
        else:
            return jsonify({"success": False, "message": "Invalid DBT repository"})
    except Exception as e:
        logger.error(f"Error validating DBT repository: {e}")
        return jsonify({"success": False, "message": str(e)}), 400


@api.route("/databases/<uuid:database_id>/generate-dbt-docs", methods=["POST"])
@user_middleware
def generate_dbt_documentation(database_id: UUID):
    """Generate DBT documentation from repository and update database."""
    database = g.session.query(Database).filter_by(id=database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    # Verify user has access to update this database
    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
    ):
        return jsonify({"error": "Access denied"}), 403

    if not database.dbt_repo_path:
        return jsonify({"error": "No DBT repository path configured"}), 400

    try:
        # Prepare database config for DBT
        database_config = {
            "engine": database.engine,
            "details": database.details,
        }

        # Generate docs
        catalog, manifest = generate_dbt_docs(database.dbt_repo_path, database_config)

        # Update database with generated docs
        database.dbt_catalog = catalog
        database.dbt_manifest = manifest
        g.session.flush()

        return jsonify(
            {
                "success": True,
                "message": "DBT documentation generated successfully",
                "catalog_nodes": len(catalog.get("nodes", {})),
                "manifest_nodes": len(manifest.get("nodes", {})),
            }
        )

    except DBTRepositoryError as e:
        logger.error(f"DBT repository error: {e}")
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Error generating DBT documentation: {e}")
        return jsonify({"error": f"Failed to generate documentation: {str(e)}"}), 500


@api.route("/databases/<uuid:database_id>/sync-metadata", methods=["POST"])
@user_middleware
def sync_database_metadata(database_id: UUID):
    """Start background sync of database metadata to catalog."""
    database = g.session.query(Database).filter_by(id=database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    # Verify user has access to this database
    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
        or database.public
    ):
        return jsonify({"error": "Unauthorized"}), 403

    # Check if already syncing
    if database.sync_status == "syncing":
        return (
            jsonify(
                {
                    "error": "Sync already in progress",
                }
            ),
            409,
        )

    # Test connection before starting background sync
    try:
        data_warehouse = database.create_data_warehouse()
        data_warehouse.test_connection()
    except ConnectionError as e:
        return jsonify({"error": f"Connection error: {str(e)}"}), 500

    # Start the background task
    run_metadata_sync_background(
        database_id=database_id,
        session_factory=get_db_session,
    )

    # Return immediately with 202 Accepted
    return (
        jsonify(
            {
                "success": True,
                "message": "Metadata sync started in background",
            }
        ),
        202,
    )


@api.route("/databases/<uuid:database_id>/sync-status", methods=["GET"])
@user_middleware
def get_sync_status(database_id: UUID):
    """Get the current sync status for a database."""
    database = g.session.query(Database).filter_by(id=database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    # Verify user has access to this database
    if not (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
        or database.public
    ):
        return jsonify({"error": "Unauthorized"}), 403

    return jsonify(
        {
            "sync_status": database.sync_status,
            "sync_progress": database.sync_progress,
            "sync_started_at": (
                database.sync_started_at.isoformat()
                if database.sync_started_at
                else None
            ),
            "sync_completed_at": (
                database.sync_completed_at.isoformat()
                if database.sync_completed_at
                else None
            ),
            "sync_error": database.sync_error,
        }
    )


@api.route("/organisation", methods=["GET"])
@user_middleware
def get_organisation():
    """Get organisation information for the current user."""
    if not g.organisation:
        return jsonify({"error": "No organisation found"}), 404

    return jsonify(g.organisation.to_dict())


@api.route("/organisation", methods=["PATCH"])
@user_middleware
@admin_required
def update_organisation():
    """Update organisation settings. Admin only."""
    if not g.organisation:
        return jsonify({"error": "No organisation found"}), 404

    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Only allow updating language for now
    if "language" in data:
        g.organisation.language = data["language"]
        g.session.flush()

    return jsonify(g.organisation.to_dict())
