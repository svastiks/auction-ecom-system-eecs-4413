#!/bin/bash
set -e

echo " Starting backend service..."

# Wait for database to be ready
echo " Waiting for database to be ready..."
until python -c "
from psycopg import connect
import os
db_url = os.environ.get('DATABASE_URL', 'postgresql://auction_user:auction_password@postgres:5432/auction_db')
try:
    with connect(db_url) as conn:
        pass
    exit(0)
except Exception:
    exit(1)
" 2>/dev/null; do
  echo "Database is unavailable - sleeping"
  sleep 1
done

echo " Database is ready!"

# Run database migrations
echo " Running database migrations..."
python db_commands.py init-db

# Start the application
echo " Starting FastAPI application..."
exec "$@"

