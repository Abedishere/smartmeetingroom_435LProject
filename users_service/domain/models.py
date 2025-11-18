"""
User Domain Models

This module defines the User entity and related domain models.
"""

from users_service.app import db
from datetime import datetime
import bcrypt


class User(db.Model):
    """
    User entity representing a system user.

    Attributes:
        id (int): Primary key
        name (str): Full name of the user
        username (str): Unique username
        password_hash (str): Hashed password
        email (str): User email address
        role (str): User role (admin, regular_user, facility_manager, moderator, auditor)
        created_at (datetime): Account creation timestamp
        updated_at (datetime): Last update timestamp
    """

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default='regular_user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        """
        Hash and set the user password.

        Args:
            password (str): Plain text password

        Returns:
            None
        """
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        """
        Verify a password against the stored hash.

        Args:
            password (str): Plain text password to verify

        Returns:
            bool: True if password matches, False otherwise
        """
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def to_dict(self, include_sensitive=False):
        """
        Convert user object to dictionary.

        Args:
            include_sensitive (bool): Whether to include sensitive information

        Returns:
            dict: User data as dictionary
        """
        data = {
            'id': self.id,
            'name': self.name,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        return data

    def __repr__(self):
        """String representation of User."""
        return f'<User {self.username}>'
