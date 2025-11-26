"""
Authentication and authorization utilities.

Provides JWT-based authentication and role helpers for RBAC enforcement.
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from reviews_service.database import get_session
from reviews_service.models import User


def _jwt_secret() -> str:
    return os.getenv("JWT_SECRET_KEY", "change-me-in-production")


def _jwt_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256")


def _service_api_key() -> Optional[str]:
    return os.getenv("SERVICE_API_KEY")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


async def _get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
    x_service_account_key: Optional[str] = Header(default=None, alias="X-Service-Account-Key"),
) -> User:
    """
    Resolve the current user from JWT or service account API key.

    Args:
        token: Bearer token from the Authorization header.
        session: Database session.
        x_service_account_key: Optional internal API key for service-to-service calls.

    Returns:
        User: The authenticated user model.

    Raises:
        HTTPException: If authentication fails.
    """
    if x_service_account_key and _service_api_key() and x_service_account_key == _service_api_key():
        service_user = User(id=0, username="service_account", role="service_account")  # type: ignore[arg-type]
        return service_user

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")

    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[_jwt_algorithm()])
        user_id = payload.get("sub")
        role = payload.get("role")
        username = payload.get("username")
        if user_id is None or role is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except JWTError as exc:  # pragma: no cover - jose provides coverage
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user = await _get_user_by_id(session, int(user_id))
    if not user:
        # fallback to token contents for service account tokens without DB row
        user = User(id=int(user_id), username=username or "unknown", role=role)  # type: ignore[arg-type]
    return user


def require_role(*allowed_roles: str):
    """
    Dependency factory to enforce allowed roles.

    Args:
        allowed_roles: Accepted role names.

    Returns:
        Callable dependency that raises 403 on mismatch.
    """

    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return dependency


def ensure_not_readonly(user: User) -> None:
    """
    Raise if the user has read-only auditor role.
    """
    if user.role == "auditor_readonly":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Read-only role cannot perform this action")


def is_owner_or_admin(resource_user_id: int, current_user: User) -> bool:
    """
    Check whether the current user owns the resource or is an admin.

    Args:
        resource_user_id: Resource owner's user id.
        current_user: Authenticated user.

    Returns:
        bool: True if owner or admin.
    """
    return current_user.id == resource_user_id or current_user.role == "admin"
