"""
Room Input Validation and Sanitization

This module provides validation and sanitization functions for room inputs
to prevent SQL injection, XSS, and other security vulnerabilities.
"""

import re
import bleach


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


def validate_room_name(name):
    """
    Validate and sanitize room name.

    Args:
        name (str): Room name to validate

    Returns:
        str: Sanitized room name

    Raises:
        ValidationError: If room name is invalid
    """
    name = sanitize_string(name, max_length=100)

    # Room name should be alphanumeric with spaces, hyphens, and underscores
    if not re.match(r'^[a-zA-Z0-9\s\-_]{2,100}$', name):
        raise ValidationError(
            "Room name must be 2-100 characters and contain only letters, numbers, spaces, hyphens, and underscores"
        )

    return name


def validate_capacity(capacity):
    """
    Validate room capacity.

    Args:
        capacity (int or str): Capacity to validate

    Returns:
        int: Validated capacity

    Raises:
        ValidationError: If capacity is invalid
    """
    try:
        capacity = int(capacity)
    except (ValueError, TypeError):
        raise ValidationError("Capacity must be a valid integer")

    if capacity < 1:
        raise ValidationError("Capacity must be at least 1")

    if capacity > 1000:
        raise ValidationError("Capacity cannot exceed 1000")

    return capacity


def validate_equipment(equipment):
    """
    Validate and sanitize equipment list.

    Args:
        equipment (list or str): Equipment to validate

    Returns:
        list: Sanitized equipment list

    Raises:
        ValidationError: If equipment is invalid
    """
    if equipment is None:
        return []

    if isinstance(equipment, str):
        # Split by comma if string
        equipment = [item.strip() for item in equipment.split(',') if item.strip()]
    elif not isinstance(equipment, list):
        raise ValidationError("Equipment must be a list or comma-separated string")

    # Sanitize each item
    sanitized_equipment = []
    for item in equipment:
        if not isinstance(item, str):
            item = str(item)

        # Remove HTML and strip whitespace
        sanitized_item = bleach.clean(item, tags=[], strip=True).strip()

        if sanitized_item:
            # Validate item length
            if len(sanitized_item) > 50:
                raise ValidationError("Each equipment item must be at most 50 characters")

            # Validate characters
            if not re.match(r'^[a-zA-Z0-9\s\-_/()]+$', sanitized_item):
                raise ValidationError(
                    "Equipment items can only contain letters, numbers, spaces, and basic punctuation"
                )

            sanitized_equipment.append(sanitized_item)

    return sanitized_equipment


def validate_location(location):
    """
    Validate and sanitize room location.

    Args:
        location (str): Location to validate

    Returns:
        str: Sanitized location

    Raises:
        ValidationError: If location is invalid
    """
    location = sanitize_string(location, max_length=200)

    # Location should contain alphanumeric with spaces, hyphens, commas, and periods
    if not re.match(r'^[a-zA-Z0-9\s\-,.#]+$', location):
        raise ValidationError(
            "Location must contain only letters, numbers, spaces, hyphens, commas, periods, and #"
        )

    return location


def validate_status(status):
    """
    Validate room status.

    Args:
        status (str): Status to validate

    Returns:
        str: Validated status

    Raises:
        ValidationError: If status is invalid
    """
    valid_statuses = ['available', 'booked', 'out_of_service']

    status = sanitize_string(status, max_length=20)

    if status not in valid_statuses:
        raise ValidationError(
            f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    return status
