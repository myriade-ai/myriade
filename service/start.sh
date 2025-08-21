#!/bin/bash
set -e

# Signal handling
cleanup() {
    echo "🛑 Shutting down..."
    kill -TERM "$child" 2>/dev/null || true
    wait "$child"
    exit
}
trap cleanup SIGTERM SIGINT

# Check if environment argument is provided
if [ -z "$1" ]; then
    echo "Please specify environment: dev or test or prod"
    echo "Usage: ./start.sh [dev|test|prod]"
    exit 1
fi

# Run OS-specific setup only in dev or test environments
if [ "$1" = "dev" ] || [ "$1" = "test" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - export Homebrew library paths for Cairo
        export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"
        export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
        echo "🍎 Detected macOS - Setting up Homebrew Cairo paths"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "🐧 Linux might work"
    else
        echo "⚠️  Unknown OS type: $OSTYPE - Using default paths"
    fi
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
    echo "🚀 Starting server in production mode"
    echo "🌐 Myriade BI will be available at http://localhost:8080"
    exec uv run gunicorn wsgi:application --config gunicorn_conf.py
else
    # Development mode with Socket.IO
    export FLASK_DEBUG=true
    echo "🚀 Starting server in development mode"
    echo "🌐 Myriade BI will be available at http://localhost:8080"
    uv run python main.py
fi