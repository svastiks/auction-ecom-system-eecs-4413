# Setup for Auction E-commerce System

This document describes the database setup and schema for the auction e-commerce system.

## Overview

The system uses PostgreSQL as the database with SQLAlchemy ORM and Alembic for migrations. The database schema includes all necessary tables for a complete auction e-commerce platform.



First, clone the repository and start Docker containers:

```bash
git clone https://github.com/svastiks/auction-ecom-system-eecs-4413.git
```

Start Docker containers
```bash
docker-compose up --build
```
* Backend will be available at: http://localhost:8000
* PostgreSQL will be available at: localhost:5434


Check running containers
```bash
docker ps
```
Expected output:
```bash
CONTAINER ID   IMAGE                                   STATUS       PORTS
f381795e7b9f   auction-ecom-system-eecs-4413-backend  Up           0.0.0.0:8000->8000/tcp
abe4291b927d   postgres:15                             Up           0.0.0.0:5434->5432/tcp
```

Enter the backend container
```bash
docker exec -it auction_backend /bin/bash
```


## Database Schema

### Core Tables

1. **Users and Authentication**
   - `users` - User accounts with authentication
   - `addresses` - User shipping addresses
   - `auth_sessions` - Active user sessions
   - `password_reset_tokens` - Password reset functionality

2. **Catalogue Management**
   - `categories` - Product categories (hierarchical)
   - `catalogue_items` - Products/items for sale
   - `item_images` - Product images

3. **Auction System**
   - `auctions` - Auction listings
   - `bids` - User bids on auctions

4. **Order Management**
   - `orders` - Purchase orders
   - `payments` - Payment processing
   - `receipts` - Order receipts
   - `shipments` - Shipping information

5. **Event Logging**
   - `event_log` - System event tracking

## Setup Instructions

### Prerequisites

1. PostgreSQL database running on localhost:5434
2. Database: `auction_db`
3. User: `auction_user`
4. Password: `auction_password`

### Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Initialize the database:
   ```bash
   python db_commands.py init-db
   ```

### Database Commands

Use the `db_commands.py` script for database operations:

```bash
# Initialize database (create all tables)
python db_commands.py init-db

# Create a new migration
python db_commands.py create "Add new feature"

# Run migrations
python db_commands.py migrate

# Show migration history
python db_commands.py history

# Show current revision
python db_commands.py current

# Downgrade by one revision
python db_commands.py downgrade
```

### Manual Alembic Commands

You can also use Alembic directly:

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Run migrations
alembic upgrade head

# Show history
alembic history

# Show current revision
alembic current
```

## Database Configuration

The database connection is configured in `app/core/config.py`:

```python
DATABASE_URL = "postgresql://auction_user:auction_password@localhost:5434/auction_db"
```

## Model Structure

All SQLAlchemy models are organized in the `app/models/` directory:

- `user.py` - User-related models
- `catalogue.py` - Product catalogue models
- `auction.py` - Auction system models
- `order.py` - Order management models
- `event_log.py` - Event logging model

## Security Features

- Password hashing with bcrypt
- Password reset tokens with expiration
- Input validation and constraints

## Development Notes

- The system uses psycopg3 (psycopg) as the PostgreSQL adapter
- All migrations are auto-generated from model changes
- The database URL is automatically converted to use the psycopg driver
- Models are imported in `app/models/__init__.py` to ensure they're registered with SQLAlchemy
