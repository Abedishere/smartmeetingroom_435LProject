"""
FastAPI application entrypoint for bookings service.
"""

from __future__ import annotations

import json
import time
import logging
from datetime import datetime

from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from bookings_service.database import Base, engine
from bookings_service.routes import router


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

app = FastAPI(title="Smart Meeting Room - Bookings Service")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Structured logging setup
logger = logging.getLogger('bookings_service')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with structured JSON format."""
    start_time = time.time()

    response = await call_next(request)

    if request.url.path == '/favicon.ico':
        return response

    duration = time.time() - start_time

    # Extract user info from request state if available
    user_id = getattr(request.state, 'user_id', None)
    username = getattr(request.state, 'username', None)

    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'bookings_service',
        'method': request.method,
        'path': request.url.path,
        'status_code': response.status_code,
        'duration_ms': round(duration * 1000, 2),
        'ip': request.client.host if request.client else None,
        'user_agent': request.headers.get('User-Agent', ''),
        'user_id': user_id,
        'username': username
    }

    logger.info(json.dumps(log_data))
    return response


@app.on_event("startup")
async def startup() -> None:
    """Initialize database schema on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "bookings"}


def get_app() -> FastAPI:
    """
    Expose app for external tools and tests.

    Returns:
        FastAPI: Configured application.
    """
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("bookings_service.main:app", host="0.0.0.0", port=5003, reload=True)
