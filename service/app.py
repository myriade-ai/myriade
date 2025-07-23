import config  # noqa: F401, I001
import logging
import sys
import os
import pathlib
import time
import urllib.request
from back.session import get_db_session
from flask import Flask, g, jsonify, request, send_from_directory
from flask_socketio import SocketIO
import webview
import threading
from werkzeug.middleware.proxy_fix import ProxyFix
import telemetry

from alembic import command
from alembic.config import Config

logger = logging.getLogger(__name__)

socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading",
    transports=["polling"],
)

if config.SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        send_default_pii=True,
        environment=config.ENV,
    )


def upgrade_db_to_head():
    here = pathlib.Path(__file__).parent
    alembic_cfg = Config(here / "alembic.ini")
    alembic_cfg.set_main_option(
        "script_location",
        str(here / "migrations"),
    )
    command.upgrade(alembic_cfg, "head")
    logging.info("✓ Database migrated (alembic head)")


def create_app():
    # run Alembic once per launch
    upgrade_db_to_head()
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
            f"{error_type} occurred in {endpoint}: {str(e)}",
            exc_info=True,
            extra={
                "endpoint": endpoint,
                "method": request.method,
                "url": request.url,
                "user_email": getattr(getattr(g, "user", None), "email", "anonymous"),
                "user_agent": request.headers.get("User-Agent", ""),
                "ip_address": request.remote_addr,
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

    # serve SPA entry point
    @app.route("/")
    def index():
        static_path = app.static_folder
        if not os.path.exists(static_path):
            return "Static folder does not exist!", 500

        index_path = os.path.join(static_path, "index.html")
        return app.send_static_file(index_path)

    @app.route("/<path:path>")
    def static_files(path):
        """Serve anything that isn't under /api from the bundled static dir,
        then fall back to index.html for SPA routes."""
        try:
            return send_from_directory(app.static_folder, path)
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

    @socketio.on("ping")
    def handle_ping():
        socketio.emit("pong")

    # Start telemetry service for version checking and usage analytics
    telemetry.start_telemetry_service()

    return app


def run_app():
    app = create_app()
    app.run(host="0.0.0.0", port=4000, debug=False)


if __name__ == "__main__":
    t = threading.Thread(target=run_app, daemon=True)
    t.start()
    # Wait for Flask instead of a blind sleep

    def wait_until_up(url, timeout):
        start = time.time()
        while time.time() - start < timeout:
            try:
                urllib.request.urlopen(url, timeout=1)
                return True
            except Exception:
                time.sleep(0.3)
        return False

    if not wait_until_up("http://localhost:4000", 60):
        print("Flask failed to start in time")
        sys.exit(1)

    webview.create_window(
        "Myriade BI",
        "http://localhost:4000",  # load the real front-page
        width=1280,
        height=800,
    )
    webview.start(debug=True)
    sys.exit()
