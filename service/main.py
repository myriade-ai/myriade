import os

from app import create_app, socketio

app = create_app()


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    socketio.run(app, host="0.0.0.0", port=8080, debug=debug, use_reloader=debug)
