#!/bin/bash
# FinShield AI — Production startup script
# Runs Alembic migrations before starting the server
# Optimized for AWS ECS/Fargate deployment
set -e

echo "=== FinShield AI Starting ==="
echo "Environment: ${APP_ENV:-production}"
echo "Python version: $(python --version)"

# Wait for database to be ready (important for AWS RDS)
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for database..."
    MAX_RETRIES=30
    RETRY_COUNT=0

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if python -c "import asyncio; from app.db.session import engine; asyncio.run(engine.connect())" 2>/dev/null; then
            echo "✓ Database is ready"
            break
        fi
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "  Waiting... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 2
    done

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "✗ Database not ready after 60 seconds. Check connection string."
        exit 1
    fi
fi

# Run database migrations
echo "Running database migrations..."
if python -m alembic upgrade head; then
    echo "✓ Migrations complete"
else
    echo "✗ Migrations failed"
    exit 1
fi

# Calculate workers based on available CPUs
WORKERS=${WORKERS:-$(nproc || echo 2)}
echo "Starting server with $WORKERS worker processes..."

# Start server with optimized settings
exec uvicorn \
    app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --loop uvloop \
    --timeout-keep-alive 5 \
    --timeout-notify 30 \
    --access-log
