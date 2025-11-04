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

- An updated design document that explains any changes in the design, test cases, project plan, and
team meeting logs ( You can go beyond 12 pages now) --> submitted on eclass ✅
```

## Postman Testing instructions (Very important read)

We built a detailed Postman collection that mimics the real interactions between a buyer and a seller in our bidding system, serving as our primary testing environment.

The collection is organized into multiple folders (/auth, /users, /catalogue, /auction, /orders, /delete_endpoints (to delete at the end, not during testing)), following the logical user flow. Each request uses collection variables—like `accessToken`, `addressId`, `categoryId`, and `itemId`, that are automatically set by scripts after running certain endpoints. For instance, when a user logs in through `/auth/login`, the script extracts the generated `access_token` and saves it as a variable (accessToken), letting all protected requests run seamlessly without manual setup.

During testing, we switch contexts between buyer and seller as needed to reflect real scenarios. For ease of use, please run from the endpoints top to bottom, i.e. auth to orders. This will help you experience the FULL user flow as intended.

For example:

- We first create the buyer and the seller, and then stay logged in as a seller

- Then, we log in as the buyer to create an `address` or `browse auction items`.

- Then, we log in as the seller again to create `categories` or list new `items` for auction.

- After that, we switch back to the buyer to place bids, check bidding status, and complete an order (pay for an order).

This approach ensures we can fully simulate both sides of the marketplace in a consistent, automated way inside Postman, verifying that authentication and endpoint flows all work correctly from end to end.

## Setup Instructions
**Step 1: Clone the repository and cd into backend OR Extract the zip file and then cd into backend**

If you decide to clone the repo, then follow the command below
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
 PORT: 5434

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

<img width="1497" height="1048" alt="image" src="https://github.com/user-attachments/assets/6979c56f-c650-4047-a460-53128341ed59" />

<img width="1470" height="1205" alt="image" src="https://github.com/user-attachments/assets/ed85c4a9-b3bb-4354-b05e-6a1d0f9cf190" />

<img width="1470" height="1095" alt="image" src="https://github.com/user-attachments/assets/44023daf-e107-42fc-81e0-f56dceefb8c2" />

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
