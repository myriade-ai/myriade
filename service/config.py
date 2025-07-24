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

WORKOS_CLIENT_ID = os.environ.get("WORKOS_CLIENT_ID", "")
WORKOS_ORGANIZATION_ID = os.environ.get("WORKOS_ORGANIZATION_ID", "")
HOST = os.environ.get("HOST", "localhost:5173")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")

SENTRY_DSN = os.environ.get("SENTRY_DSN")
COOKIE_PASSWORD = os.environ.get("COOKIE_PASSWORD", "")
