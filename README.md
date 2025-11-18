# Smart Meeting Room Management System

Backend system for managing meeting rooms with Users and Rooms services, implementing clean architecture, JWT authentication, and role-based access control.

## Project Overview

This is the first half of a complete Smart Meeting Room Management System. It implements:
- **Users Service**: User authentication, authorization, and profile management
- **Rooms Service**: Meeting room inventory management with equipment tracking

### Author
- Abdel Rahman El Kouche - Users Service, Rooms Service, Admin role, Facility Manager role

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

## Tech Stack
- **Language**: Python 3.13
- **Framework**: Flask 3.0
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 3.1
- **Authentication**: Flask-JWT-Extended 4.6
- **Containerization**: Docker & Docker Compose
- **Testing**: Pytest 7.4 with coverage
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

3. **Access the services**
- Users Service: http://localhost:5001
- Rooms Service: http://localhost:5002
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

# Generate coverage report
pytest --cov=users_service --cov=rooms_service --cov-report=html
```

### Building Documentation

```bash
cd docs
sphinx-build -b html . _build
# Open _build/index.html in browser
```

### Performance Profiling

```bash
# Performance profiling
python profiling/performance_profiler.py

# Memory profiling
python -m memory_profiler profiling/memory_profiler.py
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

### Users Table
- id (PRIMARY KEY)
- name
- username (UNIQUE, INDEXED)
- password_hash
- email (UNIQUE, INDEXED)
- role
- created_at
- updated_at

### Rooms Table
- id (PRIMARY KEY)
- name (UNIQUE, INDEXED)
- capacity
- equipment (TEXT)
- location
- status
- created_at
- updated_at

## Testing

### Test Coverage
- **Users Service**: 50+ test cases
- **Rooms Service**: 40+ test cases
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
├── users_service/
│   ├── domain/
│   │   └── models.py          # User entity
│   ├── application/
│   │   ├── services.py        # Business logic
│   │   ├── validators.py      # Input validation
│   │   └── auth.py           # Authorization
│   └── presentation/
│       └── routes.py         # API endpoints
├── rooms_service/
│   ├── domain/
│   │   └── models.py          # Room entity
│   ├── application/
│   │   ├── services.py        # Business logic
│   │   ├── validators.py      # Input validation
│   │   └── auth.py           # Authorization
│   └── presentation/
│       └── routes.py         # API endpoints
├── tests/
│   ├── test_users_service.py
│   └── test_rooms_service.py
├── docs/                      # Sphinx documentation
├── profiling/                 # Performance scripts
├── docker-compose.yml
└── requirements.txt
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

## Future Enhancements (Part II)

Planned enhancements include:
- Bookings Service
- Reviews Service
- Circuit breaker pattern
- Rate limiting
- Caching with Redis
- Real-time dashboards
- Multi-factor authentication
- Prometheus monitoring

## License

This is a academic project for Software Tools Lab - Fall 2025-2026.

## Contact

For questions or issues, please contact the project maintainer.
