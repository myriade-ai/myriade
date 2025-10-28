import eventlet

# Apply eventlet monkey patch BEFORE any other imports
eventlet.monkey_patch()


import config  # noqa: E402, F401, I001
import logging  # noqa: E402
from back.session import get_db_session  # noqa: E402
from flask import Flask, g, jsonify, request, send_from_directory  # noqa: E402
from flask_socketio import SocketIO  # noqa: E402
from werkzeug.middleware.proxy_fix import ProxyFix  # noqa: E402
import telemetry  # noqa: E402


# Configure JSON logging
from pythonjsonlogger import jsonlogger  # noqa: E402

handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(name)s %(levelname)s %(message)s", timestamp=True
)
handler.setFormatter(formatter)

logging.basicConfig(level=config.LOG_LEVEL, handlers=[handler])

logger = logging.getLogger(__name__)

socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="eventlet",
)

if config.SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        send_default_pii=True,
        environment=config.ENV,
    )


def initialize_demo_databases():
    """
    Start background sync for demo databases on startup if not already synced.
    This ensures demo databases have their catalog populated without blocking startup.
    """
    from sqlalchemy import and_, exists

    from back.background_sync import run_metadata_sync_background
    from models import Database
    from models.catalog import Asset

    session = get_db_session()
    try:
        databases_without_assets = (
            session.query(Database)
            .filter(
                and_(
                    Database.public,
                    ~exists().where(Asset.database_id == Database.id),
                )
            )
            .all()
        )

        for db in databases_without_assets:
            logger.info(
                f"Starting background sync for demo database: {db.name} (id: {db.id})"
            )

            # Start background sync for this database
            try:
                run_metadata_sync_background(
                    database_id=db.id,
                    session_factory=get_db_session,
                )
                logger.info(f"Background sync started for demo database: {db.name}")
            except Exception as e:
                logger.error(
                    f"Failed to start background sync for {db.name}: {e}",
                    exc_info=True,
                )

        session.commit()
    except Exception as e:
        logger.error(f"Error initializing demo databases: {e}", exc_info=True)
        session.rollback()
    finally:
        session.close()


def create_app():
    # Create app
    app = Flask(__name__, static_folder=config.STATIC_FOLDER)
    # trust 1 proxy in front of you for proto *and* host
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    app.json.sort_keys = False

    socketio.init_app(app)

    # Global error handler for all routes
    @app.errorhandler(Exception)
    def handle_global_exception(e):
        error_type = e.__class__.__name__
        endpoint = request.endpoint or "unknown"

        # Log the error with context
        logger.error(
            "Unhandled exception occurred",
            exc_info=True,
            extra={
                "error_type": error_type,
                "endpoint": endpoint,
                "method": request.method,
                "url": request.url,
                "user_email": getattr(getattr(g, "user", None), "email", "anonymous"),
                "user_agent": request.headers.get("User-Agent", ""),
                "ip_address": request.remote_addr,
                "error_message": str(e),
            },
        )

        # Send to Sentry if configured
        if config.SENTRY_DSN:
            sentry_sdk.capture_exception(e)

        # Return JSON error response
        return jsonify({"error": "An error occurred processing your request"}), 500

    from auth.api import api as auth_api
    from back.api import api as back_api
    from back.query import api as query_api
    from billing.api import api as billing_api
    from chat.api import api as chat_api

    app.register_blueprint(chat_api, url_prefix="/api")
    app.register_blueprint(back_api, url_prefix="/api")
    app.register_blueprint(query_api, url_prefix="/api")
    app.register_blueprint(auth_api, url_prefix="/api")
    app.register_blueprint(billing_api, url_prefix="/api")

    # Register catalog SocketIO handlers (import triggers decorator registration)
    import back.catalog_socketio  # noqa: F401

    if config.ENV != "development":
        # serve SPA entry point
        @app.route("/")
        def index():
            return app.send_static_file("index.html")

        @app.route("/<path:path>")
        def static_files(path):
            """Serve anything that isn't under /api from the bundled static dir,
            then fall back to index.html for SPA routes."""
            try:
                return send_from_directory(app.static_folder, path, conditional=True)
            except Exception:
                return app.send_static_file("index.html")

    @app.before_request
    def _open_db_session():
        g.session = get_db_session()
        g.session.begin()

    @app.teardown_request
    def end_session(exc=None):
        session = g.pop("session", None)
        if not session:
            return
        if exc is None:
            session.commit()
        else:
            session.rollback()
        session.close()

    # Global SocketIO error handler
    @socketio.on_error_default
    def default_error_handler(e):
        logger.error(
            "SocketIO error occurred",
            exc_info=True,
            extra={
                "error_type": e.__class__.__name__,
                "error_message": str(e),
                "user_email": getattr(getattr(g, "user", None), "email", "anonymous"),
            },
        )

        # Send to Sentry if configured
        if config.SENTRY_DSN:
            sentry_sdk.capture_exception(e)

        # Emit error to client
        socketio.emit("error", {"message": "An error occurred processing your request"})

    @socketio.on("ping")
    def handle_ping():
        socketio.emit("pong")

    # Start telemetry service for version checking and usage analytics
    telemetry.start_telemetry_service()

    # Initialize demo databases catalog on startup
    initialize_demo_databases()

    return app
