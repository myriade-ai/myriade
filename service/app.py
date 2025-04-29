import sentry_sdk
from flask import Flask, g
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix

import config  # noqa: F401
from back.session import SessionLocal

socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading",
    # We don't use websockets for now (until we have the need for it)
    transports=["polling"],
)


if config.ENV != "development":
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

    from ai.api import api as ai_api
    from auth.api import api as auth_api
    from back.api import api as back_api
    from chat.api import api as chat_api

    app.register_blueprint(chat_api)
    app.register_blueprint(back_api)
    app.register_blueprint(ai_api)
    app.register_blueprint(auth_api)

    @app.before_request
    def _open_db_session():
        g.session = SessionLocal()

    @app.after_request
    def _commit_or_rollback(response):
        try:
            # Commit only if *our* code did not raise – i.e. status < 400
            if response.status_code < 400:
                g.session.commit()
            else:
                g.session.rollback()
        finally:
            g.session.close()
        return response

    @app.teardown_request
    def _teardown_request(exception):
        # Handles unhandled exceptions (500 stacktrace, etc.)
        if exception is not None and hasattr(g, "session"):
            g.session.rollback()
            g.session.close()

    socketio.init_app(app)

    @socketio.on("ping")
    def handle_ping():
        socketio.emit("pong")

    return app
