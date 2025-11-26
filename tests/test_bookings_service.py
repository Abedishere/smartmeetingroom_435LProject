"""
Comprehensive Tests for Bookings Service

This module contains unit tests for all Bookings Service API endpoints.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bookings_service.database import Base, get_session
from bookings_service.main import get_app
from bookings_service.models import Booking, Room, User


TEST_SECRET = "test-secret-key"
ALGORITHM = "HS256"


def _token_for(user_id: int, username: str, role: str) -> str:
    """Generate JWT token for testing."""
    return jwt.encode({"sub": str(user_id), "username": username, "role": role}, TEST_SECRET, algorithm=ALGORITHM)


@pytest.fixture(scope="module")
def async_engine():
    """Create async database engine for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///./test_bookings.db", future=True)
    return engine


@pytest.fixture(scope="module")
def async_session_factory(async_engine):
    """Create async session factory."""
    return async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="session", autouse=True)
def setup_env():
    """Setup environment variables for testing."""
    os.environ["JWT_SECRET_KEY"] = TEST_SECRET
    os.environ["JWT_ALGORITHM"] = ALGORITHM


@pytest.fixture(scope="module")
def app(async_engine, async_session_factory, setup_env):
    """Configure app with test database and dependency overrides."""
    app = get_app()

    async def init_models():
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with async_session_factory() as session:
            # Seed test data
            session.add_all(
                [
                    User(id=1, username="alice", role="regular_user"),
                    User(id=2, username="bob", role="admin"),
                    User(id=3, username="charlie", role="facility_manager"),
                    User(id=4, username="dave", role="auditor_readonly"),
                    User(id=5, username="service", role="service_account"),
                ]
            )
            session.add_all([Room(id=1, name="Conf A"), Room(id=2, name="Conf B"), Room(id=3, name="Conf C")])
            await session.commit()

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    asyncio.get_event_loop().run_until_complete(init_models())
    return app


@pytest.fixture
def client(app):
    """Create test client that wraps AsyncClient."""
    transport = ASGITransport(app=app)
    async_client = AsyncClient(transport=transport, base_url="http://testserver")
    loop = asyncio.get_event_loop()

    class SyncClient:
        def request(self, method: str, url: str, **kwargs):
            return loop.run_until_complete(async_client.request(method, url, **kwargs))

        def post(self, url: str, **kwargs):
            return self.request("POST", url, **kwargs)

        def get(self, url: str, **kwargs):
            return self.request("GET", url, **kwargs)

        def put(self, url: str, **kwargs):
            return self.request("PUT", url, **kwargs)

        def delete(self, url: str, **kwargs):
            return self.request("DELETE", url, **kwargs)

    client = SyncClient()
    try:
        yield client
    finally:
        loop.run_until_complete(async_client.aclose())


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "bookings"


class TestListBookings:
    """Tests for listing all bookings."""

    def test_list_bookings_as_admin(self, client):
        """Test admin can list all bookings."""
        token = _token_for(2, "bob", "admin")
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/bookings", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_bookings_as_facility_manager(self, client):
        """Test facility manager can list all bookings."""
        token = _token_for(3, "charlie", "facility_manager")
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/bookings", headers=headers)
        assert response.status_code == 200

    def test_list_bookings_as_auditor(self, client):
        """Test auditor can list all bookings."""
        token = _token_for(4, "dave", "auditor_readonly")
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/bookings", headers=headers)
        assert response.status_code == 200

    def test_list_bookings_unauthorized(self, client):
        """Test regular user cannot list all bookings."""
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/bookings", headers=headers)
        assert response.status_code == 403


class TestCreateBooking:
    """Tests for creating bookings."""

    def test_create_booking_success(self, client):
        """Test successful booking creation."""
        start = datetime.utcnow()
        end = start + timedelta(hours=2)
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/bookings",
            json={
                "user_id": 1,
                "room_id": 1,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"]
        assert data["status"] == "confirmed"
        assert data["user"]["username"] == "alice"
        assert data["room"]["name"] == "Conf A"

    def test_create_booking_conflict(self, client):
        """Test booking creation fails with time conflict."""
        start = datetime.utcnow() + timedelta(days=1)
        end = start + timedelta(hours=2)
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        # Create first booking
        response = client.post(
            "/bookings",
            json={
                "user_id": 1,
                "room_id": 2,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            headers=headers,
        )
        assert response.status_code == 201

        # Try overlapping booking
        response = client.post(
            "/bookings",
            json={
                "user_id": 2,
                "room_id": 2,
                "start_time": (start + timedelta(minutes=30)).isoformat(),
                "end_time": (end + timedelta(hours=1)).isoformat(),
            },
            headers=headers,
        )
        assert response.status_code == 409
        assert "conflict" in response.json()["detail"].lower()

    def test_create_booking_invalid_time(self, client):
        """Test booking creation fails with invalid time range."""
        start = datetime.utcnow()
        end = start - timedelta(hours=1)  # End before start
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/bookings",
            json={
                "user_id": 1,
                "room_id": 1,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            headers=headers,
        )
        assert response.status_code == 422

    def test_create_booking_missing_user(self, client):
        """Test booking creation requires user_id or username."""
        start = datetime.utcnow()
        end = start + timedelta(hours=2)
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/bookings",
            json={
                "room_id": 1,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            headers=headers,
        )
        assert response.status_code == 400

    def test_create_booking_user_not_found(self, client):
        """Test booking creation fails with non-existent user."""
        start = datetime.utcnow()
        end = start + timedelta(hours=2)
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/bookings",
            json={
                "user_id": 999,
                "room_id": 1,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            headers=headers,
        )
        assert response.status_code == 404
        assert "user" in response.json()["detail"].lower()

    def test_create_booking_room_not_found(self, client):
        """Test booking creation fails with non-existent room."""
        start = datetime.utcnow()
        end = start + timedelta(hours=2)
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/bookings",
            json={
                "user_id": 1,
                "room_id": 999,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            headers=headers,
        )
        assert response.status_code == 404
        assert "room" in response.json()["detail"].lower()

    def test_create_booking_readonly_forbidden(self, client):
        """Test auditor readonly cannot create bookings."""
        start = datetime.utcnow()
        end = start + timedelta(hours=2)
        token = _token_for(4, "dave", "auditor_readonly")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/bookings",
            json={
                "user_id": 4,
                "room_id": 1,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            headers=headers,
        )
        assert response.status_code == 403


class TestUpdateBooking:
    """Tests for updating bookings."""

    def test_update_booking_as_owner(self, client):
        """Test owner can update their booking."""
        start = datetime.utcnow() + timedelta(days=2)
        end = start + timedelta(hours=2)
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        # Create booking
        response = client.post(
            "/bookings",
            json={
                "user_id": 1,
                "room_id": 1,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            headers=headers,
        )
        booking_id = response.json()["id"]

        # Update booking
        new_start = start + timedelta(hours=1)
        new_end = new_start + timedelta(hours=2)
        response = client.put(
            f"/bookings/{booking_id}",
            json={
                "start_time": new_start.isoformat(),
                "end_time": new_end.isoformat(),
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == booking_id

    def test_update_booking_as_admin(self, client):
        """Test admin can update any booking."""
        start = datetime.utcnow() + timedelta(days=3)
        end = start + timedelta(hours=2)
        token_alice = _token_for(1, "alice", "regular_user")
        token_admin = _token_for(2, "bob", "admin")

        # Create booking as alice
        response = client.post(
            "/bookings",
            json={
                "user_id": 1,
                "room_id": 1,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        booking_id = response.json()["id"]

        # Update as admin
        response = client.put(
            f"/bookings/{booking_id}",
            json={"room_id": 2},
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 200

    def test_update_booking_unauthorized(self, client):
        """Test user cannot update another user's booking."""
        start = datetime.utcnow() + timedelta(days=4)
        end = start + timedelta(hours=2)
        token_alice = _token_for(1, "alice", "regular_user")
        token_bob = _token_for(2, "bob", "regular_user")

        # Create booking as alice
        response = client.post(
            "/bookings",
            json={
                "user_id": 1,
                "room_id": 1,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        booking_id = response.json()["id"]

        # Try to update as different user (bob as regular user, not admin)
        response = client.put(
            f"/bookings/{booking_id}",
            json={"room_id": 2},
            headers={"Authorization": f"Bearer {token_bob}"},
        )
        assert response.status_code == 403

    def test_update_booking_not_found(self, client):
        """Test update fails for non-existent booking."""
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.put(
            "/bookings/999",
            json={"room_id": 2},
            headers=headers,
        )
        assert response.status_code == 404


class TestCancelBooking:
    """Tests for canceling bookings."""

    def test_cancel_booking_as_owner(self, client):
        """Test owner can cancel their booking."""
        start = datetime.utcnow() + timedelta(days=5)
        end = start + timedelta(hours=2)
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        # Create booking
        response = client.post(
            "/bookings",
            json={
                "user_id": 1,
                "room_id": 1,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            headers=headers,
        )
        booking_id = response.json()["id"]

        # Cancel booking
        response = client.delete(f"/bookings/{booking_id}", headers=headers)
        assert response.status_code == 204

    def test_cancel_booking_unauthorized(self, client):
        """Test user cannot cancel another user's booking."""
        start = datetime.utcnow() + timedelta(days=6)
        end = start + timedelta(hours=2)
        token_alice = _token_for(1, "alice", "regular_user")
        token_bob = _token_for(2, "bob", "regular_user")

        # Create booking as alice
        response = client.post(
            "/bookings",
            json={
                "user_id": 1,
                "room_id": 1,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        booking_id = response.json()["id"]

        # Try to cancel as bob
        response = client.delete(
            f"/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {token_bob}"},
        )
        assert response.status_code == 403


class TestCheckAvailability:
    """Tests for checking room availability."""

    def test_check_availability_available(self, client):
        """Test availability check for available room."""
        start = datetime.utcnow() + timedelta(days=10)
        end = start + timedelta(hours=2)
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(
            f"/bookings/check-availability?room_id=3&start_time={start.isoformat()}&end_time={end.isoformat()}",
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["available"] is True

    def test_check_availability_unavailable(self, client):
        """Test availability check for booked room."""
        start = datetime.utcnow() + timedelta(days=11)
        end = start + timedelta(hours=2)
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        # Create booking
        client.post(
            "/bookings",
            json={
                "user_id": 1,
                "room_id": 3,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            headers=headers,
        )

        # Check availability for overlapping time
        response = client.get(
            f"/bookings/check-availability?room_id=3&start_time={start.isoformat()}&end_time={end.isoformat()}",
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["available"] is False

    def test_check_availability_invalid_time(self, client):
        """Test availability check with invalid time range."""
        start = datetime.utcnow()
        end = start - timedelta(hours=1)
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(
            f"/bookings/check-availability?room_id=1&start_time={start.isoformat()}&end_time={end.isoformat()}",
            headers=headers,
        )
        assert response.status_code == 400


class TestUserBookingHistory:
    """Tests for getting user booking history."""

    def test_get_own_booking_history(self, client):
        """Test user can view their own booking history."""
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/bookings/user/alice", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_other_user_history_as_admin(self, client):
        """Test admin can view any user's booking history."""
        token = _token_for(2, "bob", "admin")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/bookings/user/alice", headers=headers)
        assert response.status_code == 200

    def test_get_other_user_history_unauthorized(self, client):
        """Test regular user cannot view other user's booking history."""
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/bookings/user/bob", headers=headers)
        assert response.status_code == 403

    def test_get_booking_history_user_not_found(self, client):
        """Test getting history for non-existent user."""
        token = _token_for(2, "bob", "admin")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/bookings/user/nonexistent", headers=headers)
        assert response.status_code == 404
