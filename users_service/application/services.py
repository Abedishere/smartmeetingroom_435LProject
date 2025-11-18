"""
User Service Layer

This module contains business logic for user operations.
"""

from users_service.app import db
from users_service.domain.models import User
from users_service.application.validators import (
    validate_username, validate_password, validate_email_address,
    validate_role, validate_name, ValidationError
)
from sqlalchemy.exc import IntegrityError


class UserService:
    """Service class for user-related business logic."""

    @staticmethod
    def create_user(name, username, password, email, role='regular_user'):
        """
        Create a new user account.

        Args:
            name (str): User's full name
            username (str): Unique username
            password (str): User's password
            email (str): User's email address
            role (str): User role (default: regular_user)

        Returns:
            User: Created user object

        Raises:
            ValidationError: If input validation fails
            ValueError: If user already exists
        """
        # Validate inputs
        name = validate_name(name)
        username = validate_username(username)
        password = validate_password(password)
        email = validate_email_address(email)
        role = validate_role(role)

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            raise ValueError(f"Username '{username}' already exists")

        if User.query.filter_by(email=email).first():
            raise ValueError(f"Email '{email}' already registered")

        # Create user
        user = User(
            name=name,
            username=username,
            email=email,
            role=role
        )
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            return user
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError("Failed to create user: User already exists")

    @staticmethod
    def authenticate_user(username, password):
        """
        Authenticate a user.

        Args:
            username (str): Username
            password (str): Password

        Returns:
            User: Authenticated user object or None

        Raises:
            ValidationError: If input validation fails
        """
        username = validate_username(username)

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            return user

        return None

    @staticmethod
    def get_user_by_id(user_id):
        """
        Get user by ID.

        Args:
            user_id (int): User ID

        Returns:
            User: User object or None
        """
        return User.query.get(user_id)

    @staticmethod
    def get_user_by_username(username):
        """
        Get user by username.

        Args:
            username (str): Username

        Returns:
            User: User object or None

        Raises:
            ValidationError: If input validation fails
        """
        username = validate_username(username)
        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_all_users():
        """
        Get all users.

        Returns:
            list: List of all users
        """
        return User.query.all()

    @staticmethod
    def update_user(user_id, **kwargs):
        """
        Update user information.

        Args:
            user_id (int): User ID
            **kwargs: Fields to update (name, email, role, password)

        Returns:
            User: Updated user object

        Raises:
            ValidationError: If input validation fails
            ValueError: If user not found or update fails
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        # Validate and update fields
        if 'name' in kwargs:
            user.name = validate_name(kwargs['name'])

        if 'email' in kwargs:
            new_email = validate_email_address(kwargs['email'])
            # Check if email is already taken by another user
            existing = User.query.filter_by(email=new_email).first()
            if existing and existing.id != user_id:
                raise ValueError(f"Email '{new_email}' already registered")
            user.email = new_email

        if 'role' in kwargs:
            user.role = validate_role(kwargs['role'])

        if 'password' in kwargs:
            password = validate_password(kwargs['password'])
            user.set_password(password)

        try:
            db.session.commit()
            return user
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError("Failed to update user")

    @staticmethod
    def delete_user(user_id):
        """
        Delete a user account.

        Args:
            user_id (int): User ID

        Returns:
            bool: True if deleted successfully

        Raises:
            ValueError: If user not found
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        try:
            db.session.delete(user)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to delete user: {str(e)}")
