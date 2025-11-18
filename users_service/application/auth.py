"""
Authentication and Authorization

This module provides decorators and utilities for authentication and authorization.
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from users_service.domain.models import User


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
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)

            if not user:
                return jsonify({'error': 'User not found'}), 404

            if user.role not in allowed_roles:
                return jsonify({
                    'error': 'Insufficient permissions',
                    'required_roles': list(allowed_roles),
                    'your_role': user.role
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user():
    """
    Get the current authenticated user.

    Returns:
        User: Current user object or None
    """
    verify_jwt_in_request()
    user_id = get_jwt_identity()
    return User.query.get(user_id)
