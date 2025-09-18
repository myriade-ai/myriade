import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import g

from back.session import get_db_session
from back.utils import sync_database_metadata_to_assets
from models import Database

logger = logging.getLogger(__name__)

scheduler = None
app_instance = None


def sync_all_databases_metadata():
    """
    Sync metadata for all databases to catalog.
    This job runs every 5 minutes to ensure schemas are not empty.
    """
    logger.info("Starting scheduled database metadata sync")

    if app_instance is None:
        logger.error("App instance not available for scheduler")
        return

    with app_instance.app_context():
        session = None
        try:
            session = get_db_session()
            session.begin()
            g.session = session

            databases = session.query(Database).all()

            for database in databases:
                try:
                    logger.info(f"Syncing metadata for database {database.name}")

                    data_warehouse = database.create_data_warehouse()
                    metadata = data_warehouse.load_metadata()

                    if metadata:
                        sync_database_metadata_to_assets(database.id, metadata)
                        logger.info(f"Successfully synced metadata for {database.name}")
                    else:
                        logger.warning(f"No metadata found for {database.name}")

                except Exception as e:
                    logger.error(f"Failed to sync {database.name}: {str(e)}")
                    session.rollback()
                    session.begin()
                    g.session = session
                    continue

            session.commit()
            logger.info("Completed scheduled database metadata sync")

        except Exception as e:
            logger.error(f"Error during sync: {str(e)}")
            if session:
                session.rollback()
        finally:
            if session:
                session.close()


def start_scheduler(app):
    """Initialize and start the background scheduler"""
    global scheduler, app_instance

    if scheduler is not None:
        logger.warning("Scheduler already started")
        return

    app_instance = app
    logger.info("Starting background scheduler")

    # Run sync immediately at startup
    logger.info("Running initial database metadata sync at startup")
    sync_all_databases_metadata()

    scheduler = BackgroundScheduler()

    # Add job to sync database metadata every 30 minutes
    scheduler.add_job(
        func=sync_all_databases_metadata,
        trigger=IntervalTrigger(minutes=30),
        id="sync_database_metadata",
        name="Sync database metadata to catalog",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Background scheduler started successfully")


def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler

    if scheduler is not None:
        logger.info("Stopping background scheduler")
        scheduler.shutdown()
        scheduler = None
        logger.info("Background scheduler stopped")
