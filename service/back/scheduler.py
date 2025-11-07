"""Background scheduler for periodic tasks."""

import logging
import threading
import time

from back.session import get_db_session

logger = logging.getLogger(__name__)


def start_dbt_sync_scheduler() -> None:
    """
    Start background scheduler for periodic DBT documentation sync.

    This runs in a daemon thread and checks for databases that need
    DBT documentation updates every hour.
    """
    from back.dbt_sync import schedule_periodic_dbt_sync

    def periodic_sync():
        """Background task that runs hourly to sync DBT docs."""
        logger.info("DBT sync scheduler started")

        while True:
            try:
                # Sleep first (1 hour)
                time.sleep(3600)

                logger.info("Running periodic DBT documentation sync")
                with get_db_session() as session:
                    schedule_periodic_dbt_sync(session)

            except Exception as exc:
                logger.error(
                    "Error in periodic DBT sync scheduler",
                    exc_info=True,
                    extra={"error": str(exc)},
                )
                # Continue running despite errors

    thread = threading.Thread(
        target=periodic_sync, daemon=True, name="DBTSyncScheduler"
    )
    thread.start()
    logger.info("DBT sync scheduler thread started")
