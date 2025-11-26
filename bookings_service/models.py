"""
SQLAlchemy models for bookings service.

Includes lightweight User and Room models to join against existing data.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bookings_service.database import Base


class User(Base):
    """
    Minimal user model for authentication/authorization context.

    It is expected that the Users service manages users; this table mirrors
    essential fields to allow joins and foreign keys.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="regular_user")

    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Room(Base):
    """
    Minimal room model to allow booking references.

    The Rooms service owns room lifecycle; this table stores identifiers and names.
    """

    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="room")

    def __repr__(self) -> str:
        return f"<Room {self.name}>"


class Booking(Base):
    """
    Booking entity representing a room reservation.
    """

    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint(
            "room_id",
            "start_time",
            "end_time",
            name="uq_booking_room_time_window",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="confirmed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship("User", back_populates="bookings")
    room: Mapped[Room] = relationship("Room", back_populates="bookings")

    def __repr__(self) -> str:
        return f"<Booking {self.id} room={self.room_id} user={self.user_id}>"
