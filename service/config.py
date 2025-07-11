import os

from dotenv import load_dotenv

# Load the appropriate .env file
dotenv_file = os.environ["DOTENV_FILE"]
load_dotenv(dotenv_file)

# Export all environment variables needed by the application
DATABASE_URL = os.environ["DATABASE_URL"]
WORKOS_CLIENT_ID = os.environ.get("WORKOS_CLIENT_ID", "")
WORKOS_ORGANIZATION_ID = os.environ.get("WORKOS_ORGANIZATION_ID", "")
HOST = os.environ.get("HOST", "localhost:5173")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")

ENV = os.environ.get("FLASK_ENV", "development")

SENTRY_DSN = os.environ.get("SENTRY_DSN")
COOKIE_PASSWORD = os.environ.get("COOKIE_PASSWORD", "")
