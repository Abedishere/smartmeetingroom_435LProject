"""
Authentication and Authorization for Rooms Service

This module provides decorators and utilities for authentication and authorization.
It verifies JWT tokens and checks user roles by calling the Users Service.
"""

from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
import requests
import os


USERS_SERVICE_URL = os.getenv('USERS_SERVICE_URL', 'http://users_service:5001')


def get_user_from_token():
    """
    Get user information from JWT token by calling Users Service.

    Returns:
        dict: User data or None if not found

    Raises:
        Exception: If unable to verify user
    """
    verify_jwt_in_request()
    user_id = get_jwt_identity()

    # Get the current token
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else None

    if not token:
        return None

    try:
        # Call Users Service to get user details
        response = requests.get(
            f'{USERS_SERVICE_URL}/api/users/me',
            headers={'Authorization': f'Bearer {token}'},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            return data.get('user')

        return None
    except requests.RequestException as e:
        # If Users Service is unavailable, raise an error
        raise Exception(f"Unable to verify user: {str(e)}")


def role_required(*allowed_roles):
    """
    Decorator to require specific roles for accessing an endpoint.

    Args:
        *allowed_roles: Variable number of role names that are allowed

    Returns:
        function: Decorated function

    Example:
        @role_required('admin', 'facility_manager')
        def some_route():
            pass
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                user = get_user_from_token()

                if not user:
                    return jsonify({'error': 'User not found'}), 404

                if user.get('role') not in allowed_roles:
                    return jsonify({
                        'error': 'Insufficient permissions',
                        'required_roles': list(allowed_roles),
                        'your_role': user.get('role')
                    }), 403

                return fn(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        return wrapper
    return decorator
