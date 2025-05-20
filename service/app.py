import config  # noqa: F401, I001
import sentry_sdk
from back.session import get_db_session
from flask import Flask, g
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix

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

    from auth.api import api as auth_api
    from back.api import api as back_api
    from back.query import api as query_api
    from chat.api import api as chat_api

    app.register_blueprint(chat_api)
    app.register_blueprint(back_api)
    app.register_blueprint(query_api)
    app.register_blueprint(auth_api)

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

    return app
