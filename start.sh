#!/bin/sh
# ========================================
# Animantis — Container Startup Script
# ========================================
# Runs Alembic migrations with retry, then starts the API server.
# Railway PostgreSQL may take a few seconds to become available.

set -e

MAX_RETRIES=5
RETRY_DELAY=3

echo "Animantis: Starting container..."
echo "DATABASE_URL is set: $([ -n "$DATABASE_URL" ] && echo 'yes' || echo 'NO!')"

# Run migrations with retry
echo "Animantis: Running Alembic migrations..."
RETRIES=0
until alembic upgrade head; do
    RETRIES=$((RETRIES + 1))
    if [ "$RETRIES" -ge "$MAX_RETRIES" ]; then
        echo "Animantis: WARNING — Alembic migration failed after $MAX_RETRIES attempts, starting anyway"
        break
    fi
    echo "Animantis: Migration attempt $RETRIES/$MAX_RETRIES failed, retrying in ${RETRY_DELAY}s..."
    sleep $RETRY_DELAY
done

# Start API server
echo "Animantis: Starting Uvicorn on port ${PORT:-8000}..."
exec uvicorn animantis.api.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 2
