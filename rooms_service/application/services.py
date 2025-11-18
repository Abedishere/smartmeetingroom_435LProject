"""
Room Service Layer

This module contains business logic for room operations.
"""

from rooms_service.app import db
from rooms_service.domain.models import Room
from rooms_service.application.validators import (
    validate_room_name, validate_capacity, validate_equipment,
    validate_location, validate_status, ValidationError
)
from sqlalchemy.exc import IntegrityError


class RoomService:
    """Service class for room-related business logic."""

    @staticmethod
    def create_room(name, capacity, equipment, location):
        """
        Create a new meeting room.

        Args:
            name (str): Room name
            capacity (int): Room capacity
            equipment (list or str): Available equipment
            location (str): Room location

        Returns:
            Room: Created room object

        Raises:
            ValidationError: If input validation fails
            ValueError: If room already exists
        """
        # Validate inputs
        name = validate_room_name(name)
        capacity = validate_capacity(capacity)
        equipment_list = validate_equipment(equipment)
        location = validate_location(location)

        # Check if room already exists
        if Room.query.filter_by(name=name).first():
            raise ValueError(f"Room '{name}' already exists")

        # Create room
        room = Room(
            name=name,
            capacity=capacity,
            location=location,
            status='available'
        )
        room.set_equipment_list(equipment_list)

        try:
            db.session.add(room)
            db.session.commit()
            return room
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Failed to create room: Room already exists")

    @staticmethod
    def get_room_by_id(room_id):
        """
        Get room by ID.

        Args:
            room_id (int): Room ID

        Returns:
            Room: Room object or None
        """
        return Room.query.get(room_id)

    @staticmethod
    def get_room_by_name(name):
        """
        Get room by name.

        Args:
            name (str): Room name

        Returns:
            Room: Room object or None

        Raises:
            ValidationError: If input validation fails
        """
        name = validate_room_name(name)
        return Room.query.filter_by(name=name).first()

    @staticmethod
    def get_all_rooms():
        """
        Get all rooms.

        Returns:
            list: List of all rooms
        """
        return Room.query.all()

    @staticmethod
    def search_available_rooms(capacity=None, location=None, equipment=None):
        """
        Search for available rooms based on criteria.

        Args:
            capacity (int, optional): Minimum capacity required
            location (str, optional): Location filter
            equipment (list, optional): Required equipment

        Returns:
            list: List of matching rooms

        Raises:
            ValidationError: If input validation fails
        """
        query = Room.query.filter_by(status='available')

        if capacity is not None:
            capacity = validate_capacity(capacity)
            query = query.filter(Room.capacity >= capacity)

        if location is not None:
            location = validate_location(location)
            query = query.filter(Room.location.ilike(f'%{location}%'))

        if equipment is not None:
            equipment_list = validate_equipment(equipment)
            # Filter rooms that have all required equipment
            for item in equipment_list:
                query = query.filter(Room.equipment.ilike(f'%{item}%'))

        return query.all()

    @staticmethod
    def update_room(room_id, **kwargs):
        """
        Update room information.

        Args:
            room_id (int): Room ID
            **kwargs: Fields to update (name, capacity, equipment, location, status)

        Returns:
            Room: Updated room object

        Raises:
            ValidationError: If input validation fails
            ValueError: If room not found or update fails
        """
        room = Room.query.get(room_id)
        if not room:
            raise ValueError(f"Room with ID {room_id} not found")

        # Validate and update fields
        if 'name' in kwargs:
            new_name = validate_room_name(kwargs['name'])
            # Check if name is already taken by another room
            existing = Room.query.filter_by(name=new_name).first()
            if existing and existing.id != room_id:
                raise ValueError(f"Room name '{new_name}' already exists")
            room.name = new_name

        if 'capacity' in kwargs:
            room.capacity = validate_capacity(kwargs['capacity'])

        if 'equipment' in kwargs:
            equipment_list = validate_equipment(kwargs['equipment'])
            room.set_equipment_list(equipment_list)

        if 'location' in kwargs:
            room.location = validate_location(kwargs['location'])

        if 'status' in kwargs:
            room.status = validate_status(kwargs['status'])

        try:
            db.session.commit()
            return room
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Failed to update room")

    @staticmethod
    def delete_room(room_id):
        """
        Delete a room.

        Args:
            room_id (int): Room ID

        Returns:
            bool: True if deleted successfully

        Raises:
            ValueError: If room not found
        """
        room = Room.query.get(room_id)
        if not room:
            raise ValueError(f"Room with ID {room_id} not found")

        try:
            db.session.delete(room)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to delete room: {str(e)}")

    @staticmethod
    def set_room_status(room_id, status):
        """
        Set room status (available, booked, out_of_service).

        Args:
            room_id (int): Room ID
            status (str): New status

        Returns:
            Room: Updated room object

        Raises:
            ValidationError: If status is invalid
            ValueError: If room not found
        """
        room = Room.query.get(room_id)
        if not room:
            raise ValueError(f"Room with ID {room_id} not found")

        room.status = validate_status(status)

        try:
            db.session.commit()
            return room
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to update room status: {str(e)}")
