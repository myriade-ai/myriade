#!/bin/bash

# Check if environment argument is provided
if [ -z "$1" ]; then
    echo "Please specify environment: dev or test"
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

# Default values
export FLASK_APP=app.py
export FLASK_DEBUG=true

# Run migrations and start the Flask server
# python-dotenv will automatically load the correct .env file based on DOTENV_FILE
alembic upgrade head
flask run --host=0.0.0.0 --port=4000
