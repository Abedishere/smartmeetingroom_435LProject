"""
Bookings API router.

Provides CRUD operations and availability checks with RBAC enforcement.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bookings_service import schemas
from bookings_service.auth import ensure_not_readonly, get_current_user, is_owner_or_admin, require_role
from bookings_service.database import get_session
from bookings_service.models import Booking, Room, User


router = APIRouter(prefix="/bookings", tags=["bookings"])


async def _get_user(
    session: AsyncSession, user_id: Optional[int] = None, username: Optional[str] = None
) -> Optional[User]:
    if user_id is not None:
        return await session.get(User, user_id)
    if username:
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    return None


async def _get_room(session: AsyncSession, room_id: int) -> Optional[Room]:
    return await session.get(Room, room_id)


def _overlaps(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    """
    Determine whether two time intervals overlap.
    """
    return start_a < end_b and end_a > start_b


async def _has_conflict(
    session: AsyncSession, room_id: int, start_time: datetime, end_time: datetime, exclude_booking_id: Optional[int] = None
) -> bool:
    stmt = select(Booking).where(
        Booking.room_id == room_id,
        Booking.status != "cancelled",
    )
    if exclude_booking_id:
        stmt = stmt.where(Booking.id != exclude_booking_id)
    result = await session.execute(stmt)
    for booking in result.scalars():
        if _overlaps(start_time, end_time, booking.start_time, booking.end_time):
            return True
    return False


@router.get(
    "",
    response_model=list[schemas.BookingOut],
    dependencies=[Depends(require_role("admin", "facility_manager", "auditor_readonly"))],
)
async def list_bookings(session: AsyncSession = Depends(get_session)) -> list[schemas.BookingOut]:
    """Return all bookings with related user and room data."""
    stmt = select(Booking).options(selectinload(Booking.user), selectinload(Booking.room))
    result = await session.execute(stmt)
    return list(result.scalars())


@router.get("/check-availability", response_model=schemas.AvailabilityResponse)
async def check_availability(
    room_id: int = Query(..., description="Room identifier"),
    start_time: datetime = Query(..., description="Proposed start time"),
    end_time: datetime = Query(..., description="Proposed end time"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> schemas.AvailabilityResponse:
    """Check if a room is available for the given time window."""
    if end_time <= start_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_time must be after start_time")

    room = await _get_room(session, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    available = not await _has_conflict(session, room_id, start_time, end_time)
    return schemas.AvailabilityResponse(available=available)


@router.get(
    "/{booking_id}",
    response_model=schemas.BookingOut,
    dependencies=[Depends(require_role("admin", "facility_manager", "auditor_readonly"))],
)
async def get_booking(booking_id: int, session: AsyncSession = Depends(get_session)) -> schemas.BookingOut:
    """Return a booking by id."""
    booking = await session.get(
        Booking,
        booking_id,
        options=[selectinload(Booking.user), selectinload(Booking.room)],
    )
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return booking


@router.get("/user/{username}", response_model=list[schemas.BookingOut])
async def get_user_bookings(
    username: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[schemas.BookingOut]:
    """Return booking history for a specific user."""
    if current_user.username != username and current_user.role not in {"admin", "facility_manager", "auditor_readonly"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view these bookings")

    user = await _get_user(session, username=username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    stmt = (
        select(Booking)
        .where(Booking.user_id == user.id)
        .options(selectinload(Booking.user), selectinload(Booking.room))
    )
    result = await session.execute(stmt)
    return list(result.scalars())


@router.post("", response_model=schemas.BookingOut, status_code=status.HTTP_201_CREATED)
async def create_booking(
    request: Request,
    payload: schemas.BookingCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> schemas.BookingOut:
    """Create a new booking after validating conflicts and permissions."""
    ensure_not_readonly(current_user)

    if current_user.role not in {"regular_user", "facility_manager", "admin", "service_account"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not permitted to create bookings")

    if payload.user_id is None and not payload.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id or username is required")

    user = await _get_user(session, user_id=payload.user_id, username=payload.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    room = await _get_room(session, payload.room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if await _has_conflict(session, payload.room_id, payload.start_time, payload.end_time):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Room already booked for that time window")

    booking = Booking(
        user_id=user.id,
        room_id=room.id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        status="confirmed",
    )
    session.add(booking)
    await session.commit()
    await session.refresh(booking)
    # ensure relationships for response
    await session.refresh(booking, attribute_names=["user", "room"])
    return booking


@router.put("/{booking_id}", response_model=schemas.BookingOut)
async def update_booking(
    booking_id: int,
    payload: schemas.BookingUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> schemas.BookingOut:
    """Update booking time or room, ensuring no conflicts."""
    ensure_not_readonly(current_user)

    booking = await session.get(
        Booking,
        booking_id,
        options=[selectinload(Booking.user), selectinload(Booking.room)],
    )
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if not (is_owner_or_admin(booking.user_id, current_user) or current_user.role == "facility_manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify this booking")

    new_start = payload.start_time or booking.start_time
    new_end = payload.end_time or booking.end_time
    new_room_id = payload.room_id or booking.room_id

    room = await _get_room(session, new_room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if await _has_conflict(session, new_room_id, new_start, new_end, exclude_booking_id=booking.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Room already booked for that time window")

    booking.start_time = new_start
    booking.end_time = new_end
    booking.room_id = new_room_id
    await session.commit()
    await session.refresh(booking)
    await session.refresh(booking, attribute_names=["user", "room"])
    return booking


@router.delete("/{booking_id}", status_code=status.HTTP_200_OK)
async def cancel_booking(
    booking_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Cancel a booking."""
    ensure_not_readonly(current_user)

    booking = await session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if not (is_owner_or_admin(booking.user_id, current_user) or current_user.role == "facility_manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot cancel this booking")

    booking.status = "cancelled"
    await session.commit()
    return {"message": f"Booking {booking_id} cancelled successfully"}
