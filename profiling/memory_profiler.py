"""
Memory Profiling Script

This script profiles memory usage of API endpoints.
Run with: python -m memory_profiler memory_profiler.py
"""

import sys
import os
from memory_profiler import profile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from users_service.app import create_app as create_users_app
from users_service.application.services import UserService
from users_service.application.validators import validate_username, validate_password


@profile
def test_user_service_memory():
    """Profile memory usage of user service operations."""
    app = create_users_app()

    with app.app_context():
        # Create multiple users
        for i in range(50):
            try:
                user = UserService.create_user(
                    name=f'User {i}',
                    username=f'user{i}',
                    password='TestPass123',
                    email=f'user{i}@example.com'
                )
            except Exception:
                pass

        # Query all users
        users = UserService.get_all_users()

        # Query specific users
        for i in range(10):
            try:
                user = UserService.get_user_by_username(f'user{i}')
            except Exception:
                pass


@profile
def test_validation_memory():
    """Profile memory usage of validation functions."""
    # Test validation functions
    for i in range(1000):
        try:
            validate_username(f'testuser{i}')
            validate_password(f'TestPass{i}')
        except Exception:
            pass


if __name__ == '__main__':
    print("=" * 80)
    print("MEMORY PROFILING")
    print("=" * 80)
    print("\nUser Service Memory Profile:")
    test_user_service_memory()
    print("\nValidation Functions Memory Profile:")
    test_validation_memory()
