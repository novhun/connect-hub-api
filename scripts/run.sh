#!/usr/bin/env bash
set -e

# Move to the script's directory / project root
cd "$(dirname "$0")/.."

PORT="${PORT:-8008}"
HOST="${HOST:-0.0.0.0}"

echo "🚀 Starting Connect-Hub API Server on http://${HOST}:${PORT}..."

# Activate virtualenv if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run database seed if DB does not exist
if [ ! -f "connect_hub.db" ]; then
    echo "🌱 Initializing database schema and seeding demo data..."
    python scripts/seed_data.py
fi

# Run Uvicorn server with auto-reload
exec uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
