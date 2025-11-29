# Smart Meeting Room Management System

Backend system for managing meeting rooms with Users and Rooms services, implementing clean architecture, JWT authentication, and role-based access control.

## Project Overview

This is a complete Smart Meeting Room Management System. It implements:
- **Users Service**: User authentication, authorization, and profile management
- **Rooms Service**: Meeting room inventory management with equipment tracking
- **Bookings Service**: Room reservation management with conflict detection
- **Reviews Service**: Room reviews with ratings and moderation

### Authors
- Abdel Rahman El Kouche - Users Service, Rooms Service, Admin role, Facility Manager role
- Karim Abou Daher - Bookings Service, Reviews Service, Part II features integration

## Services Architecture

### Users Service (Port 5001)
- User registration and authentication
- JWT token-based authorization
- Role-based access control
- Profile management
- Password hashing with bcrypt

### Rooms Service (Port 5002)
- Room creation and management
- Equipment tracking
- Room search by capacity, location, and equipment
- Status management (available, booked, out_of_service)
- Inter-service authentication with Users Service

### Bookings Service (Port 5003)
- Create and manage room reservations
- Conflict detection for overlapping bookings
- Availability checking
- User booking history
- Status management (confirmed, cancelled)
- Role-based booking permissions

### Reviews Service (Port 5004)
- Create and manage room reviews
- 5-star rating system
- Comment sanitization with bleach
- Review flagging and moderation
- Filter by rating and flagged status
- Moderator controls for content management

## Tech Stack
- **Language**: Python 3.12
- **Frameworks**: Flask 3.0 (Users, Rooms) & FastAPI 0.110 (Bookings, Reviews)
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0 (sync & async with asyncpg)
- **Authentication**: Flask-JWT-Extended 4.6 & python-jose 3.3
- **Rate Limiting**: Flask-Limiter 3.5 & SlowAPI 0.1.9
- **Containerization**: Docker & Docker Compose
- **Testing**: Pytest 7.4 with coverage
- **Profiling**: cProfile, line-profiler 4.1.1, memory-profiler
- **Documentation**: Sphinx 7.2 with Read the Docs theme
- **Security**: bcrypt, bleach, email-validator

## User Roles

### Admin (Implemented)
- Full system access
- Create/read/update/delete users
- Assign and change roles
- Manage all rooms
- View all bookings and history

### Facility Manager (Implemented)
- Create/update/delete rooms
- Manage room equipment
- Set room availability status
- View all bookings
- Manage own profile

### Other Roles (Defined)
- Regular User
- Moderator
- Auditor
- Service Account

## Setup Instructions

### Prerequisites
- Docker Desktop installed
- Git installed
- Postman (optional, for API testing)

### Quick Start

1. **Clone the repository**
```bash
git clone <repository-url>
cd 435LProject
```

2. **Start the services**
```bash
docker-compose up --build
```

**Note**: The PostgreSQL database is automatically initialized with schema, indexes, constraints, and sample data from `init.sql` on first startup.

3. **Access the services**
- Users Service: http://localhost:5001
- Rooms Service: http://localhost:5002
- Bookings Service: http://localhost:5003
- Reviews Service: http://localhost:5004
- PostgreSQL: localhost:5432

### Running Tests

```bash
# Install dependencies in virtual environment
pip install -r requirements.txt

# Run all tests with coverage
pytest

# Run specific service tests
pytest tests/test_users_service.py
pytest tests/test_rooms_service.py
pytest tests/test_bookings_service.py
pytest tests/test_reviews_service.py

# Generate coverage report
pytest --cov=users_service --cov=rooms_service --cov=bookings_service --cov=reviews_service --cov-report=html
```

### Building Documentation

```bash
cd docs
sphinx-build -b html . _build
# Open _build/index.html in browser
```

### Performance Profiling

```bash
# Function-level profiler (identifies bottleneck functions)
python profiling/profiler.py

# Line-by-line profiler (pinpoints exact slow code lines)
python profiling/line_profiler_script.py

# Memory profiling
python -m memory_profiler profiling/profile_memory.py

# Legacy performance profiler
python profiling/performance_profiler.py
```

## API Documentation

### Importing Postman Collection

1. Open Postman
2. Click "Import"
3. Select `postman_collection.json`
4. Collection includes all endpoints with examples and descriptions

### Key Endpoints

#### Users Service

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/users/health` | GET | Health check | No |
| `/api/users/register` | POST | Register new user | No |
| `/api/users/login` | POST | Login and get JWT | No |
| `/api/users/` | GET | Get all users | Admin/Auditor |
| `/api/users/<username>` | GET | Get user by username | Yes |
| `/api/users/me` | GET | Get current user | Yes |
| `/api/users/<id>` | PUT | Update user | Yes |
| `/api/users/<id>` | DELETE | Delete user | Admin |

#### Rooms Service

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/rooms/health` | GET | Health check | No |
| `/api/rooms/` | POST | Create room | Admin/FM |
| `/api/rooms/` | GET | Get all rooms | Yes |
| `/api/rooms/search` | GET | Search rooms | Yes |
| `/api/rooms/<id>` | GET | Get room by ID | Yes |
| `/api/rooms/<id>` | PUT | Update room | Admin/FM |
| `/api/rooms/<id>` | DELETE | Delete room | Admin/FM |
| `/api/rooms/<id>/status` | PATCH | Update status | Admin/FM |

#### Bookings Service

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/health` | GET | Health check | No |
| `/bookings` | GET | Get all bookings | Admin/FM/Auditor |
| `/bookings/<id>` | GET | Get booking by ID | Admin/FM/Auditor |
| `/bookings/user/<username>` | GET | Get user bookings | Yes |
| `/bookings` | POST | Create booking | Yes |
| `/bookings/<id>` | PUT | Update booking | Owner/Admin/FM |
| `/bookings/<id>` | DELETE | Cancel booking | Owner/Admin/FM |
| `/bookings/check-availability` | GET | Check availability | Yes |

#### Reviews Service

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/health` | GET | Health check | No |
| `/reviews` | POST | Create review | Yes |
| `/reviews/<id>` | PUT | Update review | Owner/Admin |
| `/reviews/<id>` | DELETE | Delete review | Owner/Admin/Moderator |
| `/reviews/room/<id>` | GET | Get room reviews | Yes |
| `/reviews/<id>/flag` | POST | Flag review | Yes |
| `/reviews/<id>/unflag` | POST | Unflag review | Moderator/Admin |

## Part II Features (Implemented)

### Rate Limiting
All services implement rate limiting to prevent abuse:

**Flask Services (Users, Rooms):**
- Global limits: 200 requests/day, 50 requests/hour
- Registration endpoint: 10 requests/hour
- Login endpoint: 20 requests/hour
- Room creation: 30 requests/hour
- Implementation: Flask-Limiter with in-memory storage

**FastAPI Services (Bookings, Reviews):**
- Global limits: 200 requests/day, 50 requests/hour
- Implementation: SlowAPI for async FastAPI support

### Structured Logging
All services log requests in structured JSON format for monitoring and analysis:

**Logged Information:**
- Timestamp (ISO 8601 format)
- Service name
- HTTP method and path
- Status code
- Request duration (milliseconds)
- Client IP address
- User agent
- Authenticated user ID and username (if available)

**Example Log Entry:**
```json
{
  "timestamp": "2025-11-26T10:30:45.123456",
  "service": "users_service",
  "method": "POST",
  "path": "/api/users/login",
  "status_code": 200,
  "duration_ms": 45.23,
  "ip": "172.18.0.1",
  "user_agent": "PostmanRuntime/7.32.3",
  "user_id": 1,
  "username": "admin"
}
```

**Benefits:**
- Easy integration with log aggregation tools (ELK, Splunk)
- Performance monitoring and analysis
- Security audit trails
- Debugging and troubleshooting

## Security Features

### Input Validation & Sanitization
- All inputs validated and sanitized
- HTML/script tag removal using bleach
- SQL injection prevention via ORM
- Email validation
- Password strength requirements

### Authentication & Authorization
- JWT tokens with 1-hour expiration
- Password hashing with bcrypt (salt rounds: 12)
- Role-based access control
- Protected endpoints

### Security Best Practices
- Parameterized queries (SQLAlchemy ORM)
- No sensitive data in logs
- Environment variables for secrets
- CORS ready for production

## Database Schema

The database schema is defined in `init.sql` which is automatically executed on first PostgreSQL container startup. It includes tables, indexes, foreign keys, check constraints, and triggers.

### Users Table
- id (SERIAL PRIMARY KEY)
- name (VARCHAR 100)
- username (VARCHAR 50, UNIQUE, INDEXED)
- password_hash (VARCHAR 255)
- email (VARCHAR 120, UNIQUE, INDEXED)
- role (VARCHAR 20, INDEXED, DEFAULT 'regular_user')
- created_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
- updated_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP, auto-updated via trigger)

### Rooms Table
- id (SERIAL PRIMARY KEY)
- name (VARCHAR 100, UNIQUE, INDEXED)
- capacity (INTEGER, CHECK > 0, INDEXED)
- equipment (TEXT)
- location (VARCHAR 200, INDEXED)
- status (VARCHAR 20, INDEXED, DEFAULT 'available')
- created_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
- updated_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP, auto-updated via trigger)

### Bookings Table
- id (SERIAL PRIMARY KEY)
- user_id (INTEGER, FOREIGN KEY → users.id, INDEXED, CASCADE DELETE)
- room_id (INTEGER, FOREIGN KEY → rooms.id, INDEXED, CASCADE DELETE)
- start_time (TIMESTAMP, INDEXED)
- end_time (TIMESTAMP, INDEXED, CHECK end_time > start_time)
- status (VARCHAR 20, INDEXED, DEFAULT 'confirmed')
- created_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
- **Unique Constraint**: (room_id, start_time, end_time) to prevent double-booking

### Reviews Table
- id (SERIAL PRIMARY KEY)
- room_id (INTEGER, FOREIGN KEY → rooms.id, INDEXED, CASCADE DELETE)
- user_id (INTEGER, FOREIGN KEY → users.id, INDEXED, CASCADE DELETE)
- rating (INTEGER, CHECK 1-5, INDEXED)
- comment (TEXT)
- flagged (BOOLEAN, INDEXED, DEFAULT FALSE)
- created_at (TIMESTAMP, INDEXED, DEFAULT CURRENT_TIMESTAMP)

### Default Data
The `init.sql` script includes:
- Admin user (username: `admin`, password: `admin123`)
- Facility Manager user (username: `facility_manager`, password: `manager123`)
- 5 sample meeting rooms with various capacities and equipment

## Testing

### Test Coverage
- **Users Service**: 50+ test cases
- **Rooms Service**: 40+ test cases
- **Bookings Service**: 25+ test cases
- **Reviews Service**: 25+ test cases
- **Total**: 99+ test cases
- **Code Coverage**: >85%

### Test Categories
- Unit tests for all endpoints
- Validation tests
- Authentication tests
- Authorization tests
- Security tests (XSS, SQL injection)
- Error handling tests

## Project Structure

```
435LProject/
├── users_service/             # Flask - Port 5001
│   ├── domain/
│   │   └── models.py          # User entity
│   ├── application/
│   │   ├── services.py        # Business logic
│   │   ├── validators.py      # Input validation
│   │   └── auth.py           # Authorization
│   ├── presentation/
│   │   └── routes.py         # API endpoints
│   ├── app.py                # App factory with rate limiting & logging
│   └── Dockerfile
├── rooms_service/             # Flask - Port 5002
│   ├── domain/
│   │   └── models.py          # Room entity
│   ├── application/
│   │   ├── services.py        # Business logic
│   │   ├── validators.py      # Input validation
│   │   └── auth.py           # Authorization
│   ├── presentation/
│   │   └── routes.py         # API endpoints
│   ├── app.py                # App factory with rate limiting & logging
│   └── Dockerfile
├── bookings_service/          # FastAPI - Port 5003
│   ├── models.py             # Booking, User, Room entities
│   ├── schemas.py            # Pydantic models
│   ├── database.py           # Async SQLAlchemy setup
│   ├── auth.py               # JWT authentication
│   ├── routes.py             # API endpoints
│   ├── main.py               # FastAPI app with rate limiting & logging
│   └── Dockerfile
├── reviews_service/           # FastAPI - Port 5004
│   ├── models.py             # Review, User, Room entities
│   ├── schemas.py            # Pydantic models
│   ├── database.py           # Async SQLAlchemy setup
│   ├── auth.py               # JWT authentication
│   ├── routes.py             # API endpoints
│   ├── main.py               # FastAPI app with rate limiting & logging
│   └── Dockerfile
├── tests/
│   ├── test_users_service.py
│   ├── test_rooms_service.py
│   ├── test_bookings_service.py
│   └── test_reviews_service.py
├── docs/                      # Sphinx documentation
├── profiling/                 # Performance analysis tools
│   ├── profiler.py           # Function-level profiler
│   ├── line_profiler_script.py  # Line-by-line profiler
│   ├── profile_memory.py     # Memory profiler
│   └── performance_profiler.py   # Legacy profiler
├── init.sql                   # Database schema initialization
├── docker-compose.yml        # All 4 services + PostgreSQL
└── requirements.txt          # All dependencies
```

## Development Workflow

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes and commit
git add .
git commit -m "Description of changes"

# Push to remote
git push origin feature/your-feature
```

### Code Quality
- Follow PEP 8 style guide
- Write docstrings for all functions
- Maintain >80% test coverage
- Document all API endpoints

## Troubleshooting

### Common Issues

**Port already in use**
```bash
# Stop existing containers
docker-compose down

# Check for processes using ports
netstat -ano | findstr :5001
netstat -ano | findstr :5002
```

**Database connection issues**
```bash
# Reset database
docker-compose down -v
docker-compose up --build
```

**Import errors in tests**
```bash
# Ensure you're in the project root
cd C:\Users\user\PycharmProjects\435LProject

# Run with Python module syntax
python -m pytest tests/
```

## Future Enhancements

Additional features that could be implemented:
- Circuit breaker pattern for service resilience
- Caching with Redis for improved performance
- Real-time dashboards with WebSockets
- Multi-factor authentication
- Prometheus monitoring and metrics
- API versioning
- GraphQL support

