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

# Seed categories
echo " Seeding categories..."
python -c "
from psycopg import connect
import os
db_url = os.environ.get('DATABASE_URL', 'postgresql://auction_user:auction_password@postgres:5432/auction_db')
with connect(db_url) as conn:
    with conn.cursor() as cur:
        cur.execute('''
            INSERT INTO categories (category_id, name, description, parent_category_id) VALUES
            ('7b6a2c2b-9c7a-4c9e-bd1c-6c9c4fa3e6a4', 'Electronics', 'Electronics', NULL),
            ('0f4d9c7e-6e8b-4d0c-b7d8-9e0a3c2f7b51', 'Fashion & Apparel', 'Clothing, shoes, and accessories', NULL),
            ('2c1a8f9b-3e2f-45d7-8c6a-1b0d3e9f4a72', 'Home & Garden', 'Home goods, furniture, garden supplies', NULL),
            ('9e3b7a1c-5d2f-49f0-9c84-2a6d8e1f3b90', 'Sports & Outdoors', 'Sports equipment and outdoor gear', NULL),
            ('4a7f2c1e-8b3d-4f6a-92d7-6e1c9a0f2b34', 'Collectibles & Art', 'Collectibles, art, antiques', NULL),
            ('8c2e5a9b-1f7d-4e3a-9b6c-3d0a7f2e1c45', 'Books, Movies & Music', 'Media and entertainment', NULL),
            ('5d1a9c7e-2b4f-4a8e-9f03-7c2e1b6a5d98', 'Automotive', 'Vehicle parts and accessories', NULL),
            ('1e9b3c7a-6d2f-4b0a-8f91-4a7c2e5d1b63', 'Toys & Hobbies', 'Toys, games, hobby supplies', NULL),
            ('c7e2a1b9-3f5d-4a8c-92e1-6b0f4d2a7c53', 'Health & Beauty', 'Personal care and wellness', NULL),
            ('a3f7c2e1-9b5d-4d8a-86c1-2e4a0f7b6d19', 'Other', 'Miscellaneous items', NULL)
            ON CONFLICT (category_id) DO NOTHING;
        ''')
        conn.commit()
print('Categories seeded successfully!')
"

# Start the application
echo " Starting FastAPI application..."
exec "$@"

