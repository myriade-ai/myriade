import config  # noqa: F401, I001
import logging

from back.session import get_db_session
from flask import Flask, g, jsonify, request
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix
import telemetry

logger = logging.getLogger(__name__)

socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading",
    # We don't use websockets for now (until we have the need for it)
    transports=["polling"],
)

if config.SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        send_default_pii=True,
        environment=config.ENV,
    )


def create_app():
    app = Flask(__name__)
    # trust 1 proxy in front of you for proto *and* host
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    app.json.sort_keys = False

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

    app.register_blueprint(chat_api)
    app.register_blueprint(back_api)
    app.register_blueprint(query_api)
    app.register_blueprint(auth_api)
    app.register_blueprint(billing_api)

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

    socketio.init_app(app)

    @socketio.on("ping")
    def handle_ping():
        socketio.emit("pong")

    # Start telemetry service for version checking and usage analytics
    telemetry.start_telemetry_service()

    return app
