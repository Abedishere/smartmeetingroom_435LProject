"""
Unit Tests for Users Service

This module contains comprehensive unit tests for the Users Service API endpoints.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from users_service.app import create_app, db
from users_service.domain.models import User
from users_service.application.services import UserService
from users_service.application.validators import ValidationError


@pytest.fixture
def app():
    """Create and configure a test application instance."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the application."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Create an authenticated admin user and return auth headers."""
    # Register admin user
    response = client.post('/api/users/register', json={
        'name': 'Admin User',
        'username': 'admin',
        'password': 'Admin123',
        'email': 'admin@example.com',
        'role': 'admin'
    })

    # Login
    response = client.post('/api/users/login', json={
        'username': 'admin',
        'password': 'Admin123'
    })

    data = response.get_json()
    token = data['access_token']

    return {'Authorization': f'Bearer {token}'}


class TestUserRegistration:
    """Tests for user registration endpoint."""

    def test_register_user_success(self, client):
        """Test successful user registration."""
        response = client.post('/api/users/register', json={
            'name': 'John Doe',
            'username': 'johndoe',
            'password': 'SecurePass123',
            'email': 'john@example.com',
            'role': 'regular_user'
        })

        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'User created successfully'
        assert data['user']['username'] == 'johndoe'
        assert data['user']['email'] == 'john@example.com'
        assert data['user']['role'] == 'regular_user'

    def test_register_duplicate_username(self, client):
        """Test registration with duplicate username."""
        # Create first user
        client.post('/api/users/register', json={
            'name': 'John Doe',
            'username': 'johndoe',
            'password': 'SecurePass123',
            'email': 'john@example.com'
        })

        # Try to create user with same username
        response = client.post('/api/users/register', json={
            'name': 'Jane Doe',
            'username': 'johndoe',
            'password': 'AnotherPass123',
            'email': 'jane@example.com'
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'already exists' in data['error'].lower()

    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post('/api/users/register', json={
            'name': 'John Doe',
            'username': 'johndoe',
            'password': 'SecurePass123',
            'email': 'invalid-email'
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'validation error' in data['error'].lower()

    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post('/api/users/register', json={
            'name': 'John Doe',
            'username': 'johndoe',
            'password': 'weak',
            'email': 'john@example.com'
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'validation error' in data['error'].lower()

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields."""
        response = client.post('/api/users/register', json={
            'name': 'John Doe',
            'username': 'johndoe'
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'missing required fields' in data['error'].lower()


class TestUserAuthentication:
    """Tests for user authentication endpoint."""

    def test_login_success(self, client):
        """Test successful login."""
        # Register user
        client.post('/api/users/register', json={
            'name': 'John Doe',
            'username': 'johndoe',
            'password': 'SecurePass123',
            'email': 'john@example.com'
        })

        # Login
        response = client.post('/api/users/login', json={
            'username': 'johndoe',
            'password': 'SecurePass123'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert data['message'] == 'Login successful'

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        # Register user
        client.post('/api/users/register', json={
            'name': 'John Doe',
            'username': 'johndoe',
            'password': 'SecurePass123',
            'email': 'john@example.com'
        })

        # Try to login with wrong password
        response = client.post('/api/users/login', json={
            'username': 'johndoe',
            'password': 'WrongPassword123'
        })

        assert response.status_code == 401
        data = response.get_json()
        assert 'invalid' in data['error'].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        response = client.post('/api/users/login', json={
            'username': 'nonexistent',
            'password': 'SomePass123'
        })

        assert response.status_code == 401

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials."""
        response = client.post('/api/users/login', json={
            'username': 'johndoe'
        })

        assert response.status_code == 400


class TestUserRetrieval:
    """Tests for user retrieval endpoints."""

    def test_get_all_users_as_admin(self, client, auth_headers):
        """Test getting all users as admin."""
        # Create another user
        client.post('/api/users/register', json={
            'name': 'Jane Doe',
            'username': 'janedoe',
            'password': 'SecurePass123',
            'email': 'jane@example.com'
        })

        response = client.get('/api/users/', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'users' in data
        assert data['count'] >= 2  # At least admin and janedoe

    def test_get_all_users_unauthorized(self, client):
        """Test getting all users without authentication."""
        response = client.get('/api/users/')

        assert response.status_code == 401

    def test_get_user_by_username(self, client, auth_headers):
        """Test getting a specific user by username."""
        response = client.get('/api/users/admin', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['username'] == 'admin'

    def test_get_nonexistent_user(self, client, auth_headers):
        """Test getting a nonexistent user."""
        response = client.get('/api/users/nonexistent', headers=auth_headers)

        assert response.status_code == 404

    def test_get_current_user_profile(self, client, auth_headers):
        """Test getting current user's profile."""
        response = client.get('/api/users/me', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['username'] == 'admin'


class TestUserUpdate:
    """Tests for user update endpoint."""

    def test_update_own_profile(self, client, auth_headers):
        """Test updating own profile."""
        # Get current user ID
        response = client.get('/api/users/me', headers=auth_headers)
        user_id = response.get_json()['user']['id']

        # Update profile
        response = client.put(f'/api/users/{user_id}',
                             headers=auth_headers,
                             json={
                                 'name': 'Updated Name',
                                 'email': 'newemail@example.com'
                             })

        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['name'] == 'Updated Name'
        assert data['user']['email'] == 'newemail@example.com'

    def test_update_user_role_as_admin(self, client, auth_headers):
        """Test updating user role as admin."""
        # Create regular user
        client.post('/api/users/register', json={
            'name': 'Jane Doe',
            'username': 'janedoe',
            'password': 'SecurePass123',
            'email': 'jane@example.com'
        })

        # Get Jane's ID
        response = client.get('/api/users/janedoe', headers=auth_headers)
        user_id = response.get_json()['user']['id']

        # Update role
        response = client.put(f'/api/users/{user_id}',
                             headers=auth_headers,
                             json={'role': 'facility_manager'})

        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['role'] == 'facility_manager'

    def test_update_nonexistent_user(self, client, auth_headers):
        """Test updating nonexistent user."""
        response = client.put('/api/users/9999',
                             headers=auth_headers,
                             json={'name': 'New Name'})

        assert response.status_code == 404


class TestUserDeletion:
    """Tests for user deletion endpoint."""

    def test_delete_user_as_admin(self, client, auth_headers):
        """Test deleting a user as admin."""
        # Create user
        client.post('/api/users/register', json={
            'name': 'Jane Doe',
            'username': 'janedoe',
            'password': 'SecurePass123',
            'email': 'jane@example.com'
        })

        # Get user ID
        response = client.get('/api/users/janedoe', headers=auth_headers)
        user_id = response.get_json()['user']['id']

        # Delete user
        response = client.delete(f'/api/users/{user_id}', headers=auth_headers)

        assert response.status_code == 200

        # Verify user is deleted
        response = client.get('/api/users/janedoe', headers=auth_headers)
        assert response.status_code == 404

    def test_delete_nonexistent_user(self, client, auth_headers):
        """Test deleting nonexistent user."""
        response = client.delete('/api/users/9999', headers=auth_headers)

        assert response.status_code == 404


class TestInputValidation:
    """Tests for input validation and sanitization."""

    def test_sanitize_xss_attempt(self, client):
        """Test that XSS attempts are sanitized."""
        response = client.post('/api/users/register', json={
            'name': '<script>alert("XSS")</script>John',
            'username': 'johndoe',
            'password': 'SecurePass123',
            'email': 'john@example.com'
        })

        assert response.status_code == 201
        data = response.get_json()
        # Script tags should be removed
        assert '<script>' not in data['user']['name']

    def test_validate_username_format(self, client):
        """Test username format validation."""
        response = client.post('/api/users/register', json={
            'name': 'John Doe',
            'username': 'john@doe',  # Invalid character
            'password': 'SecurePass123',
            'email': 'john@example.com'
        })

        assert response.status_code == 400

    def test_password_strength_requirements(self, client):
        """Test password strength requirements."""
        # No uppercase
        response = client.post('/api/users/register', json={
            'name': 'John Doe',
            'username': 'johndoe',
            'password': 'securepass123',
            'email': 'john@example.com'
        })
        assert response.status_code == 400

        # No lowercase
        response = client.post('/api/users/register', json={
            'name': 'John Doe',
            'username': 'johndoe',
            'password': 'SECUREPASS123',
            'email': 'john@example.com'
        })
        assert response.status_code == 400

        # No digit
        response = client.post('/api/users/register', json={
            'name': 'John Doe',
            'username': 'johndoe',
            'password': 'SecurePassword',
            'email': 'john@example.com'
        })
        assert response.status_code == 400


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/api/users/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'users'
