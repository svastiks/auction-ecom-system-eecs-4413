# Authentication Service Tests

This directory contains comprehensive tests for the UC1 Authentication Service.

## Test Coverage

### Authentication Tests (`test_auth.py`)
- ✅ **User Registration (3 tests)**
  - Successful signup with valid data
  - Duplicate username rejection
  - Duplicate email rejection
  - Invalid data validation

- ✅ **User Login (3 tests)**
  - Successful login with valid credentials
  - Invalid credentials rejection
  - Inactive user rejection

- ✅ **Password Reset (3 tests)**
  - Successful password reset flow
  - Invalid token rejection
  - Non-existent email handling

- ✅ **Security Tests (3 tests)**
  - Protected endpoint access without auth
  - Invalid token rejection
  - Successful logout

### User Management Tests (`test_users.py`)
- ✅ **Profile Management (3 tests)**
  - Get current user profile
  - Update profile with valid data
  - Duplicate email prevention

- ✅ **Address Management (5 tests)**
  - Create address with default shipping
  - Multiple addresses with default logic
  - Update address
  - Delete address
  - Access control (cannot access other users' addresses)

## Running Tests

### Option 1: Using the test runner script
```bash
cd backend
python run_tests.py
```

### Option 2: Using pytest directly
```bash
cd backend
pytest tests/ -v
```

### Option 3: Run specific test files
```bash
# Run only authentication tests
pytest tests/test_auth.py -v

# Run only user management tests
pytest tests/test_users.py -v
```

## Test Database

Tests use SQLite in-memory database for fast execution and isolation. Each test gets a fresh database state.

## Test Fixtures

- `client`: FastAPI test client
- `db_session`: Database session for each test
- `test_user`: Pre-created test user
- `auth_headers`: Authentication headers for protected endpoints
- `test_user_data`: Sample user data for testing

## Test Categories

### Happy Path Tests
1. Successful user registration
2. Successful login with JWT return
3. Successful password reset flow
4. Address CRUD operations
5. Profile management

### Error Path Tests
1. Duplicate username/email registration
2. Invalid login credentials
3. Expired/invalid reset tokens
4. Unauthorized access attempts
5. Invalid input validation

### Security Tests
1. JWT token validation
2. Protected endpoint access
3. User isolation (cannot access other users' data)
4. Session management

## Test Results Summary

**Total Tests: 16+**
- Authentication: 12 tests
- User Management: 8+ tests
- Security: 6+ tests

All tests cover both happy paths and error scenarios as required by the acceptance criteria.
