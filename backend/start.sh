#!/bin/bash
# FinShield AI — Production startup script
# Runs Alembic migrations before starting the server.
set -e

echo "=== FinShield AI Starting ==="
echo "Running database migrations..."
python -m alembic upgrade head

echo "Migrations complete. Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
