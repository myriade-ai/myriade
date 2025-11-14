import json
import logging
import os
import socket
from typing import Any
from uuid import UUID

import anthropic
from agentlys import Agentlys
from flask import Blueprint, g, jsonify, request
from sqlalchemy import and_, or_
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session, contains_eager, joinedload, selectinload
from sqlalchemy.sql.expression import true

import telemetry
from back.background_sync import run_metadata_sync_background
from back.catalog_events import (
    emit_asset_updated,
    emit_tag_deleted,
    emit_tag_updated,
)
from back.catalog_search import search_assets
from back.data_warehouse import ConnectionError, DataWarehouseFactory
from back.dbt_sync import run_dbt_generation_background
from back.github_manager import (
    GithubIntegrationError,
    create_pull_request_for_conversation,
    ensure_valid_access_token,
    exchange_oauth_code,
    get_github_integration,
    get_workspace_changes,
    list_repositories,
    start_oauth_flow,
)
from back.session import get_db_session
from back.sync_state import get_sync_state
from back.utils import (
    create_database,
    get_provider_metadata_for_asset,
    get_tables_metadata_from_catalog,
    update_catalog_privacy,
)
from chat.proxy_provider import ProxyProvider
from config import DATABASE_URL
from middleware import admin_required, user_middleware
from models import (
    DBT,
    Chart,
    Conversation,
    ConversationMessage,
    Database,
    Document,
    DocumentVersion,
    GithubIntegration,
    GithubOAuthState,
    Note,
    Project,
    ProjectTables,
    Query,
    UserFavorite,
)
from models.catalog import (
    Asset,
    AssetTag,
    ColumnFacet,
    TableFacet,
    Term,
)
from models.quality import BusinessEntity, Issue

logger = logging.getLogger(__name__)
api = Blueprint("back_api", __name__)

AGENTLYS_PROVIDER = os.getenv("AGENTLYS_PROVIDER", "proxy")


try:
    _INTERNAL_DATABASE_URL = make_url(DATABASE_URL)
except Exception:
    _INTERNAL_DATABASE_URL = None


def _normalize_host(value: Any) -> str | None:
    if value is None:
        return None
    return str(value).strip().lower()


def _resolve_host_to_ips(host: str | None) -> set[str]:
    """
    Resolve a hostname to its IP addresses.
    Returns a set of IP addresses that the hostname resolves to.
    Returns empty set if host is None or resolution fails.
    """
    if not host:
        return set()

    normalized_host = _normalize_host(host)
    if not normalized_host:
        return set()

    resolved_ips = set()

    try:
        # Get all IP addresses for the hostname
        addr_info = socket.getaddrinfo(normalized_host, None)
        for info in addr_info:
            ip_address = info[4][0]
            # Normalize IPv6 addresses by removing zone identifiers and converting to lowercase
            if "%" in ip_address:
                ip_address = ip_address.split("%")[0]
            resolved_ips.add(ip_address.lower())
    except (socket.gaierror, socket.error, OSError):
        # If resolution fails, fall back to comparing the normalized string
        # This ensures we don't accidentally allow connections due to DNS errors
        resolved_ips.add(normalized_host)

    return resolved_ips


def _is_internal_database(engine: str, details: dict[str, Any]) -> bool:
    """
    Prevent users from connecting to the application's own database.
    Resolves hostnames to IPs to prevent bypasses via alternative addresses
    (e.g., localhost vs 127.0.0.1, Docker service names vs IPs).
    """

    if not _INTERNAL_DATABASE_URL:
        return False

    driver_name = _INTERNAL_DATABASE_URL.get_backend_name()

    if engine == "postgres" and driver_name.startswith("postgres"):
        # Resolve both hosts to IPs for comparison
        request_host_ips = _resolve_host_to_ips(details.get("host"))
        internal_host_ips = _resolve_host_to_ips(_INTERNAL_DATABASE_URL.host)

        # If any IP addresses match, the hosts refer to the same machine
        if not request_host_ips.isdisjoint(internal_host_ips):
            port = str(details.get("port", "5432"))
            internal_port = str(_INTERNAL_DATABASE_URL.port or "5432")

            database = details.get("database", "postgres")
            internal_database = _INTERNAL_DATABASE_URL.database or "postgres"

            return port == internal_port and database == internal_database

        return False

    if engine == "sqlite" and driver_name.startswith("sqlite"):
        filename = details.get("filename")
        if not filename or not _INTERNAL_DATABASE_URL.database:
            return False
        return os.path.abspath(filename) == os.path.abspath(
            _INTERNAL_DATABASE_URL.database
        )

    return False


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


def _github_settings_payload(integration: GithubIntegration | None) -> dict[str, Any]:
    if not integration:
        return {
            "connected": False,
            "hasToken": False,
            "repoOwner": None,
            "repoName": None,
            "repoFullName": None,
            "defaultBranch": None,
            "tokenExpiresAt": None,
        }

    repo_full_name = (
        f"{integration.repo_owner}/{integration.repo_name}"
        if integration.repo_owner and integration.repo_name
        else None
    )
    return {
        "connected": bool(repo_full_name),
        "hasToken": bool(integration.access_token),
        "repoOwner": integration.repo_owner,
        "repoName": integration.repo_name,
        "repoFullName": repo_full_name,
        "defaultBranch": integration.default_branch,
        "tokenExpiresAt": integration.token_expires_at.isoformat()
        if integration.token_expires_at
        else None,
    }


def _user_can_manage_database(database: Database) -> bool:
    if database.ownerId == g.user.id:
        return True
    if (
        database.organisationId is not None
        and g.organization_id is not None
        and database.organisationId == g.organization_id
        and g.auth_user.role == "admin"
    ):
        return True
    return False


def _get_catalog_database(database_id: UUID) -> tuple[Database | None, tuple | None]:
    """Fetch a database and verify the current user has access to it."""

    database = g.session.query(Database).filter_by(id=database_id).first()
    if not database:
        return None, (jsonify({"error": "Database not found"}), 404)

    has_access = (
        database.ownerId == g.user.id
        or (
            database.organisationId is not None
            and database.organisationId == g.organization_id
        )
        or database.public
    )

    if not has_access:
        return None, (jsonify({"error": "Access denied"}), 403)

    return database, None


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


@api.route("/conversations/<uuid:conversation_id>/github/changes", methods=["GET"])
@user_middleware
def get_conversation_changes(conversation_id: UUID):
    """Get detailed information about uncommitted changes in conversation workspace."""
    conversation = (
        g.session.query(Conversation)
        .options(joinedload(Conversation.database))
        .filter(Conversation.id == conversation_id)
        .first()
    )
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    user_owns_conversation = conversation.ownerId == g.user.id
    database = conversation.database
    user_in_same_org = (
        database.organisationId is not None
        and g.organization_id is not None
        and database.organisationId == g.organization_id
    )

    if not (user_owns_conversation or user_in_same_org):
        return jsonify({"error": "Cannot access conversations you don't own"}), 403

    changes = get_workspace_changes(g.session, conversation)
    return jsonify(changes)


@api.route("/conversations/<uuid:conversation_id>/github/pr", methods=["POST"])
@user_middleware
def create_conversation_pull_request(conversation_id: UUID):
    conversation = (
        g.session.query(Conversation)
        .options(joinedload(Conversation.database))
        .filter(Conversation.id == conversation_id)
        .first()
    )
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    user_owns_conversation = conversation.ownerId == g.user.id
    database = conversation.database
    user_in_same_org = (
        database.organisationId is not None
        and g.organization_id is not None
        and database.organisationId == g.organization_id
    )

    if not (user_owns_conversation or user_in_same_org):
        return jsonify({"error": "Cannot modify conversations you don't own"}), 403

    if conversation.github_pr_url:
        return jsonify(
            {"error": "A pull request already exists for this conversation."}
        ), 400

    integration = get_github_integration(g.session, database.id)
    if (
        not integration
        or not integration.access_token
        or not integration.repo_owner
        or not integration.repo_name
    ):
        return jsonify(
            {"error": "GitHub integration is not configured for this database"}
        ), 400

    # Build context for AI agent
    context_text = f"""# Conversation Context
Conversation Name: {conversation.name or "Unnamed conversation"}
Database: {database.name}
Branch: myriade/{conversation.id}
Repository: {integration.repo_owner}/{integration.repo_name}

# Task
Generate a pull request title, commit message, and description based on the full
conversation history that will be loaded. The PR will contain changes made during
this conversation.
"""

    # Set up AI agent to generate PR details
    if AGENTLYS_PROVIDER == "proxy":
        provider = ProxyProvider
    else:
        provider = AGENTLYS_PROVIDER

    pr_agent = Agentlys(
        provider=provider,
        context=context_text,
        use_tools_only=True,
    )

    # Load the full conversation history into the agent
    messages = (
        g.session.query(ConversationMessage)
        .filter_by(conversationId=conversation.id)
        .order_by(ConversationMessage.createdAt)
        .all()
    )
    agentlys_messages = [m.to_agentlys_message() for m in messages]
    pr_agent.load_messages(agentlys_messages)

    # Define the function that will capture the generated PR details

    def generate_pull_request(title: str, commit_message: str, body: str):
        """Generate a pull request with title, commit message, and description."""
        pass

    pr_agent.add_function(generate_pull_request)

    # Ask the agent to generate PR details
    prompt = """Generate a pull request for the changes made in this conversation.
Provide:
1. A clear, concise title (max 72 characters) that summarizes the changes
2. A commit message (one line summarizing the commit)
3. A description body that explains what was changed and why (can be multiple lines)

Make sure the title is specific and professional."""

    try:
        message = pr_agent.ask(prompt)
    except Exception as e:
        logger.error(
            "Error generating PR with AI", exc_info=True, extra={"error": str(e)}
        )
        return jsonify({"error": f"Failed to generate PR details: {str(e)}"}), 500

    response_dict = message.function_call["arguments"]

    try:
        url = create_pull_request_for_conversation(
            g.session, conversation, **response_dict
        )
        conversation.github_pr_url = url
        g.session.flush()
    except GithubIntegrationError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(
        {
            "github_pr_url": url,
        }
    )


@api.route("/databases", methods=["POST"])
@user_middleware
@admin_required
def create_database_route():
    """Create a new database and sync its metadata to the catalog."""
    data = request.get_json()

    if _is_internal_database(data["engine"], data["details"]):
        return (
            jsonify(
                {
                    "message": "Connecting to the internal Myriade database is not allowed."
                }
            ),
            400,
        )

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
    database_dict = database.to_dict()
    database_dict["sync_status"] = "syncing"
    database_dict["sync_progress"] = 0
    return jsonify(database_dict)


@api.route("/databases/test-connection", methods=["POST"])
@user_middleware
def test_database_connection():
    """Test database connection without creating the database."""
    data = request.get_json()

    if _is_internal_database(data["engine"], data["details"]):
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Connecting to the internal Myriade database is not allowed.",
                }
            ),
            400,
        )

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

    # Delete all related records to avoid foreign key violations
    # Order matters: delete children before parents

    # Get conversation message IDs for this database before deletion
    conversation_message_ids = [
        msg.id
        for msg in g.session.query(ConversationMessage.id)
        .filter(
            ConversationMessage.conversationId.in_(
                g.session.query(Conversation.id).filter(
                    Conversation.databaseId == database_id
                )
            )
        )
        .all()
    ]

    # Set issue.message_id to NULL for issues referencing these messages
    if conversation_message_ids:
        g.session.query(Issue).filter(
            Issue.message_id.in_(conversation_message_ids)
        ).update({"message_id": None}, synchronize_session=False)

    # Delete conversation messages (they reference queries and charts)
    g.session.query(ConversationMessage).filter(
        ConversationMessage.conversationId.in_(
            g.session.query(Conversation.id).filter(
                Conversation.databaseId == database_id
            )
        )
    ).delete(synchronize_session=False)

    # Delete user favorites for queries/charts in this database
    g.session.query(UserFavorite).filter(
        or_(
            UserFavorite.query_id.in_(
                g.session.query(Query.id).filter(Query.databaseId == database_id)
            ),
            UserFavorite.chart_id.in_(
                g.session.query(Chart.id).filter(
                    Chart.queryId.in_(
                        g.session.query(Query.id).filter(
                            Query.databaseId == database_id
                        )
                    )
                )
            ),
        )
    ).delete(synchronize_session=False)

    # Delete charts (references queries)
    g.session.query(Chart).filter(
        Chart.queryId.in_(
            g.session.query(Query.id).filter(Query.databaseId == database_id)
        )
    ).delete(synchronize_session=False)

    # Delete queries
    g.session.query(Query).filter(Query.databaseId == database_id).delete(
        synchronize_session=False
    )

    # Delete catalog-related records
    # Delete facets first (column_facet has parent_table_asset_id FK to asset)
    from models.catalog import (
        ColumnFacet,
        DatabaseFacet,
        SchemaFacet,
        TableFacet,
        asset_tag_association,
    )

    # Get all asset IDs for this database
    asset_ids = [
        asset.id
        for asset in g.session.query(Asset.id)
        .filter(Asset.database_id == database_id)
        .all()
    ]

    if asset_ids:
        # Delete asset-tag associations first
        g.session.execute(
            asset_tag_association.delete().where(
                asset_tag_association.c.asset_id.in_(asset_ids)
            )
        )

        # Delete facets explicitly to avoid FK violations
        g.session.query(ColumnFacet).filter(ColumnFacet.asset_id.in_(asset_ids)).delete(
            synchronize_session=False
        )
        g.session.query(TableFacet).filter(TableFacet.asset_id.in_(asset_ids)).delete(
            synchronize_session=False
        )
        g.session.query(SchemaFacet).filter(SchemaFacet.asset_id.in_(asset_ids)).delete(
            synchronize_session=False
        )
        g.session.query(DatabaseFacet).filter(
            DatabaseFacet.asset_id.in_(asset_ids)
        ).delete(synchronize_session=False)

        # Now safe to delete assets
        g.session.query(Asset).filter(Asset.database_id == database_id).delete(
            synchronize_session=False
        )

    # Delete terms
    g.session.query(Term).filter(Term.database_id == database_id).delete(
        synchronize_session=False
    )

    # Delete asset tags
    g.session.query(AssetTag).filter(AssetTag.database_id == database_id).delete(
        synchronize_session=False
    )

    # Delete issues
    g.session.query(Issue).filter(Issue.database_id == database_id).delete(
        synchronize_session=False
    )

    # Delete business entities
    g.session.query(BusinessEntity).filter(
        BusinessEntity.database_id == database_id
    ).delete(synchronize_session=False)

    # Get project IDs before deletion to handle dependent records
    project_ids = [
        proj.id
        for proj in g.session.query(Project.id)
        .filter(Project.databaseId == database_id)
        .all()
    ]

    if project_ids:
        # Set conversation.projectId to NULL for conversations in these projects
        g.session.query(Conversation).filter(
            Conversation.projectId.in_(project_ids)
        ).update({"projectId": None}, synchronize_session=False)

        # Delete project_tables (bulk delete bypasses ORM cascades)
        g.session.query(ProjectTables).filter(
            ProjectTables.projectId.in_(project_ids)
        ).delete(synchronize_session=False)

        # Delete notes
        g.session.query(Note).filter(Note.projectId.in_(project_ids)).delete(
            synchronize_session=False
        )

    # Delete projects
    g.session.query(Project).filter(Project.databaseId == database_id).delete(
        synchronize_session=False
    )

    # Delete documents (document versions will cascade)
    g.session.query(Document).filter(Document.database_id == database_id).delete(
        synchronize_session=False
    )

    # Delete GitHub integration
    g.session.query(GithubIntegration).filter(
        GithubIntegration.databaseId == database_id
    ).delete(synchronize_session=False)

    # Delete GitHub OAuth state
    g.session.query(GithubOAuthState).filter(
        GithubOAuthState.databaseId == database_id
    ).delete(synchronize_session=False)

    # Get conversation IDs before deletion
    conversation_ids = [
        conv.id
        for conv in g.session.query(Conversation.id)
        .filter(Conversation.databaseId == database_id)
        .all()
    ]

    # Set business_entity.review_conversation_id to NULL for entities referencing these conversations
    if conversation_ids:
        g.session.query(BusinessEntity).filter(
            BusinessEntity.review_conversation_id.in_(conversation_ids)
        ).update({"review_conversation_id": None}, synchronize_session=False)

    # Delete conversations (messages already deleted above)
    g.session.query(Conversation).filter(Conversation.databaseId == database_id).delete(
        synchronize_session=False
    )

    # Delete DBT records
    g.session.query(DBT).filter(DBT.database_id == database_id).delete(
        synchronize_session=False
    )

    # Now safe to delete the database
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

    if _is_internal_database(data["engine"], data["details"]):
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Connecting to the internal Myriade database is not allowed.",
                }
            ),
            400,
        )

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

    g.session.flush()

    # IMPORTANT: Commit the database before starting background thread
    # The background thread needs to be able to query the database record
    g.session.commit()

    run_metadata_sync_background(
        database_id=database.id,
        session_factory=get_db_session,
    )

    # Return immediately - metadata sync runs in background
    database_dict = database.to_dict()
    database_dict["sync_status"] = "syncing"
    database_dict["sync_progress"] = 0
    return jsonify(database_dict)


@api.route("/databases/<uuid:database_id>/share", methods=["PUT"])
@user_middleware
def share_database_to_organisation(database_id: UUID):
    """Share or unshare a database to/from the current user's organisation."""
    data = request.get_json()
    share_to_org = data.get("share_to_organisation", False)

    # Get the database
    database = g.session.query(Database).filter_by(id=database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    # Only the owner can share/unshare their database
    if database.ownerId != g.user.id:
        return jsonify({"error": "Only the database owner can share it"}), 403

    # Update the organisationId
    if share_to_org:
        if not g.organization_id:
            return jsonify({"error": "User is not part of an organisation"}), 400
        database.organisationId = g.organization_id
    else:
        # Unshare: remove from organisation
        database.organisationId = None

    g.session.flush()
    database_dict = database.to_dict()
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
    databases_list = [db.to_dict() for db in databases_query]
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

    context = (
        "# Database Name: "
        + database.name
        + "\n# Memory: "  # TODO: use Catalog asset instead of database.memory
        + (database.memory or "No memory")
    )

    if project_id:
        project = g.session.query(Project).filter_by(id=project_id).first()
        if not project:
            raise ValueError(f"Project with id {project_id} not found")
        context += "\n# Project Name: " + project.name
        context += "\n# Project Description: " + project.description

    if AGENTLYS_PROVIDER == "proxy":
        provider = ProxyProvider
    else:
        provider = AGENTLYS_PROVIDER

    questionAssistant = Agentlys(
        provider=provider,
        context=json.dumps(context),
        use_tools_only=True,
    )

    def questions(question1: str, question2: str, question3: str):
        pass

    questionAssistant.add_function(questions)

    prompt = (
        "Generate 3 business questions about different topics that the user "
        + "can ask based on the context (database name, memory, etc)"
        + f"\nDo it in the user preferred language (Accept-Language: {user_language})"
        + "If you don't have enough information about the database, this is the questions (explore the data, complete the catalog, ... etc)"
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
@api.route("/databases/<uuid:database_id>/catalog/assets", methods=["GET"])
@user_middleware
def get_catalog_assets(database_id: UUID):
    """Get all catalog assets for a database."""

    database, error_response = _get_catalog_database(database_id)
    if error_response:
        return error_response

    if database is None:
        return jsonify({"error": "Database not found"}), 404

    # Build query to fetch all assets with all facets
    # Use selectinload for parent relationships to avoid N+1 queries
    query = (
        g.session.query(Asset)
        .filter(Asset.database_id == database.id)
        .outerjoin(Asset.database_facet)
        .outerjoin(Asset.schema_facet)
        .outerjoin(Asset.table_facet)
        .outerjoin(Asset.column_facet)
        .options(
            contains_eager(Asset.database_facet),
            contains_eager(Asset.schema_facet),
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
    database_id_str = str(database.id)

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
        if asset_type == "DATABASE":
            df = asset.database_facet
            if df:
                asset_dict["database_facet"] = {
                    "asset_id": asset_id_str,
                    "database_id": database_id_str,
                    "database_name": df.database_name,
                }
        elif asset_type == "SCHEMA":
            sf = asset.schema_facet
            if sf:
                asset_dict["schema_facet"] = {
                    "asset_id": asset_id_str,
                    "database_id": database_id_str,
                    "database_name": sf.database_name,
                    "schema_name": sf.schema_name,
                    "parent_database_asset_id": str(sf.parent_database_asset_id),
                }
        elif asset_type == "TABLE":
            tf = asset.table_facet
            if tf:
                asset_dict["table_facet"] = {
                    "asset_id": asset_id_str,
                    "database_id": database_id_str,
                    "database_name": tf.database_name,
                    "schema": tf.schema,
                    "table_name": tf.table_name,
                    "table_type": tf.table_type,
                }
                if tf.parent_schema_asset_id:
                    asset_dict["table_facet"]["parent_schema_asset_id"] = str(
                        tf.parent_schema_asset_id
                    )
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


@api.route("/databases/<uuid:database_id>/catalog/search", methods=["GET"])
@user_middleware
def search_catalog_assets(database_id: UUID):
    """
    Search catalog assets by text query. Returns only asset IDs.

    Query parameters:
    - q: Search query string (required)
    - asset_type: Filter by type (optional: "TABLE", "COLUMN", "SCHEMA", "DATABASE")
    - tag_ids: Filter by tag IDs (optional, array: ?tag_ids=uuid1&tag_ids=uuid2)
    - statuses: Filter by status values (optional, array: ?statuses=validated&statuses=needs_review)

    Returns: Array of matching asset IDs (strings)
    """
    database, error_response = _get_catalog_database(database_id)
    if error_response:
        return error_response

    if database is None:
        return jsonify({"error": "Database not found"}), 404

    # Get search query from parameters
    search_query = request.args.get("q", "").strip()
    if not search_query:
        return jsonify({"error": "Search query (q parameter) is required"}), 400

    # Get optional parameters
    asset_type = request.args.get("asset_type", "").strip() or None
    tag_ids = request.args.getlist("tag_ids") or None
    statuses = request.args.getlist("statuses") or None

    try:
        results = search_assets(
            g.session,
            database_id,
            search_query,
            asset_type=asset_type,
            tag_ids=tag_ids,
            statuses=statuses,
            limit=50,
        )
        asset_ids = [asset["id"] for asset in results]
        return jsonify(asset_ids)
    except Exception as e:
        logger.error(f"Error searching catalog assets: {str(e)}", exc_info=True)
        return jsonify({"error": f"Search failed: {str(e)}"}), 500


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

    if asset.type == "DATABASE" and asset.database_facet:
        asset_dict["database_facet"] = asset.database_facet.to_dict()
    elif asset.type == "SCHEMA" and asset.schema_facet:
        asset_dict["schema_facet"] = asset.schema_facet.to_dict()
    elif asset.type == "TABLE" and asset.table_facet:
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
    database_name = asset.table_facet.database_name

    if not table_name:
        return jsonify({"error": "Table name not found"}), 400

    # Get limit from query params (default 10, max 20)
    limit = min(int(request.args.get("limit", 10)), 20)

    try:
        dw = database.create_data_warehouse()

        # Use the data warehouse's get_sample_data method
        sample_result = dw.get_sample_data(table_name, schema, limit, database_name)

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


@api.route("/databases/<uuid:database_id>/catalog/terms", methods=["GET"])
@user_middleware
def get_catalog_terms(database_id: UUID):
    """Get catalog terms for a database."""
    database, error_response = _get_catalog_database(database_id)
    if error_response:
        return error_response

    limit = int(request.args.get("limit", 50))

    terms = (
        g.session.query(Term).filter(Term.database_id == database.id).limit(limit).all()
    )

    return jsonify([term.to_dict() for term in terms])


@api.route("/databases/<uuid:database_id>/catalog/terms", methods=["POST"])
@user_middleware
def create_catalog_term(database_id: UUID):
    """Create a new catalog term."""
    database, error_response = _get_catalog_database(database_id)
    if error_response:
        return error_response

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a valid JSON object"}), 400
    required_fields = ["name", "definition"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields: name, definition"}), 400

    # Check if term with same name already exists
    existing_term = (
        g.session.query(Term)
        .filter(Term.database_id == database.id, Term.name.ilike(data["name"]))
        .first()
    )

    if existing_term:
        return jsonify({"error": "Term with this name already exists"}), 409

    new_term = Term(
        name=data["name"],
        definition=data["definition"],
        database_id=database.id,
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


@api.route("/databases/<uuid:database_id>/catalog/tags", methods=["GET"])
@user_middleware
def get_catalog_tags(database_id: UUID):
    """Get all available tags for a database."""
    database, error_response = _get_catalog_database(database_id)
    if error_response:
        return error_response

    tags = g.session.query(AssetTag).filter(AssetTag.database_id == database.id).all()

    return jsonify([tag.to_dict() for tag in tags])


@api.route("/databases/<uuid:database_id>/catalog/tags", methods=["POST"])
@user_middleware
def create_catalog_tag(database_id: UUID):
    """Create a new tag."""
    database, error_response = _get_catalog_database(database_id)
    if error_response:
        return error_response

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a valid JSON object"}), 400

    required_fields = ["name"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required field: name"}), 400

    # Check if tag with same name already exists
    existing_tag = (
        g.session.query(AssetTag)
        .filter(AssetTag.database_id == database.id, AssetTag.name.ilike(data["name"]))
        .first()
    )

    if existing_tag:
        return jsonify({"error": "Tag with this name already exists"}), 409

    new_tag = AssetTag(
        name=data["name"],
        description=data.get("description"),
        database_id=database.id,
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

    current_state = get_sync_state(database_id)
    if current_state["sync_status"] == "syncing":
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
    """Get the current sync status for a database from in-memory state."""
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

    # Get sync state from in-memory storage
    from back.sync_state import get_sync_state

    state = get_sync_state(database_id)

    return jsonify(
        {
            "sync_status": state["sync_status"],
            "sync_progress": state["sync_progress"],
            "sync_error": state["sync_error"],
            "updated_at": state["updated_at"],
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


@api.route("/databases/<uuid:database_id>/github/settings", methods=["GET"])
@user_middleware
def get_database_github_settings(database_id: UUID):
    database = g.session.query(Database).filter(Database.id == database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    if not _user_can_manage_database(database):
        return jsonify({"error": "Access denied"}), 403

    integration = get_github_integration(g.session, database.id)
    return jsonify(_github_settings_payload(integration))


@api.route("/databases/<uuid:database_id>/github/settings", methods=["PUT"])
@user_middleware
def update_database_github_settings(database_id: UUID):
    database = g.session.query(Database).filter(Database.id == database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    if not _user_can_manage_database(database):
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json(silent=True) or {}

    integration = get_github_integration(g.session, database.id)
    if not integration:
        integration = GithubIntegration(databaseId=database.id)
        g.session.add(integration)

    if "repo_owner" in data or "repo_name" in data:
        new_owner = data.get("repo_owner") or None
        new_name = data.get("repo_name") or None
        integration.repo_owner = new_owner
        integration.repo_name = new_name
        if new_owner and new_name:
            integration.default_branch = (
                data.get("default_branch") or integration.default_branch
            )
        else:
            integration.default_branch = None

    elif "default_branch" in data:
        integration.default_branch = (
            data.get("default_branch") or integration.default_branch
        )

    g.session.flush()

    return jsonify(_github_settings_payload(integration))


@api.route("/databases/<uuid:database_id>/github/oauth/start", methods=["POST"])
@user_middleware
def start_database_github_oauth(database_id: UUID):
    database = g.session.query(Database).filter(Database.id == database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    if not _user_can_manage_database(database):
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json(silent=True) or {}
    redirect_uri = data.get("redirectUri")
    if not redirect_uri:
        return jsonify({"error": "redirectUri is required"}), 400

    try:
        oauth_payload = start_oauth_flow(
            g.session, database.id, g.user.id, redirect_uri
        )
    except GithubIntegrationError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(oauth_payload)


@api.route("/databases/<uuid:database_id>/github/oauth/exchange", methods=["POST"])
@user_middleware
def exchange_database_github_oauth(database_id: UUID):
    database = g.session.query(Database).filter(Database.id == database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    if not _user_can_manage_database(database):
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json(silent=True) or {}
    code = data.get("code")
    state = data.get("state")
    redirect_uri = data.get("redirectUri")
    if not code or not state:
        return jsonify({"error": "code and state are required"}), 400

    try:
        integration = exchange_oauth_code(
            g.session,
            database.id,
            g.user.id,
            code,
            state,
            redirect_uri,
        )
    except GithubIntegrationError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(_github_settings_payload(integration))


@api.route("/databases/<uuid:database_id>/github/repos", methods=["GET"])
@user_middleware
def list_database_github_repos(database_id: UUID):
    database = g.session.query(Database).filter(Database.id == database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    if not _user_can_manage_database(database):
        return jsonify({"error": "Access denied"}), 403

    integration = get_github_integration(g.session, database.id)
    if not integration or not integration.access_token:
        return jsonify({"error": "GitHub integration is not connected"}), 400

    try:
        ensure_valid_access_token(g.session, integration)
    except GithubIntegrationError as exc:
        return jsonify({"error": str(exc)}), 400

    search = request.args.get("search")
    try:
        repositories = list_repositories(integration.access_token, search=search)
    except GithubIntegrationError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"repositories": repositories})


@api.route("/databases/<uuid:database_id>/github/sync-dbt-docs", methods=["POST"])
@user_middleware
def trigger_dbt_docs_sync(database_id: UUID):
    """Trigger background DBT documentation generation for a database."""
    database = g.session.query(Database).filter(Database.id == database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    if not _user_can_manage_database(database):
        return jsonify({"error": "Access denied"}), 403

    integration = get_github_integration(g.session, database.id)
    if not integration or not integration.access_token:
        return jsonify({"error": "GitHub integration is not connected"}), 400

    # Check if sync is already in progress

    dbt = g.session.query(DBT).filter(DBT.database_id == database.id).first()
    if dbt and dbt.sync_status == "generating":
        return jsonify({"error": "DBT documentation sync is already in progress"}), 409

    try:
        run_dbt_generation_background(database.id, get_db_session)
        return jsonify(
            {
                "status": "started",
                "message": "DBT documentation generation started in background",
            }
        ), 202
    except Exception as exc:
        logger.error(
            "Failed to start DBT generation",
            exc_info=True,
            extra={"database_id": str(database_id), "error": str(exc)},
        )
        return jsonify({"error": f"Failed to start generation: {str(exc)}"}), 500


@api.route("/databases/<uuid:database_id>/github/dbt-sync-status", methods=["GET"])
@user_middleware
def get_dbt_sync_status(database_id: UUID):
    """Get DBT documentation sync status for a database."""
    database = g.session.query(Database).filter(Database.id == database_id).first()
    if not database:
        return jsonify({"error": "Database not found"}), 404

    if not _user_can_manage_database(database):
        return jsonify({"error": "Access denied"}), 403

    dbt = g.session.query(DBT).filter(DBT.database_id == database.id).first()

    # Return default values if DBT record doesn't exist yet
    if not dbt:
        return jsonify(
            {
                "status": "idle",
                "last_synced_at": None,
                "generation_started_at": None,
                "commit_hash": None,
                "error": None,
            }
        )

    return jsonify(
        {
            "status": dbt.sync_status,
            "last_synced_at": (
                dbt.last_synced_at.isoformat() if dbt.last_synced_at else None
            ),
            "generation_started_at": (
                dbt.generation_started_at.isoformat()
                if dbt.generation_started_at
                else None
            ),
            "commit_hash": dbt.last_commit_hash,
            "error": dbt.generation_error,
        }
    )


# Document API routes
@api.route("/databases/<uuid:database_id>/documents", methods=["GET"])
@user_middleware
def list_documents(database_id: UUID):
    """List all documents for a database."""
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

    # Check if we should include archived documents
    include_archived = request.args.get("includeArchived", "false").lower() == "true"

    query = g.session.query(Document).filter(
        Document.database_id == database_id,
        Document.deleted == False,  # noqa: E712
    )

    # Filter out archived documents by default
    if not include_archived:
        query = query.filter(Document.archived == False)  # noqa: E712

    documents = query.order_by(Document.updatedAt.desc()).all()

    return jsonify([doc.to_dict() for doc in documents])


@api.route("/documents/<uuid:document_id>", methods=["GET"])
@user_middleware
def get_document(document_id: UUID):
    """Get a single document by ID."""
    document = g.session.query(Document).filter_by(id=document_id).first()
    if not document:
        return jsonify({"error": "Document not found"}), 404

    # Don't allow viewing deleted documents
    if document.deleted:
        return jsonify({"error": "Document has been deleted"}), 404

    # Verify user has access through database
    database = g.session.query(Database).filter_by(id=document.database_id).first()
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

    return jsonify(document.to_dict())


@api.route("/documents/<uuid:document_id>", methods=["PUT"])
@user_middleware
def update_document(document_id: UUID):
    """Update a document's content and/or title."""
    document = g.session.query(Document).filter_by(id=document_id).first()
    if not document:
        return jsonify({"error": "Document not found"}), 404

    # Verify user has access through database
    database = g.session.query(Database).filter_by(id=document.database_id).first()
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

    # Track if content changed to create version
    content_changed = False

    if "title" in data:
        document.title = data["title"]

    if "content" in data:
        new_content = data["content"]
        if new_content != document.content:
            document.content = new_content
            content_changed = True

    document.updated_by = g.user.id

    if content_changed:
        # Get the latest version number
        latest_version = (
            g.session.query(DocumentVersion)
            .filter(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.desc())
            .first()
        )

        next_version = (latest_version.version_number + 1) if latest_version else 1

        # Create new version
        version = DocumentVersion(
            document_id=document_id,
            content=document.content,
            version_number=next_version,
            created_by=g.user.id,
            change_description=data.get(
                "change_description",
                f"Edited by {g.user.email}",
            ),
        )
        g.session.add(version)

    g.session.flush()

    return jsonify(document.to_dict())


@api.route("/documents/<uuid:document_id>", methods=["DELETE"])
@user_middleware
def delete_document(document_id: UUID):
    """Soft delete a document."""
    document = g.session.query(Document).filter_by(id=document_id).first()
    if not document:
        return jsonify({"error": "Document not found"}), 404

    # Verify user has access through database
    database = g.session.query(Database).filter_by(id=document.database_id).first()
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

    # Soft delete - just mark as deleted
    document.deleted = True
    document.updated_by = g.user.id
    g.session.flush()

    return jsonify({"success": True})


@api.route("/documents/<uuid:document_id>/versions", methods=["GET"])
@user_middleware
def get_document_versions(document_id: UUID):
    """Get version history for a document."""
    document = g.session.query(Document).filter_by(id=document_id).first()
    if not document:
        return jsonify({"error": "Document not found"}), 404

    # Verify user has access through database
    database = g.session.query(Database).filter_by(id=document.database_id).first()
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

    versions = (
        g.session.query(DocumentVersion)
        .filter(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_number.desc())
        .all()
    )

    return jsonify([version.to_dict() for version in versions])


@api.route("/documents/<uuid:document_id>/archive", methods=["POST"])
@user_middleware
def archive_document(document_id: UUID):
    """Archive or unarchive a document."""
    document = g.session.query(Document).filter_by(id=document_id).first()
    if not document:
        return jsonify({"error": "Document not found"}), 404

    # Verify user has access through database
    database = g.session.query(Database).filter_by(id=document.database_id).first()
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
    archived = data.get("archived", True)  # Default to archive if not specified

    document.archived = archived
    document.updated_by = g.user.id
    g.session.flush()

    return jsonify(document.to_dict())
