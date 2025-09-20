#!/bin/bash
set -e

# Fly.io startup script for Myriade
echo "🚀 Starting Myriade on Fly.io..."

# Signal handling for graceful shutdown
cleanup() {
    echo "🛑 Shutting down gracefully..."
    kill -TERM "$child" 2>/dev/null || true
    wait "$child"
    exit
}
trap cleanup SIGTERM SIGINT

# Use fly.io environment configuration
export DOTENV_FILE=".env.fly"

# Check if we're using SQLite (default) or external database
if [[ "$DATABASE_URL" == sqlite* ]]; then
    echo "📦 Using SQLite database"
    # Ensure data directory exists
    mkdir -p /app/data
else
    echo "🗄️ Using external database: ${DATABASE_URL%%://*}"
fi

# Run database migrations
echo "🔧 Running database migrations..."
uv run alembic upgrade head

# Start the application with Gunicorn
echo "🌐 Starting Myriade server..."
echo "📍 Application will be available on the assigned Fly.io URL"

# Start Gunicorn in the background so we can handle signals
uv run gunicorn wsgi:application --config gunicorn_conf.py &
child=$!

# Wait for the background process
wait "$child"