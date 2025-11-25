"""
FastAPI application entrypoint for bookings and reviews services.
"""

from __future__ import annotations

from fastapi import FastAPI

from booking_review_service.database import Base, engine
from booking_review_service.routers import bookings, reviews

app = FastAPI(title="Smart Meeting Room - Bookings & Reviews Service")


@app.on_event("startup")
async def startup() -> None:
    """Initialize database schema on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(bookings.router)
app.include_router(reviews.router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "bookings_reviews"}


def get_app() -> FastAPI:
    """
    Expose app for external tools and tests.

    Returns:
        FastAPI: Configured application.
    """
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("booking_review_service.main:app", host="0.0.0.0", port=8002, reload=True)
