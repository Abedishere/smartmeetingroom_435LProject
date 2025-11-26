"""
Pydantic schemas for the reviews service.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserOut(BaseModel):
    """Lightweight user representation returned in responses."""

    id: int
    username: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class ReviewBase(BaseModel):
    """Shared fields for reviews."""

    rating: int = Field(ge=1, le=5)
    comment: str

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("comment must not be empty")
        return value


class ReviewCreate(ReviewBase):
    """Review creation payload."""

    room_id: int


class ReviewUpdate(ReviewBase):
    """Review update payload."""

    pass


class ReviewOut(BaseModel):
    """Review response schema."""

    id: int
    room_id: int
    user_id: int
    rating: int
    comment: str
    flagged: bool
    created_at: datetime
    user: Optional[UserOut] = None

    model_config = ConfigDict(from_attributes=True)
