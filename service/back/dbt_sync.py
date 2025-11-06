"""Background DBT documentation generation and synchronization."""

import logging
import threading
from datetime import datetime, timezone
from typing import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from app import socketio
from back.dbt_environment import DBTEnvironmentError, ensure_dbt_environment
from back.dbt_repository import generate_dbt_docs, get_or_create_dbt
from back.github_manager import (
    ensure_default_workspace,
    get_github_integration,
    get_workspace_commit_hash,
)

logger = logging.getLogger(__name__)


def run_dbt_generation_background(
    database_id: UUID, session_factory: Callable[[], Session]
) -> None:
    """
    Generate DBT docs from shared workspace in a background thread.

    Args:
        database_id: ID of the database to generate docs for
        session_factory: Function that returns a new database session
    """

    def _generate_docs():
        from models import Database

        with session_factory() as session:
            try:
                database = (
                    session.query(Database).filter(Database.id == database_id).first()
                )
                if not database:
                    logger.error(f"Database not found: {database_id}")
                    return

                # Get or create DBT record
                dbt = get_or_create_dbt(session, database_id)

                # Update status to generating
                dbt.sync_status = "generating"
                dbt.generation_started_at = datetime.now(timezone.utc)
                session.commit()

                # Ensure default workspace exists and is up to date
                workspace = ensure_default_workspace(session, database_id)
                if not workspace:
                    raise Exception("Default workspace not found")

                # Get current commit hash
                current_hash = get_workspace_commit_hash(workspace)
                if not current_hash:
                    raise Exception("Failed to get workspace commit hash")

                # Check if we need to regenerate (commit hash changed)
                if dbt.last_commit_hash == current_hash:
                    logger.info(
                        f"DBT docs are up to date for database {database_id}, \
                        skipping generation"
                    )
                    dbt.sync_status = "idle"
                    session.commit()
                    return

                logger.info(
                    f"Starting DBT docs generation for database {database_id} at \
                    commit {current_hash}"
                )

                # Ensure DBT environment is ready
                try:
                    ensure_dbt_environment(workspace, database.engine)
                except DBTEnvironmentError as exc:
                    logger.warning(
                        "Failed to prepare DBT environment",
                        extra={"workspace": str(workspace), "error": str(exc)},
                    )
                    raise DBTEnvironmentError(
                        f"Failed to prepare DBT environment: {exc}"
                    ) from exc

                # Generate DBT docs
                catalog, manifest = generate_dbt_docs(
                    str(workspace),
                    {
                        "engine": database.engine,
                        "details": database.details,
                    },
                )

                # Update DBT record with generated docs and commit hash
                dbt.catalog = catalog
                dbt.manifest = manifest
                dbt.last_commit_hash = current_hash
                dbt.last_synced_at = datetime.now(timezone.utc)
                dbt.sync_status = "completed"
                dbt.generation_error = None
                session.commit()

                logger.info(
                    f"Successfully generated DBT docs for database {database_id}",
                    extra={
                        "commit_hash": current_hash,
                        "catalog_nodes": len(catalog.get("nodes", {})),
                        "manifest_nodes": len(manifest.get("nodes", {})),
                    },
                )

                # Broadcast completion event via SocketIO
                room = f"catalog:database:{database_id}"
                socketio.emit(
                    "dbt:generation:completed",
                    {
                        "database_id": str(database_id),
                        "commit_hash": current_hash,
                        "synced_at": dbt.last_synced_at.isoformat(),
                    },
                    to=room,
                )

            except Exception as exc:
                logger.error(
                    f"Failed to generate DBT docs for database {database_id}",
                    exc_info=True,
                    extra={"error": str(exc)},
                )
                # Update status to failed
                try:
                    dbt = get_or_create_dbt(session, database_id)
                    dbt.sync_status = "failed"
                    dbt.generation_error = str(exc)
                    session.commit()
                except Exception as update_exc:
                    logger.error(
                        f"Failed to update database status: {update_exc}",
                        exc_info=True,
                    )

    # Start background thread
    thread = threading.Thread(target=_generate_docs, daemon=True)
    thread.start()
    logger.info(f"Started background DBT generation for database {database_id}")


def schedule_periodic_dbt_sync(session: Session) -> None:
    """
    Check and schedule DBT docs generation for active databases.

    This function checks all databases with GitHub integration that have
    had recent conversation activity and schedules background doc generation.

    Args:
        session: Database session
    """
    from datetime import timedelta

    from back.session import get_db_session
    from models import DBT, Conversation, Database

    try:
        # Find databases with GitHub integration and recent activity
        recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        active_databases = (
            session.query(Database.id)
            .join(Conversation, Database.id == Conversation.databaseId)
            .filter(Conversation.updatedAt >= recent_cutoff)
            .distinct()
            .all()
        )

        for (database_id,) in active_databases:
            # Check if database has GitHub integration
            integration = get_github_integration(session, database_id)
            if not integration or not integration.access_token:
                continue

            # Check if sync is already in progress
            dbt = session.query(DBT).filter(DBT.database_id == database_id).first()
            if dbt and dbt.sync_status == "generating":
                logger.info(
                    f"Skipping database {database_id} - sync already in progress"
                )
                continue

            logger.info(f"Scheduling periodic DBT sync for database {database_id}")
            run_dbt_generation_background(database_id, get_db_session)

    except Exception as exc:
        logger.error(
            "Error during periodic DBT sync scheduling",
            exc_info=True,
            extra={"error": str(exc)},
        )
