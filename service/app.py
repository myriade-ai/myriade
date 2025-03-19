import sentry_sdk
from flask import Flask, g
from flask_socketio import SocketIO

import config  # noqa: F401
from back.session import Session

socketio = SocketIO(cors_allowed_origins="*")

sentry_sdk.init(
    dsn="https://b030d37fd0ec1da2e17104283f990f1a@o4508993570275328.ingest.de.sentry.io/4508993573814352",
    send_default_pii=True,
    environment=config.ENV,
)


def create_app():
    app = Flask(__name__)

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
    def create_session():
        g.session = Session()

    @app.teardown_appcontext
    def close_session(exception=None):
        if hasattr(g, "session"):
            if exception:
                g.session.rollback()
            g.session.close()

    socketio.init_app(app)

    return app
