"""
Tests for the FastAPI bookings and reviews service.
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

from booking_review_service.database import Base, get_session
from booking_review_service.main import get_app
from booking_review_service.models import Booking, Review, Room, User


TEST_SECRET = "change-me-in-production"
ALGORITHM = "HS256"


def _token_for(user_id: int, username: str, role: str) -> str:
    return jwt.encode({"sub": str(user_id), "username": username, "role": role}, TEST_SECRET, algorithm=ALGORITHM)


@pytest.fixture(scope="module")
def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///./test_booking_review.db", future=True)
    return engine


@pytest.fixture(scope="module")
def async_session_factory(async_engine):
    return async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="session", autouse=True)
def setup_env():
    os.environ["JWT_SECRET_KEY"] = TEST_SECRET
    os.environ["JWT_ALGORITHM"] = ALGORITHM


@pytest.fixture(scope="module")
def app(async_engine, async_session_factory, setup_env):
    """
    Configure app with in-memory database and dependency overrides.
    """
    app = get_app()

    async def init_models():
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with async_session_factory() as session:
            # Seed users and rooms
            session.add_all(
                [
                    User(id=1, username="alice", role="regular_user"),
                    User(id=2, username="bob", role="admin"),
                    User(id=3, username="mod", role="moderator"),
                    User(id=4, username="svc", role="service_account"),
                    User(id=5, username="audit", role="auditor_readonly"),
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

        def delete(self, url: str, **kwargs):
            return self.request("DELETE", url, **kwargs)

    client = SyncClient()
    try:
        yield client
    finally:
        loop.run_until_complete(async_client.aclose())


class TestBookings:
    def test_create_booking_and_conflict(self, client):
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
        assert response.status_code == 201, response.text
        booking_id = response.json()["id"]
        assert booking_id

        # overlapping booking should fail
        response = client.post(
            "/bookings",
            json={
                "user_id": 2,
                "room_id": 1,
                "start_time": (start + timedelta(minutes=30)).isoformat(),
                "end_time": (end + timedelta(hours=1)).isoformat(),
            },
            headers=headers,
        )
        assert response.status_code == 409


class TestReviews:
    def test_review_flag_lifecycle_with_roles(self, client):
        token_user = _token_for(1, "alice", "regular_user")
        token_mod = _token_for(3, "mod", "moderator")
        headers_user = {"Authorization": f"Bearer {token_user}"}
        headers_mod = {"Authorization": f"Bearer {token_mod}"}

        # create review
        response = client.post(
            "/reviews",
            json={"room_id": 1, "rating": 4, "comment": "Nice room"},
            headers=headers_user,
        )
        assert response.status_code == 201, response.text
        review_id = response.json()["id"]

        # regular user can flag
        response = client.post(f"/reviews/{review_id}/flag", headers=headers_user)
        assert response.status_code == 200
        assert response.json()["flagged"] is True

        # moderator can unflag
        response = client.post(f"/reviews/{review_id}/unflag", headers=headers_mod)
        assert response.status_code == 200
        assert response.json()["flagged"] is False

        # moderator can delete
        response = client.delete(f"/reviews/{review_id}", headers=headers_mod)
        assert response.status_code == 204

        # ensure it is gone
        response = client.get("/reviews/room/1", headers=headers_mod)
        assert response.status_code == 200
        assert not any(r["id"] == review_id for r in response.json())
