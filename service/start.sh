#!/bin/bash

# Check if environment argument is provided
if [ -z "$1" ]; then
    echo "Please specify environment: dev or test or prod"
    echo "Usage: ./start.sh [dev|test|prod]"
    exit 1
fi

# Set the environment file name
if [ "$1" = "dev" ]; then
    export DOTENV_FILE=".env.dev"
elif [ "$1" = "test" ]; then
    export DOTENV_FILE=".env.test"
elif [ "$1" = "prod" ]; then
    export DOTENV_FILE=".env"
else
    echo "Invalid environment. Choose 'dev' or 'test' or 'prod'"
    exit 1
fi

uv run alembic upgrade head

# Start the server based on environment
if [ "$1" = "prod" ]; then
    # Production mode with Gunicorn
    echo "Starting server in production mode"
    exec uv run gunicorn wsgi:application --config gunicorn_conf.py
else
    # Development mode with Flask
    export FLASK_APP=app.py
    export FLASK_DEBUG=true
    uv run flask run --host=0.0.0.0 --port=8080
fi
