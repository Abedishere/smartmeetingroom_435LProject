"""
Unit Tests for Rooms Service

This module contains comprehensive unit tests for the Rooms Service API endpoints.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rooms_service.app import create_app, db
from rooms_service.domain.models import Room
from rooms_service.application.services import RoomService
from rooms_service.application.validators import ValidationError


@pytest.fixture
def app():
    """Create and configure a test application instance."""
    # Set DATABASE_URL and TESTING env vars before create_app() is called
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['TESTING'] = 'True'

    app = create_app()
    app.config['TESTING'] = True

    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()

    # Clean up env vars
    for key in ['DATABASE_URL', 'TESTING']:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture
def client(app):
    """Create a test client for the application."""
    return app.test_client()


@pytest.fixture
def mock_auth():
    """Mock authentication to bypass Users Service calls."""
    with patch('rooms_service.application.auth.get_user_from_token') as mock:
        mock.return_value = {
            'id': 1,
            'username': 'admin',
            'role': 'admin',
            'email': 'admin@example.com'
        }
        yield mock


@pytest.fixture
def mock_facility_manager_auth():
    """Mock authentication for facility manager."""
    with patch('rooms_service.application.auth.get_user_from_token') as mock:
        mock.return_value = {
            'id': 2,
            'username': 'facility_manager',
            'role': 'facility_manager',
            'email': 'fm@example.com'
        }
        yield mock


@pytest.fixture
def mock_regular_user_auth():
    """Mock authentication for regular user."""
    with patch('rooms_service.application.auth.get_user_from_token') as mock:
        mock.return_value = {
            'id': 3,
            'username': 'user',
            'role': 'regular_user',
            'email': 'user@example.com'
        }
        yield mock


@pytest.fixture
def auth_headers():
    """Mock auth headers."""
    return {'Authorization': 'Bearer fake-token'}


class TestRoomCreation:
    """Tests for room creation endpoint."""

    def test_create_room_success(self, client, mock_auth, auth_headers):
        """Test successful room creation."""
        response = client.post('/api/rooms/',
                              headers=auth_headers,
                              json={
                                  'name': 'Conference Room A',
                                  'capacity': 10,
                                  'equipment': ['Projector', 'Whiteboard'],
                                  'location': 'Building 1, Floor 2'
                              })

        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'Room created successfully'
        assert data['room']['name'] == 'Conference Room A'
        assert data['room']['capacity'] == 10
        assert 'Projector' in data['room']['equipment']

    def test_create_room_as_facility_manager(self, client, mock_facility_manager_auth, auth_headers):
        """Test room creation as facility manager."""
        response = client.post('/api/rooms/',
                              headers=auth_headers,
                              json={
                                  'name': 'Meeting Room B',
                                  'capacity': 5,
                                  'equipment': ['TV Screen'],
                                  'location': 'Building 2, Floor 1'
                              })

        assert response.status_code == 201

    def test_create_room_duplicate_name(self, client, mock_auth, auth_headers):
        """Test creating room with duplicate name."""
        # Create first room
        client.post('/api/rooms/',
                   headers=auth_headers,
                   json={
                       'name': 'Conference Room A',
                       'capacity': 10,
                       'equipment': [],
                       'location': 'Building 1'
                   })

        # Try to create duplicate
        response = client.post('/api/rooms/',
                              headers=auth_headers,
                              json={
                                  'name': 'Conference Room A',
                                  'capacity': 5,
                                  'equipment': [],
                                  'location': 'Building 2'
                              })

        assert response.status_code == 400
        data = response.get_json()
        assert 'already exists' in data['error'].lower()

    def test_create_room_invalid_capacity(self, client, mock_auth, auth_headers):
        """Test creating room with invalid capacity."""
        response = client.post('/api/rooms/',
                              headers=auth_headers,
                              json={
                                  'name': 'Conference Room A',
                                  'capacity': -5,  # Invalid
                                  'equipment': [],
                                  'location': 'Building 1'
                              })

        assert response.status_code == 400

    def test_create_room_missing_fields(self, client, mock_auth, auth_headers):
        """Test creating room with missing required fields."""
        response = client.post('/api/rooms/',
                              headers=auth_headers,
                              json={
                                  'name': 'Conference Room A',
                                  'capacity': 10
                              })

        assert response.status_code == 400
        data = response.get_json()
        assert 'missing required fields' in data['error'].lower()

    def test_create_room_unauthorized(self, client, mock_regular_user_auth, auth_headers):
        """Test creating room as regular user (should fail)."""
        response = client.post('/api/rooms/',
                              headers=auth_headers,
                              json={
                                  'name': 'Conference Room A',
                                  'capacity': 10,
                                  'equipment': [],
                                  'location': 'Building 1'
                              })

        assert response.status_code == 403


class TestRoomRetrieval:
    """Tests for room retrieval endpoints."""

    def test_get_all_rooms(self, client, mock_auth, auth_headers, app):
        """Test getting all rooms."""
        # Create test rooms
        with app.app_context():
            room1 = Room(name='Room A', capacity=10, location='Building 1', status='available')
            room2 = Room(name='Room B', capacity=5, location='Building 2', status='available')
            db.session.add_all([room1, room2])
            db.session.commit()

        response = client.get('/api/rooms/', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'rooms' in data
        assert data['count'] == 2

    def test_get_room_by_id(self, client, mock_auth, auth_headers, app):
        """Test getting a specific room by ID."""
        with app.app_context():
            room = Room(name='Room A', capacity=10, location='Building 1', status='available')
            db.session.add(room)
            db.session.commit()
            room_id = room.id

        response = client.get(f'/api/rooms/{room_id}', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['room']['name'] == 'Room A'

    def test_get_nonexistent_room(self, client, mock_auth, auth_headers):
        """Test getting a nonexistent room."""
        response = client.get('/api/rooms/9999', headers=auth_headers)

        assert response.status_code == 404


class TestRoomSearch:
    """Tests for room search endpoint."""

    def test_search_by_capacity(self, client, mock_auth, auth_headers, app):
        """Test searching rooms by capacity."""
        with app.app_context():
            room1 = Room(name='Small Room', capacity=5, location='Building 1', status='available')
            room2 = Room(name='Large Room', capacity=20, location='Building 2', status='available')
            db.session.add_all([room1, room2])
            db.session.commit()

        response = client.get('/api/rooms/search?capacity=10', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 1
        assert data['rooms'][0]['name'] == 'Large Room'

    def test_search_by_location(self, client, mock_auth, auth_headers, app):
        """Test searching rooms by location."""
        with app.app_context():
            room1 = Room(name='Room A', capacity=10, location='Building 1', status='available')
            room2 = Room(name='Room B', capacity=10, location='Building 2', status='available')
            db.session.add_all([room1, room2])
            db.session.commit()

        response = client.get('/api/rooms/search?location=Building 1', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 1
        assert data['rooms'][0]['location'] == 'Building 1'

    def test_search_by_equipment(self, client, mock_auth, auth_headers, app):
        """Test searching rooms by equipment."""
        with app.app_context():
            room1 = Room(name='Room A', capacity=10, location='Building 1', status='available')
            room1.set_equipment_list(['Projector', 'Whiteboard'])
            room2 = Room(name='Room B', capacity=10, location='Building 2', status='available')
            room2.set_equipment_list(['TV Screen'])
            db.session.add_all([room1, room2])
            db.session.commit()

        response = client.get('/api/rooms/search?equipment=Projector', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 1
        assert data['rooms'][0]['name'] == 'Room A'


class TestRoomUpdate:
    """Tests for room update endpoint."""

    def test_update_room_success(self, client, mock_auth, auth_headers, app):
        """Test successful room update."""
        with app.app_context():
            room = Room(name='Room A', capacity=10, location='Building 1', status='available')
            db.session.add(room)
            db.session.commit()
            room_id = room.id

        response = client.put(f'/api/rooms/{room_id}',
                             headers=auth_headers,
                             json={
                                 'name': 'Updated Room A',
                                 'capacity': 15
                             })

        assert response.status_code == 200
        data = response.get_json()
        assert data['room']['name'] == 'Updated Room A'
        assert data['room']['capacity'] == 15

    def test_update_room_as_facility_manager(self, client, mock_facility_manager_auth, auth_headers, app):
        """Test updating room as facility manager."""
        with app.app_context():
            room = Room(name='Room A', capacity=10, location='Building 1', status='available')
            db.session.add(room)
            db.session.commit()
            room_id = room.id

        response = client.put(f'/api/rooms/{room_id}',
                             headers=auth_headers,
                             json={'capacity': 12})

        assert response.status_code == 200

    def test_update_room_unauthorized(self, client, mock_regular_user_auth, auth_headers, app):
        """Test updating room as regular user (should fail)."""
        with app.app_context():
            room = Room(name='Room A', capacity=10, location='Building 1', status='available')
            db.session.add(room)
            db.session.commit()
            room_id = room.id

        response = client.put(f'/api/rooms/{room_id}',
                             headers=auth_headers,
                             json={'capacity': 12})

        assert response.status_code == 403

    def test_update_nonexistent_room(self, client, mock_auth, auth_headers):
        """Test updating nonexistent room."""
        response = client.put('/api/rooms/9999',
                             headers=auth_headers,
                             json={'capacity': 12})

        assert response.status_code == 404


class TestRoomDeletion:
    """Tests for room deletion endpoint."""

    def test_delete_room_success(self, client, mock_auth, auth_headers, app):
        """Test successful room deletion."""
        with app.app_context():
            room = Room(name='Room A', capacity=10, location='Building 1', status='available')
            db.session.add(room)
            db.session.commit()
            room_id = room.id

        response = client.delete(f'/api/rooms/{room_id}', headers=auth_headers)

        assert response.status_code == 200

        # Verify deletion
        response = client.get(f'/api/rooms/{room_id}', headers=auth_headers)
        assert response.status_code == 404

    def test_delete_room_as_facility_manager(self, client, mock_facility_manager_auth, auth_headers, app):
        """Test deleting room as facility manager."""
        with app.app_context():
            room = Room(name='Room A', capacity=10, location='Building 1', status='available')
            db.session.add(room)
            db.session.commit()
            room_id = room.id

        response = client.delete(f'/api/rooms/{room_id}', headers=auth_headers)

        assert response.status_code == 200

    def test_delete_room_unauthorized(self, client, mock_regular_user_auth, auth_headers, app):
        """Test deleting room as regular user (should fail)."""
        with app.app_context():
            room = Room(name='Room A', capacity=10, location='Building 1', status='available')
            db.session.add(room)
            db.session.commit()
            room_id = room.id

        response = client.delete(f'/api/rooms/{room_id}', headers=auth_headers)

        assert response.status_code == 403

    def test_delete_nonexistent_room(self, client, mock_auth, auth_headers):
        """Test deleting nonexistent room."""
        response = client.delete('/api/rooms/9999', headers=auth_headers)

        assert response.status_code == 404


class TestRoomStatusUpdate:
    """Tests for room status update endpoint."""

    def test_update_room_status(self, client, mock_auth, auth_headers, app):
        """Test updating room status."""
        with app.app_context():
            room = Room(name='Room A', capacity=10, location='Building 1', status='available')
            db.session.add(room)
            db.session.commit()
            room_id = room.id

        response = client.patch(f'/api/rooms/{room_id}/status',
                               headers=auth_headers,
                               json={'status': 'out_of_service'})

        assert response.status_code == 200
        data = response.get_json()
        assert data['room']['status'] == 'out_of_service'

    def test_update_room_status_invalid(self, client, mock_auth, auth_headers, app):
        """Test updating room status with invalid value."""
        with app.app_context():
            room = Room(name='Room A', capacity=10, location='Building 1', status='available')
            db.session.add(room)
            db.session.commit()
            room_id = room.id

        response = client.patch(f'/api/rooms/{room_id}/status',
                               headers=auth_headers,
                               json={'status': 'invalid_status'})

        assert response.status_code == 400


class TestInputValidation:
    """Tests for input validation and sanitization."""

    def test_sanitize_xss_attempt(self, client, mock_auth, auth_headers):
        """Test that XSS attempts are sanitized."""
        response = client.post('/api/rooms/',
                              headers=auth_headers,
                              json={
                                  'name': '<script>alert("XSS")</script>Room',
                                  'capacity': 10,
                                  'equipment': [],
                                  'location': 'Building 1'
                              })

        assert response.status_code == 201
        data = response.get_json()
        # Script tags should be removed
        assert '<script>' not in data['room']['name']

    def test_validate_room_name_format(self, client, mock_auth, auth_headers):
        """Test room name format validation."""
        response = client.post('/api/rooms/',
                              headers=auth_headers,
                              json={
                                  'name': 'R',  # Too short
                                  'capacity': 10,
                                  'equipment': [],
                                  'location': 'Building 1'
                              })

        assert response.status_code == 400

    def test_validate_equipment_format(self, client, mock_auth, auth_headers):
        """Test equipment validation."""
        response = client.post('/api/rooms/',
                              headers=auth_headers,
                              json={
                                  'name': 'Room A',
                                  'capacity': 10,
                                  'equipment': ['Valid Equipment', '<script>bad</script>'],
                                  'location': 'Building 1'
                              })

        assert response.status_code == 201
        data = response.get_json()
        # Script should be sanitized
        assert not any('<script>' in eq for eq in data['room']['equipment'])


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/api/rooms/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'rooms'
