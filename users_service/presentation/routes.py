"""
Users Service API Routes

This module defines the REST API endpoints for user management.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from users_service.application.services import UserService
from users_service.application.validators import ValidationError
from users_service.application.auth import role_required, get_current_user
from users_service.domain.models import User

users_bp = Blueprint('users', __name__, url_prefix='/api/users')


@users_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON response with service status
    """
    return jsonify({'status': 'healthy', 'service': 'users'}), 200


@users_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.

    Request Body:
        - name (str): User's full name
        - username (str): Unique username
        - password (str): User's password
        - email (str): User's email address
        - role (str, optional): User role (default: regular_user)

    Returns:
        JSON response with created user data

    Status Codes:
        201: User created successfully
        400: Validation error or user already exists
        500: Internal server error
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Extract required fields
        name = data.get('name')
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        role = data.get('role', 'regular_user')

        # Validate required fields
        if not all([name, username, password, email]):
            return jsonify({
                'error': 'Missing required fields',
                'required': ['name', 'username', 'password', 'email']
            }), 400

        # Create user
        user = UserService.create_user(name, username, password, email, role)

        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201

    except ValidationError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@users_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate a user and return JWT token.

    Request Body:
        - username (str): Username
        - password (str): Password

    Returns:
        JSON response with access token and user data

    Status Codes:
        200: Authentication successful
        400: Missing credentials
        401: Invalid credentials
        500: Internal server error
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({
                'error': 'Missing credentials',
                'required': ['username', 'password']
            }), 400

        # Authenticate user
        user = UserService.authenticate_user(username, password)

        if not user:
            return jsonify({'error': 'Invalid username or password'}), 401

        # Create access token
        access_token = create_access_token(identity=user.id)

        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200

    except ValidationError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@users_bp.route('/', methods=['GET'])
@jwt_required()
@role_required('admin', 'auditor')
def get_all_users():
    """
    Get all users (Admin and Auditor only).

    Headers:
        - Authorization: Bearer <access_token>

    Returns:
        JSON response with list of all users

    Status Codes:
        200: Success
        403: Insufficient permissions
        500: Internal server error
    """
    try:
        users = UserService.get_all_users()
        return jsonify({
            'users': [user.to_dict() for user in users],
            'count': len(users)
        }), 200

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@users_bp.route('/<string:username>', methods=['GET'])
@jwt_required()
def get_user(username):
    """
    Get a specific user by username.

    Admin can view any user, regular users can only view their own profile.

    Headers:
        - Authorization: Bearer <access_token>

    Path Parameters:
        - username (str): Username to retrieve

    Returns:
        JSON response with user data

    Status Codes:
        200: Success
        403: Insufficient permissions
        404: User not found
        500: Internal server error
    """
    try:
        current_user = get_current_user()

        # Check permissions: admin can view anyone, users can view themselves
        if current_user.role not in ['admin', 'auditor'] and current_user.username != username:
            return jsonify({
                'error': 'You can only view your own profile'
            }), 403

        user = UserService.get_user_by_username(username)

        if not user:
            return jsonify({'error': f"User '{username}' not found"}), 404

        return jsonify({'user': user.to_dict()}), 200

    except ValidationError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """
    Update user information.

    Admin can update any user, regular users can only update their own profile.

    Headers:
        - Authorization: Bearer <access_token>

    Path Parameters:
        - user_id (int): User ID to update

    Request Body (all optional):
        - name (str): Updated name
        - email (str): Updated email
        - role (str): Updated role (admin only)
        - password (str): Updated password

    Returns:
        JSON response with updated user data

    Status Codes:
        200: Update successful
        400: Validation error
        403: Insufficient permissions
        404: User not found
        500: Internal server error
    """
    try:
        current_user = get_current_user()

        # Check permissions
        if current_user.role != 'admin' and current_user.id != user_id:
            return jsonify({
                'error': 'You can only update your own profile'
            }), 403

        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Only admin can change roles
        if 'role' in data and current_user.role != 'admin':
            return jsonify({
                'error': 'Only admins can change user roles'
            }), 403

        # Update user
        user = UserService.update_user(user_id, **data)

        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200

    except ValidationError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 404 if 'not found' in str(e) else 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def delete_user(user_id):
    """
    Delete a user account (Admin only).

    Headers:
        - Authorization: Bearer <access_token>

    Path Parameters:
        - user_id (int): User ID to delete

    Returns:
        JSON response confirming deletion

    Status Codes:
        200: Deletion successful
        403: Insufficient permissions
        404: User not found
        500: Internal server error
    """
    try:
        UserService.delete_user(user_id)

        return jsonify({
            'message': f'User with ID {user_id} deleted successfully'
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404 if 'not found' in str(e) else 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@users_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_profile():
    """
    Get current authenticated user's profile.

    Headers:
        - Authorization: Bearer <access_token>

    Returns:
        JSON response with current user data

    Status Codes:
        200: Success
        404: User not found
        500: Internal server error
    """
    try:
        current_user = get_current_user()

        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({'user': current_user.to_dict()}), 200

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
