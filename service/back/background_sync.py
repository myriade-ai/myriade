"""
Background task runner for database metadata synchronization.

This module provides threading support for running metadata sync operations
in the background, updating database sync status, and emitting real-time
progress events via SocketIO.
"""

import logging
import threading
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from back.catalog_events import (
    emit_sync_completed,
    emit_sync_failed,
    emit_sync_progress,
)
from models import Database

logger = logging.getLogger(__name__)


def run_metadata_sync_background(
    database_id: UUID,
    session_factory,
):
    """
    Run metadata sync in a background thread.

    Args:
        database_id: UUID of the database to sync
        session_factory: Function that returns a new SQLAlchemy session
        socketio: Optional SocketIO instance for emitting progress events
    """

    def sync_task():
        """The actual sync task that runs in the background thread."""
        from back.utils import (
            get_tables_metadata_from_catalog,
            merge_tables_metadata,
            sync_database_metadata_to_assets,
        )

        # Timeout configuration (30 minutes)
        SYNC_TIMEOUT_SECONDS = 30 * 60

        # Create a new session for this thread
        session: Session = session_factory()

        try:
            # Get the database record
            database = session.query(Database).filter_by(id=database_id).first()
            if not database:
                logger.error(f"Database {database_id} not found")
                return

            # Set initial status and record start time
            sync_start_time = datetime.utcnow()
            database.sync_status = "syncing"
            database.sync_progress = 0
            database.sync_started_at = sync_start_time
            database.sync_error = None
            session.commit()

            emit_sync_progress(
                database.id,
                stage="metadata",
                current=0,
                total=0,
                progress=0,
                message="Starting metadata sync",
            )

            # Create data warehouse instance
            data_warehouse = database.create_data_warehouse(session=session)

            # Track last commit to batch commits
            last_commit_count = 0
            last_progress_percent = -1  # Track last emitted progress to throttle
            COMMIT_BATCH_SIZE = 500  # Commit every 500 tables
            PROGRESS_UPDATE_INTERVAL = 5  # Emit progress every 5% change

            # Define progress callback to update status
            def progress_callback(current: int, total: int, table_name: str):
                """Update progress in database."""
                nonlocal last_commit_count, last_progress_percent

                # Check for timeout
                elapsed_seconds = (datetime.utcnow() - sync_start_time).total_seconds()
                if elapsed_seconds > SYNC_TIMEOUT_SECONDS:
                    timeout_mins = SYNC_TIMEOUT_SECONDS / 60
                    error_msg = f"Sync timeout exceeded ({timeout_mins:.0f} minutes)"
                    logger.error(
                        f"Timeout during metadata sync for {database_id}: {error_msg}"
                    )
                    raise TimeoutError(error_msg)

                if total > 0:
                    # Metadata loading represents 0-80% of total progress
                    metadata_progress = int((current / total) * 80)
                    database.sync_progress = metadata_progress

                    # Batch commits: only commit every 500 tables or on last item
                    if (
                        current - last_commit_count >= COMMIT_BATCH_SIZE
                        or current == total
                    ):
                        session.commit()
                        last_commit_count = current

                    # Only emit socket progress if
                    # progress percentage changed by interval
                    # or if this is the last table
                    if (
                        current == total
                        or metadata_progress - last_progress_percent
                        >= PROGRESS_UPDATE_INTERVAL
                    ):
                        emit_sync_progress(
                            database.id,
                            stage="metadata",
                            current=current,
                            total=total,
                            progress=metadata_progress,
                            message=table_name,
                        )
                        last_progress_percent = metadata_progress

                    logger.info(
                        f"Metadata sync progress: {current}/{total} "
                        f"({metadata_progress}%) - {table_name}"
                    )
                else:
                    emit_sync_progress(
                        database.id,
                        stage="metadata",
                        current=current,
                        total=total,
                        progress=0,
                        message=table_name,
                    )
                    logger.info(
                        f"Metadata sync progress: {current}/{total} (0%) - {table_name}"
                    )

            # Load new metadata with progress tracking
            logger.info(f"Starting metadata load for database {database_id}")
            new_metadata = data_warehouse.load_metadata(
                progress_callback=progress_callback
            )

            if not new_metadata:
                raise ValueError("No metadata returned from data warehouse")

            # Get existing catalog metadata to preserve existing data
            existing_catalog_meta = get_tables_metadata_from_catalog(
                database.id, session=session
            )

            # Merge existing and new metadata
            merged_metadata = merge_tables_metadata(existing_catalog_meta, new_metadata)

            # Sync to catalog/assets (commits happen in batches within this function)
            logger.info(f"Syncing {len(merged_metadata)} tables to catalog")

            # Create a progress callback for catalog sync
            # Maps 0-100% catalog progress to 80-100% overall progress
            catalog_last_progress_percent = 80  # Start at 80 since metadata was 0-80

            def catalog_progress_callback(current: int, total: int, message: str):
                """Progress callback for catalog sync phase (80-100%)."""
                nonlocal catalog_last_progress_percent

                # Check for timeout
                elapsed_seconds = (datetime.utcnow() - sync_start_time).total_seconds()
                if elapsed_seconds > SYNC_TIMEOUT_SECONDS:
                    timeout_mins = SYNC_TIMEOUT_SECONDS / 60
                    error_msg = f"Sync timeout exceeded ({timeout_mins:.0f} minutes)"
                    logger.error(
                        f"Timeout during catalog sync for {database_id}: {error_msg}"
                    )
                    raise TimeoutError(error_msg)

                if total > 0:
                    # Map catalog progress to 80-100% range
                    # Formula: 80 + (catalog_completion * 20)
                    catalog_completion = current / total
                    overall_progress = int(80 + (catalog_completion * 20))
                    database.sync_progress = overall_progress

                    # Only emit socket progress if progress
                    # percentage changed by interval
                    # or if this is the last item
                    if (
                        current == total
                        or overall_progress - catalog_last_progress_percent
                        >= PROGRESS_UPDATE_INTERVAL
                    ):
                        emit_sync_progress(
                            database.id,
                            stage="catalog",
                            current=current,
                            total=total,
                            progress=overall_progress,
                            message=message,
                        )
                        catalog_last_progress_percent = overall_progress

                    logger.info(
                        f"Catalog sync progress: {current}/{total} "
                        f"({overall_progress}%) - {message}"
                    )
                else:
                    emit_sync_progress(
                        database.id,
                        stage="catalog",
                        current=current,
                        total=total,
                        progress=database.sync_progress,
                        message=message,
                    )
                    logger.info(
                        f"Catalog sync progress: {current}/{total}"
                        f" ({database.sync_progress}%) - {message}"
                    )

            result = sync_database_metadata_to_assets(
                database.id,
                merged_metadata,
                session=session,
                progress_callback=catalog_progress_callback,
            )

            # Mark as completed
            database.sync_status = "completed"
            database.sync_progress = 100
            database.sync_completed_at = datetime.utcnow()
            session.commit()

            emit_sync_progress(
                database.id,
                stage="catalog",
                current=result.get("synced_count", 0),
                total=result.get("synced_count", 0),
                progress=100,
                message="Sync completed",
            )
            emit_sync_completed(
                database.id,
                result.get("created_count", 0),
                result.get("updated_count", 0),
            )

            logger.info(
                f"Metadata sync completed for database {database_id}. "
                f"Synced {result.get('synced_count', 0)} assets."
            )

        except Exception as e:
            logger.error(
                f"Error during metadata sync for database {database_id}: {e}",
                exc_info=True,
            )

            # Mark as failed
            try:
                database = session.query(Database).filter_by(id=database_id).first()
                if database:
                    database.sync_status = "failed"
                    database.sync_error = str(e)
                    database.sync_completed_at = datetime.utcnow()
                    session.commit()
                emit_sync_failed(database_id, error=str(e))
            except Exception as commit_error:
                logger.error(f"Failed to update sync error status: {commit_error}")

        finally:
            session.close()

    # Start the background thread
    thread = threading.Thread(target=sync_task, daemon=True)
    thread.start()
    logger.info(f"Started background metadata sync thread for database {database_id}")
