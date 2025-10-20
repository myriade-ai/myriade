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

# Infra Configuration
INFRA_URL = os.environ.get("INFRA_URL", "https://infra.myriade.ai")
SENTRY_DSN = os.environ.get("SENTRY_DSN")

# Logging Configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# JWT Configuration for auth tokens
AUTH_CLIENT_ID = os.environ.get("AUTH_CLIENT_ID", "")

# Local Development Authentication
USE_LOCAL_AUTH = os.environ.get("USE_LOCAL_AUTH", "false").lower() == "true"
