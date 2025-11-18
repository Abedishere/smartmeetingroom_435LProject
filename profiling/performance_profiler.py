"""
Performance Profiling Script

This script profiles the performance of API endpoints using cProfile.
"""

import cProfile
import pstats
import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from users_service.app import create_app as create_users_app
from rooms_service.app import create_app as create_rooms_app


def profile_users_service():
    """Profile Users Service endpoints."""
    print("=" * 80)
    print("PROFILING USERS SERVICE")
    print("=" * 80)

    app = create_users_app()
    client = app.test_client()

    # Profile user registration
    pr = cProfile.Profile()
    pr.enable()

    for _ in range(100):
        client.post('/api/users/register', json={
            'name': 'Test User',
            'username': f'testuser_{_}',
            'password': 'TestPass123',
            'email': f'test{_}@example.com'
        })

    pr.disable()

    print("\n--- User Registration (100 requests) ---")
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)
    print(s.getvalue())

    # Profile user login
    pr = cProfile.Profile()
    pr.enable()

    for _ in range(100):
        client.post('/api/users/login', json={
            'username': 'testuser_0',
            'password': 'TestPass123'
        })

    pr.disable()

    print("\n--- User Login (100 requests) ---")
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)
    print(s.getvalue())


def profile_rooms_service():
    """Profile Rooms Service endpoints."""
    print("=" * 80)
    print("PROFILING ROOMS SERVICE")
    print("=" * 80)

    app = create_rooms_app()

    # Note: Rooms service requires authentication
    # This is a simplified profiling example
    print("\nRooms service profiling requires authentication setup.")
    print("In production, profile with authenticated requests.")


if __name__ == '__main__':
    profile_users_service()
    profile_rooms_service()
