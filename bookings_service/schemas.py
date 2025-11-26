"""
Pydantic schemas for the bookings service.
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


class RoomOut(BaseModel):
    """Lightweight room representation returned in responses."""

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class BookingBase(BaseModel):
    """Shared booking attributes."""

    start_time: datetime
    end_time: datetime

    @field_validator("end_time")
    @classmethod
    def validate_time_window(cls, end_time: datetime, info):
        start_time = info.data.get("start_time") if hasattr(info, "data") else None
        if start_time and end_time <= start_time:
            raise ValueError("end_time must be after start_time")
        return end_time


class BookingCreate(BookingBase):
    """Payload for booking creation."""

    user_id: Optional[int] = Field(default=None)
    username: Optional[str] = Field(default=None)
    room_id: int


class BookingUpdate(BaseModel):
    """Payload for booking updates."""

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    room_id: Optional[int] = None

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, end_time: Optional[datetime], info):
        start_time = info.data.get("start_time") if hasattr(info, "data") else None
        if start_time and end_time and end_time <= start_time:
            raise ValueError("end_time must be after start_time")
        return end_time


class BookingOut(BaseModel):
    """Booking response schema."""

    id: int
    start_time: datetime
    end_time: datetime
    status: str
    created_at: datetime
    user: UserOut
    room: RoomOut

    model_config = ConfigDict(from_attributes=True)


class AvailabilityResponse(BaseModel):
    """Availability check response."""

    available: bool
