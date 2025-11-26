"""
SQLAlchemy models for reviews service.

Includes lightweight User and Room models to join against existing data.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from reviews_service.database import Base


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

    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Room(Base):
    """
    Minimal room model to allow review references.

    The Rooms service owns room lifecycle; this table stores identifiers and names.
    """

    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="room")

    def __repr__(self) -> str:
        return f"<Room {self.name}>"


class Review(Base):
    """
    Review entity for rooms.
    """

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship("User", back_populates="reviews")
    room: Mapped[Room] = relationship("Room", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<Review {self.id} room={self.room_id} user={self.user_id}>"
