"""
Comprehensive Tests for Reviews Service

This module contains unit tests for all Reviews Service API endpoints.
"""

from __future__ import annotations

import asyncio
import os
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from reviews_service.database import Base, get_session
from reviews_service.main import get_app
from reviews_service.models import Review, Room, User


TEST_SECRET = "test-secret-key"
ALGORITHM = "HS256"


def _token_for(user_id: int, username: str, role: str) -> str:
    """Generate JWT token for testing."""
    return jwt.encode({"sub": str(user_id), "username": username, "role": role}, TEST_SECRET, algorithm=ALGORITHM)


@pytest.fixture(scope="module")
def async_engine():
    """Create async database engine for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///./test_reviews.db", future=True)
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
                    User(id=3, username="moderator", role="moderator"),
                    User(id=4, username="dave", role="auditor_readonly"),
                    User(id=5, username="charlie", role="facility_manager"),
                ]
            )
            session.add_all([Room(id=1, name="Conf A"), Room(id=2, name="Conf B")])
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
        assert data["service"] == "reviews"


class TestCreateReview:
    """Tests for creating reviews."""

    def test_create_review_success(self, client):
        """Test successful review creation."""
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/reviews",
            json={
                "room_id": 1,
                "rating": 5,
                "comment": "Excellent room with great equipment!",
            },
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"]
        assert data["rating"] == 5
        assert data["comment"] == "Excellent room with great equipment!"
        assert data["flagged"] is False
        assert data["user"]["username"] == "alice"

    def test_create_review_sanitizes_html(self, client):
        """Test review comment is sanitized to remove HTML."""
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/reviews",
            json={
                "room_id": 1,
                "rating": 4,
                "comment": "<script>alert('xss')</script>Great room!",
            },
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "<script>" not in data["comment"]
        assert "Great room!" in data["comment"]

    def test_create_review_invalid_rating(self, client):
        """Test review creation fails with invalid rating."""
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        # Rating too high
        response = client.post(
            "/reviews",
            json={
                "room_id": 1,
                "rating": 6,
                "comment": "Nice room",
            },
            headers=headers,
        )
        assert response.status_code == 422

        # Rating too low
        response = client.post(
            "/reviews",
            json={
                "room_id": 1,
                "rating": 0,
                "comment": "Nice room",
            },
            headers=headers,
        )
        assert response.status_code == 422

    def test_create_review_empty_comment(self, client):
        """Test review creation fails with empty comment."""
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/reviews",
            json={
                "room_id": 1,
                "rating": 5,
                "comment": "",
            },
            headers=headers,
        )
        assert response.status_code == 422

    def test_create_review_room_not_found(self, client):
        """Test review creation fails for non-existent room."""
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/reviews",
            json={
                "room_id": 999,
                "rating": 5,
                "comment": "Great room",
            },
            headers=headers,
        )
        assert response.status_code == 404
        assert "room" in response.json()["detail"].lower()

    def test_create_review_readonly_forbidden(self, client):
        """Test auditor readonly cannot create reviews."""
        token = _token_for(4, "dave", "auditor_readonly")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/reviews",
            json={
                "room_id": 1,
                "rating": 5,
                "comment": "Nice room",
            },
            headers=headers,
        )
        assert response.status_code == 403

    def test_create_review_as_facility_manager(self, client):
        """Test facility manager can create reviews."""
        token = _token_for(5, "charlie", "facility_manager")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/reviews",
            json={
                "room_id": 1,
                "rating": 4,
                "comment": "Good room",
            },
            headers=headers,
        )
        assert response.status_code == 201


class TestUpdateReview:
    """Tests for updating reviews."""

    def test_update_review_as_owner(self, client):
        """Test owner can update their review."""
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        # Create review
        response = client.post(
            "/reviews",
            json={
                "room_id": 2,
                "rating": 3,
                "comment": "Average room",
            },
            headers=headers,
        )
        review_id = response.json()["id"]

        # Update review
        response = client.put(
            f"/reviews/{review_id}",
            json={
                "rating": 4,
                "comment": "Actually a good room after second visit",
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 4
        assert data["comment"] == "Actually a good room after second visit"

    def test_update_review_as_admin(self, client):
        """Test admin can update any review."""
        token_alice = _token_for(1, "alice", "regular_user")
        token_admin = _token_for(2, "bob", "admin")

        # Create review as alice
        response = client.post(
            "/reviews",
            json={
                "room_id": 2,
                "rating": 5,
                "comment": "Perfect room",
            },
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        review_id = response.json()["id"]

        # Update as admin
        response = client.put(
            f"/reviews/{review_id}",
            json={
                "rating": 4,
                "comment": "Updated by admin",
            },
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 200

    def test_update_review_unauthorized(self, client):
        """Test user cannot update another user's review."""
        token_alice = _token_for(1, "alice", "regular_user")
        token_charlie = _token_for(5, "charlie", "regular_user")

        # Create review as alice
        response = client.post(
            "/reviews",
            json={
                "room_id": 2,
                "rating": 4,
                "comment": "Good room",
            },
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        review_id = response.json()["id"]

        # Try to update as charlie
        response = client.put(
            f"/reviews/{review_id}",
            json={
                "rating": 2,
                "comment": "Bad room",
            },
            headers={"Authorization": f"Bearer {token_charlie}"},
        )
        assert response.status_code == 403

    def test_update_review_not_found(self, client):
        """Test update fails for non-existent review."""
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.put(
            "/reviews/999",
            json={
                "rating": 5,
                "comment": "Great",
            },
            headers=headers,
        )
        assert response.status_code == 404


class TestDeleteReview:
    """Tests for deleting reviews."""

    def test_delete_review_as_owner(self, client):
        """Test owner can delete their review."""
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        # Create review
        response = client.post(
            "/reviews",
            json={
                "room_id": 1,
                "rating": 3,
                "comment": "Okay room",
            },
            headers=headers,
        )
        review_id = response.json()["id"]

        # Delete review
        response = client.delete(f"/reviews/{review_id}", headers=headers)
        assert response.status_code == 204

    def test_delete_review_as_moderator(self, client):
        """Test moderator can delete any review."""
        token_alice = _token_for(1, "alice", "regular_user")
        token_mod = _token_for(3, "moderator", "moderator")

        # Create review as alice
        response = client.post(
            "/reviews",
            json={
                "room_id": 1,
                "rating": 1,
                "comment": "Terrible room",
            },
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        review_id = response.json()["id"]

        # Delete as moderator
        response = client.delete(
            f"/reviews/{review_id}",
            headers={"Authorization": f"Bearer {token_mod}"},
        )
        assert response.status_code == 204

    def test_delete_review_as_admin(self, client):
        """Test admin can delete any review."""
        token_alice = _token_for(1, "alice", "regular_user")
        token_admin = _token_for(2, "bob", "admin")

        # Create review as alice
        response = client.post(
            "/reviews",
            json={
                "room_id": 1,
                "rating": 2,
                "comment": "Poor room",
            },
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        review_id = response.json()["id"]

        # Delete as admin
        response = client.delete(
            f"/reviews/{review_id}",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 204

    def test_delete_review_unauthorized(self, client):
        """Test user cannot delete another user's review."""
        token_alice = _token_for(1, "alice", "regular_user")
        token_charlie = _token_for(5, "charlie", "regular_user")

        # Create review as alice
        response = client.post(
            "/reviews",
            json={
                "room_id": 1,
                "rating": 4,
                "comment": "Nice room",
            },
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        review_id = response.json()["id"]

        # Try to delete as charlie
        response = client.delete(
            f"/reviews/{review_id}",
            headers={"Authorization": f"Bearer {token_charlie}"},
        )
        assert response.status_code == 403


class TestGetReviewsForRoom:
    """Tests for getting reviews for a room."""

    def test_get_reviews_for_room(self, client):
        """Test getting all reviews for a room."""
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        # Create reviews
        client.post(
            "/reviews",
            json={"room_id": 1, "rating": 5, "comment": "Excellent!"},
            headers=headers,
        )
        client.post(
            "/reviews",
            json={"room_id": 1, "rating": 4, "comment": "Very good"},
            headers=headers,
        )

        # Get reviews
        response = client.get("/reviews/room/1", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert all(r["room_id"] == 1 for r in data)

    def test_get_reviews_with_min_rating_filter(self, client):
        """Test getting reviews with minimum rating filter."""
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        # Create reviews with different ratings
        client.post(
            "/reviews",
            json={"room_id": 2, "rating": 5, "comment": "Excellent!"},
            headers=headers,
        )
        client.post(
            "/reviews",
            json={"room_id": 2, "rating": 3, "comment": "Average"},
            headers=headers,
        )
        client.post(
            "/reviews",
            json={"room_id": 2, "rating": 2, "comment": "Poor"},
            headers=headers,
        )

        # Get reviews with min_rating=4
        response = client.get("/reviews/room/2?min_rating=4", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert all(r["rating"] >= 4 for r in data)

    def test_get_reviews_flagged_only(self, client):
        """Test getting only flagged reviews."""
        token = _token_for(1, "alice", "regular_user")
        headers = {"Authorization": f"Bearer {token}"}

        # Create review and flag it
        response = client.post(
            "/reviews",
            json={"room_id": 1, "rating": 1, "comment": "Terrible!"},
            headers=headers,
        )
        review_id = response.json()["id"]
        client.post(f"/reviews/{review_id}/flag", headers=headers)

        # Get flagged reviews only
        response = client.get("/reviews/room/1?flagged_only=true", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert all(r["flagged"] is True for r in data)


class TestFlagReview:
    """Tests for flagging reviews."""

    def test_flag_review_as_regular_user(self, client):
        """Test regular user can flag a review."""
        token_alice = _token_for(1, "alice", "regular_user")
        token_charlie = _token_for(5, "charlie", "regular_user")

        # Create review as alice
        response = client.post(
            "/reviews",
            json={"room_id": 1, "rating": 1, "comment": "Inappropriate content"},
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        review_id = response.json()["id"]

        # Flag as charlie
        response = client.post(
            f"/reviews/{review_id}/flag",
            headers={"Authorization": f"Bearer {token_charlie}"},
        )
        assert response.status_code == 200
        assert response.json()["flagged"] is True

    def test_flag_review_as_moderator(self, client):
        """Test moderator can flag a review."""
        token_alice = _token_for(1, "alice", "regular_user")
        token_mod = _token_for(3, "moderator", "moderator")

        # Create review as alice
        response = client.post(
            "/reviews",
            json={"room_id": 1, "rating": 2, "comment": "Bad content"},
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        review_id = response.json()["id"]

        # Flag as moderator
        response = client.post(
            f"/reviews/{review_id}/flag",
            headers={"Authorization": f"Bearer {token_mod}"},
        )
        assert response.status_code == 200
        assert response.json()["flagged"] is True

    def test_flag_review_readonly_forbidden(self, client):
        """Test auditor readonly cannot flag reviews."""
        token_alice = _token_for(1, "alice", "regular_user")
        token_auditor = _token_for(4, "dave", "auditor_readonly")

        # Create review as alice
        response = client.post(
            "/reviews",
            json={"room_id": 1, "rating": 3, "comment": "Average"},
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        review_id = response.json()["id"]

        # Try to flag as auditor
        response = client.post(
            f"/reviews/{review_id}/flag",
            headers={"Authorization": f"Bearer {token_auditor}"},
        )
        assert response.status_code == 403


class TestUnflagReview:
    """Tests for unflagging reviews."""

    def test_unflag_review_as_moderator(self, client):
        """Test moderator can unflag a review."""
        token_alice = _token_for(1, "alice", "regular_user")
        token_mod = _token_for(3, "moderator", "moderator")

        # Create and flag review
        response = client.post(
            "/reviews",
            json={"room_id": 1, "rating": 3, "comment": "Okay"},
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        review_id = response.json()["id"]
        client.post(f"/reviews/{review_id}/flag", headers={"Authorization": f"Bearer {token_alice}"})

        # Unflag as moderator
        response = client.post(
            f"/reviews/{review_id}/unflag",
            headers={"Authorization": f"Bearer {token_mod}"},
        )
        assert response.status_code == 200
        assert response.json()["flagged"] is False

    def test_unflag_review_as_admin(self, client):
        """Test admin can unflag a review."""
        token_alice = _token_for(1, "alice", "regular_user")
        token_admin = _token_for(2, "bob", "admin")

        # Create and flag review
        response = client.post(
            "/reviews",
            json={"room_id": 1, "rating": 4, "comment": "Good"},
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        review_id = response.json()["id"]
        client.post(f"/reviews/{review_id}/flag", headers={"Authorization": f"Bearer {token_alice}"})

        # Unflag as admin
        response = client.post(
            f"/reviews/{review_id}/unflag",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 200
        assert response.json()["flagged"] is False

    def test_unflag_review_unauthorized(self, client):
        """Test regular user cannot unflag a review."""
        token_alice = _token_for(1, "alice", "regular_user")
        token_charlie = _token_for(5, "charlie", "regular_user")

        # Create and flag review
        response = client.post(
            "/reviews",
            json={"room_id": 1, "rating": 2, "comment": "Not great"},
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        review_id = response.json()["id"]
        client.post(f"/reviews/{review_id}/flag", headers={"Authorization": f"Bearer {token_alice}"})

        # Try to unflag as regular user
        response = client.post(
            f"/reviews/{review_id}/unflag",
            headers={"Authorization": f"Bearer {token_charlie}"},
        )
        assert response.status_code == 403
