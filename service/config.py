import os

from dotenv import load_dotenv

# Load the appropriate .env file
dotenv_file = os.getenv("DOTENV_FILE", ".env")
load_dotenv(dotenv_file)

# Export all environment variables needed by the application
DATABASE_URL = os.environ["DATABASE_URL"]
WORKOS_API_KEY = os.environ["WORKOS_API_KEY"]
WORKOS_CLIENT_ID = os.environ["WORKOS_CLIENT_ID"]
