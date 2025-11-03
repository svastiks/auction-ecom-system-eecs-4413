# Auction E-commerce System

## Tech Stack

- Pyhton/FastAPI --> **Backend services**
- Postgres --> **Database**
- Alembic --> **Database Migrations**
- OpenAPI/Swagger Docs --> **API Documentation**
- React, TypeScript, TailwindCSS --> **Frontend service**

## Note for TA/Grader:
```
- The server and client-side implementations submitted as a zip file on eclass --> ✅

- A readme file with installation instructions --> this is the README file with instructions ✅

- A script file with curl or Postman test cases; the test cases should test for robustness (user wrong
inputs) as well --> postman collection submitted with the zip ✅

- A SQL file that populates the database (if needed) --> Not needed, we are running migration
during the DockerFile setup, which will initialize the database (populate), the setup instructions
below will elaborate ✅

- An updated design document that explains any changes in the design, testcases, project plan, and
team meeting logs ( You can go beyond 12 pages now) --> submitted on eclass ✅
```

## Postman Testing instructions

The postman collection is attached in the zip file, that .json will need to be imported into your postman in order to view it.

The collection automatically sets many variables as collection variables. For example, the accessToken, addressId, categoryId etc.
A javascript script was added under the scripts section in order to set these variables and will help with testing.

To give a working example, when the /auth/login endpoint is hit we generate an access_token, this is required to run AUTH protected endpoints.
We set the access_token as accessToken and ensure a smooth testing experience is provided (avoiding the need to manually set it)

## Setup Instructions
**Step 1: Clone the repository and cd into backend:**
```bash
git clone https://github.com/svastiks/auction-ecom-system-eecs-4413.git

cd backend
```
**Pre-req for step 2:**
- `brew install docker`
- Then, download the Docker application: https://www.docker.com/products/docker-desktop

**Finally, step 2: Start the Docker containers**
Note: The Dockerfile is built such that it will install the Python dependencies and run the migration to populate the database (so no manual SQL script is needed)

```bash
docker-compose up --build
```
* Backend will be available at: http://127.0.0.1:8000
* PostgreSQL will be available at: http://localhost:5434. Config is as follows:
```
 POSTGRES_DB: auction_db
 POSTGRES_USER: auction_user
 POSTGRES_PASSWORD: auction_password

 DATABASE_URL = "postgresql://auction_user:auction_password@localhost:5434/auction_db"
```

Step 3: Ensure containers are running
```bash
docker ps
```
Expected output (along those lines):
```bash
CONTAINER ID   IMAGE                                   STATUS       PORTS
f381795e7b9f   auction-ecom-system-eecs-4413-backend  Up           0.0.0.0:8000->8000/tcp
abe4291b927d   postgres:15                             Up           0.0.0.0:5434->5432/tcp
```

## API Endpoints

Once the application is up and running, this URL for our API documentation: http://localhost:8000/docs#

Screenshot below for reference:
<img width="2161" height="5140" alt="latest_endpoints" src="https://github.com/user-attachments/assets/786507a0-4a6c-4b69-99b5-ba841ddd4952" />

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
