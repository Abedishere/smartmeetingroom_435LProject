"""
Room Domain Models

This module defines the Room entity and related domain models.
"""

from rooms_service.app import db
from datetime import datetime


class Room(db.Model):
    """
    Room entity representing a meeting room.

    Attributes:
        id (int): Primary key
        name (str): Room name
        capacity (int): Maximum number of people
        equipment (str): Available equipment (comma-separated)
        location (str): Room location/building
        status (str): Room status (available, booked, out_of_service)
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
    """

    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    capacity = db.Column(db.Integer, nullable=False)
    equipment = db.Column(db.Text, nullable=True)  # Comma-separated list
    location = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_equipment_list(self):
        """
        Get equipment as a list.

        Returns:
            list: List of equipment items
        """
        if not self.equipment:
            return []
        return [item.strip() for item in self.equipment.split(',') if item.strip()]

    def set_equipment_list(self, equipment_list):
        """
        Set equipment from a list.

        Args:
            equipment_list (list): List of equipment items

        Returns:
            None
        """
        if equipment_list:
            self.equipment = ', '.join(str(item).strip() for item in equipment_list if str(item).strip())
        else:
            self.equipment = ''

    def to_dict(self):
        """
        Convert room object to dictionary.

        Returns:
            dict: Room data as dictionary
        """
        return {
            'id': self.id,
            'name': self.name,
            'capacity': self.capacity,
            'equipment': self.get_equipment_list(),
            'location': self.location,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        """String representation of Room."""
        return f'<Room {self.name}>'
