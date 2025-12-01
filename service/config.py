import os
import pathlib

from dotenv import load_dotenv

here = pathlib.Path(__file__).parent
# If standalone executable, use .env
dotenv_file = os.environ.get("DOTENV_FILE", here / ".env")
STATIC_FOLDER = os.environ.get("STATIC_FOLDER", "../view/dist")
load_dotenv(dotenv_file)

ENV = os.environ.get("FLASK_ENV", "development")

# Export all environment variables needed by the application
DATABASE_URL = os.environ["DATABASE_URL"]

# SQLite: if database folder does not exist, create it
if DATABASE_URL.startswith("sqlite:///") and ENV != "development":
    # We adapt ~ to the user's home directory
    path = DATABASE_URL.replace("sqlite:///", "")
    if path.startswith("~"):
        path = os.path.expanduser(path)
        DATABASE_URL = "sqlite:///" + path
    # We create the database folder if it does not exist
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent)

HOST = os.environ.get("HOST")

# Warn if HOST is not set in production (may cause OAuth redirect issues)
if ENV == "production" and not HOST:
    import logging

    logging.warning(
        "HOST environment variable is not set. "
        "OAuth redirects may fail if running behind a reverse proxy. "
        "Set HOST to your public URL (e.g., HOST=https://myriade.example.com)"
    )

# Infra Configuration
INFRA_URL = os.environ.get("INFRA_URL", "https://infra.myriade.ai")
SENTRY_DSN = os.environ.get("SENTRY_DSN")

# Organisation access control
ALLOWED_ORGANIZATION_ID = os.environ.get("ORGANIZATION_ID")

# Logging Configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# JWT Configuration for auth tokens
AUTH_CLIENT_ID = os.environ.get("AUTH_CLIENT_ID", "")
