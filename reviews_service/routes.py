"""
Reviews API router.

Supports CRUD, flagging, and filtering of room reviews with role-based controls.
"""

from __future__ import annotations

from typing import Optional

import bleach
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from reviews_service import schemas
from reviews_service.auth import ensure_not_readonly, get_current_user, is_owner_or_admin, require_role
from reviews_service.database import get_session
from reviews_service.models import Review, Room, User


router = APIRouter(prefix="/reviews", tags=["reviews"])


def _sanitize_comment(comment: str) -> str:
    """Remove scripts/unsafe tags while preserving simple formatting."""
    return bleach.clean(comment, strip=True)


async def _get_review(session: AsyncSession, review_id: int) -> Optional[Review]:
    review = await session.get(
        Review,
        review_id,
        options=[selectinload(Review.user)],
    )
    return review


@router.post("", response_model=schemas.ReviewOut, status_code=status.HTTP_201_CREATED)
async def create_review(
    request: Request,
    payload: schemas.ReviewCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> schemas.ReviewOut:
    """Create a review for a room."""
    ensure_not_readonly(current_user)
    if current_user.role not in {"regular_user", "facility_manager", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not permitted to create reviews")

    room = await session.get(Room, payload.room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    review = Review(
        room_id=payload.room_id,
        user_id=current_user.id,
        rating=payload.rating,
        comment=_sanitize_comment(payload.comment),
        flagged=False,
    )
    session.add(review)
    await session.commit()
    await session.refresh(review)
    await session.refresh(review, attribute_names=["user"])
    return review


@router.put("/{review_id}", response_model=schemas.ReviewOut)
async def update_review(
    review_id: int,
    payload: schemas.ReviewUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> schemas.ReviewOut:
    """Update an existing review."""
    ensure_not_readonly(current_user)
    review = await _get_review(session, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    if not is_owner_or_admin(review.user_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to edit this review")

    review.rating = payload.rating
    review.comment = _sanitize_comment(payload.comment)
    await session.commit()
    await session.refresh(review)
    await session.refresh(review, attribute_names=["user"])
    return review


@router.delete("/{review_id}", status_code=status.HTTP_200_OK)
async def delete_review(
    review_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Delete a review (owner, moderator, admin)."""
    ensure_not_readonly(current_user)
    review = await _get_review(session, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    if current_user.role not in {"admin", "moderator"} and not is_owner_or_admin(review.user_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete this review")

    await session.delete(review)
    await session.commit()
    return {"message": f"Review {review_id} deleted successfully"}


@router.get("/room/{room_id}", response_model=list[schemas.ReviewOut])
async def get_reviews_for_room(
    room_id: int,
    min_rating: Optional[int] = Query(default=None, ge=1, le=5),
    flagged_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[schemas.ReviewOut]:
    """Retrieve reviews for a room with optional filters."""
    stmt = select(Review).where(Review.room_id == room_id).options(selectinload(Review.user))
    if min_rating is not None:
        stmt = stmt.where(Review.rating >= min_rating)
    if flagged_only:
        stmt = stmt.where(Review.flagged.is_(True))

    result = await session.execute(stmt)
    return list(result.scalars())


@router.post("/{review_id}/flag", response_model=schemas.ReviewOut)
async def flag_review(
    review_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> schemas.ReviewOut:
    """Flag a review as inappropriate."""
    ensure_not_readonly(current_user)
    if current_user.role not in {"regular_user", "moderator", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not permitted to flag reviews")

    review = await _get_review(session, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    review.flagged = True
    await session.commit()
    await session.refresh(review)
    await session.refresh(review, attribute_names=["user"])
    return review


@router.post(
    "/{review_id}/unflag",
    response_model=schemas.ReviewOut,
    dependencies=[Depends(require_role("moderator", "admin"))],
)
async def unflag_review(
    review_id: int,
    session: AsyncSession = Depends(get_session),
) -> schemas.ReviewOut:
    """Remove a flag from a review."""
    review = await _get_review(session, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    review.flagged = False
    await session.commit()
    await session.refresh(review)
    await session.refresh(review, attribute_names=["user"])
    return review
