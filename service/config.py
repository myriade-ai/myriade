import os

from dotenv import load_dotenv

# Load the appropriate .env file
dotenv_file = os.getenv("DOTENV_FILE", ".env")
load_dotenv(dotenv_file)

# Export all environment variables needed by the application
DATABASE_URL = os.environ["DATABASE_URL"]
WORKOS_API_KEY = os.environ.get("WORKOS_API_KEY", "")
WORKOS_CLIENT_ID = os.environ.get("WORKOS_CLIENT_ID", "")
WORKOS_ORGANIZATION_ID = os.environ.get("WORKOS_ORGANIZATION_ID", "")
HOST = os.environ.get("HOST", "localhost")

# Development mode flag - set to True to use mock authentication
OFFLINE_MODE = os.environ.get("OFFLINE_MODE", "false").lower() == "true"

ENV = os.environ.get("FLASK_ENV", "development")

SENTRY_DSN = "https://b030d37fd0ec1da2e17104283f990f1a@o4508993570275328.ingest.de.sentry.io/4508993573814352"
