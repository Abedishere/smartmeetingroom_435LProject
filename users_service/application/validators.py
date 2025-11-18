"""
Input Validation and Sanitization

This module provides validation and sanitization functions for user inputs
to prevent SQL injection, XSS, and other security vulnerabilities.
"""

import re
import bleach
from email_validator import validate_email, EmailNotValidError


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def sanitize_string(value, max_length=None):
    """
    Sanitize string input to prevent XSS attacks.

    Args:
        value (str): Input string to sanitize
        max_length (int, optional): Maximum allowed length

    Returns:
        str: Sanitized string

    Raises:
        ValidationError: If input is invalid
    """
    if not isinstance(value, str):
        raise ValidationError("Input must be a string")

    # Remove any HTML tags
    sanitized = bleach.clean(value, tags=[], strip=True)

    # Strip whitespace
    sanitized = sanitized.strip()

    if not sanitized:
        raise ValidationError("Input cannot be empty")

    if max_length and len(sanitized) > max_length:
        raise ValidationError(f"Input exceeds maximum length of {max_length}")

    return sanitized


def validate_username(username):
    """
    Validate and sanitize username.

    Args:
        username (str): Username to validate

    Returns:
        str: Sanitized username

    Raises:
        ValidationError: If username is invalid
    """
    username = sanitize_string(username, max_length=50)

    # Username must be alphanumeric with underscores, 3-50 characters
    if not re.match(r'^[a-zA-Z0-9_]{3,50}$', username):
        raise ValidationError(
            "Username must be 3-50 characters and contain only letters, numbers, and underscores"
        )

    return username


def validate_password(password):
    """
    Validate password strength.

    Args:
        password (str): Password to validate

    Returns:
        str: Validated password

    Raises:
        ValidationError: If password is invalid
    """
    if not isinstance(password, str):
        raise ValidationError("Password must be a string")

    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")

    if len(password) > 128:
        raise ValidationError("Password exceeds maximum length of 128 characters")

    # Check for at least one uppercase, one lowercase, and one digit
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter")

    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter")

    if not re.search(r'[0-9]', password):
        raise ValidationError("Password must contain at least one digit")

    return password


def validate_email_address(email):
    """
    Validate and normalize email address.

    Args:
        email (str): Email address to validate

    Returns:
        str: Normalized email address

    Raises:
        ValidationError: If email is invalid
    """
    try:
        email = sanitize_string(email, max_length=120)
        validated = validate_email(email, check_deliverability=False)
        return validated.normalized
    except EmailNotValidError as e:
        raise ValidationError(f"Invalid email address: {str(e)}")


def validate_role(role):
    """
    Validate user role.

    Args:
        role (str): Role to validate

    Returns:
        str: Validated role

    Raises:
        ValidationError: If role is invalid
    """
    valid_roles = ['admin', 'regular_user', 'facility_manager', 'moderator', 'auditor', 'service_account']

    role = sanitize_string(role, max_length=20)

    if role not in valid_roles:
        raise ValidationError(
            f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )

    return role


def validate_name(name):
    """
    Validate and sanitize user's full name.

    Args:
        name (str): Name to validate

    Returns:
        str: Sanitized name

    Raises:
        ValidationError: If name is invalid
    """
    name = sanitize_string(name, max_length=100)

    # Name should contain only letters, spaces, hyphens, and apostrophes
    if not re.match(r"^[a-zA-Z\s\-']{2,100}$", name):
        raise ValidationError(
            "Name must be 2-100 characters and contain only letters, spaces, hyphens, and apostrophes"
        )

    return name
