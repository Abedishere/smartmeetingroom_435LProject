"""
Rooms Service API Routes

This module defines the REST API endpoints for room management.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from rooms_service.app import limiter
from rooms_service.application.services import RoomService
from rooms_service.application.validators import ValidationError
from rooms_service.application.auth import role_required

rooms_bp = Blueprint('rooms', __name__, url_prefix='/api/rooms')


@rooms_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON response with service status
    """
    return jsonify({'status': 'healthy', 'service': 'rooms'}), 200


@rooms_bp.route('/', methods=['POST'])
@limiter.limit("30 per hour")
@jwt_required()
@role_required('admin', 'facility_manager')
def create_room():
    """
    Create a new meeting room (Admin and Facility Manager only).

    Headers:
        - Authorization: Bearer <access_token>

    Request Body:
        - name (str): Room name
        - capacity (int): Room capacity
        - equipment (list or str): Available equipment
        - location (str): Room location

    Returns:
        JSON response with created room data

    Status Codes:
        201: Room created successfully
        400: Validation error or room already exists
        403: Insufficient permissions
        500: Internal server error
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Extract required fields
        name = data.get('name')
        capacity = data.get('capacity')
        equipment = data.get('equipment', [])
        location = data.get('location')

        # Validate required fields
        if not all([name, capacity, location]):
            return jsonify({
                'error': 'Missing required fields',
                'required': ['name', 'capacity', 'location']
            }), 400

        # Create room
        room = RoomService.create_room(name, capacity, equipment, location)

        return jsonify({
            'message': 'Room created successfully',
            'room': room.to_dict()
        }), 201

    except ValidationError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@rooms_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_rooms():
    """
    Get all rooms.

    Headers:
        - Authorization: Bearer <access_token>

    Returns:
        JSON response with list of all rooms

    Status Codes:
        200: Success
        500: Internal server error
    """
    try:
        rooms = RoomService.get_all_rooms()
        return jsonify({
            'rooms': [room.to_dict() for room in rooms],
            'count': len(rooms)
        }), 200

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@rooms_bp.route('/search', methods=['GET'])
@jwt_required()
def search_rooms():
    """
    Search for available rooms based on criteria.

    Headers:
        - Authorization: Bearer <access_token>

    Query Parameters:
        - capacity (int, optional): Minimum capacity required
        - location (str, optional): Location filter
        - equipment (str, optional): Required equipment (comma-separated)

    Returns:
        JSON response with list of matching rooms

    Status Codes:
        200: Success
        400: Validation error
        500: Internal server error
    """
    try:
        # Get query parameters
        capacity = request.args.get('capacity', type=int)
        location = request.args.get('location')
        equipment = request.args.get('equipment')

        # Parse equipment if provided
        equipment_list = None
        if equipment:
            equipment_list = [item.strip() for item in equipment.split(',') if item.strip()]

        # Search rooms
        rooms = RoomService.search_available_rooms(
            capacity=capacity,
            location=location,
            equipment=equipment_list
        )

        return jsonify({
            'rooms': [room.to_dict() for room in rooms],
            'count': len(rooms)
        }), 200

    except ValidationError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@rooms_bp.route('/<int:room_id>', methods=['GET'])
@jwt_required()
def get_room(room_id):
    """
    Get a specific room by ID.

    Headers:
        - Authorization: Bearer <access_token>

    Path Parameters:
        - room_id (int): Room ID

    Returns:
        JSON response with room data

    Status Codes:
        200: Success
        404: Room not found
        500: Internal server error
    """
    try:
        room = RoomService.get_room_by_id(room_id)

        if not room:
            return jsonify({'error': f"Room with ID {room_id} not found"}), 404

        return jsonify({'room': room.to_dict()}), 200

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@rooms_bp.route('/<int:room_id>', methods=['PUT'])
@jwt_required()
@role_required('admin', 'facility_manager')
def update_room(room_id):
    """
    Update room information (Admin and Facility Manager only).

    Headers:
        - Authorization: Bearer <access_token>

    Path Parameters:
        - room_id (int): Room ID

    Request Body (all optional):
        - name (str): Updated room name
        - capacity (int): Updated capacity
        - equipment (list): Updated equipment list
        - location (str): Updated location
        - status (str): Updated status

    Returns:
        JSON response with updated room data

    Status Codes:
        200: Update successful
        400: Validation error
        403: Insufficient permissions
        404: Room not found
        500: Internal server error
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Update room
        room = RoomService.update_room(room_id, **data)

        return jsonify({
            'message': 'Room updated successfully',
            'room': room.to_dict()
        }), 200

    except ValidationError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 404 if 'not found' in str(e) else 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@rooms_bp.route('/<int:room_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin', 'facility_manager')
def delete_room(room_id):
    """
    Delete a room (Admin and Facility Manager only).

    Headers:
        - Authorization: Bearer <access_token>

    Path Parameters:
        - room_id (int): Room ID

    Returns:
        JSON response confirming deletion

    Status Codes:
        200: Deletion successful
        403: Insufficient permissions
        404: Room not found
        500: Internal server error
    """
    try:
        RoomService.delete_room(room_id)

        return jsonify({
            'message': f'Room with ID {room_id} deleted successfully'
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404 if 'not found' in str(e) else 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@rooms_bp.route('/<int:room_id>/status', methods=['PATCH'])
@jwt_required()
@role_required('admin', 'facility_manager')
def update_room_status(room_id):
    """
    Update room status (Admin and Facility Manager only).

    Headers:
        - Authorization: Bearer <access_token>

    Path Parameters:
        - room_id (int): Room ID

    Request Body:
        - status (str): New status (available, booked, out_of_service)

    Returns:
        JSON response with updated room data

    Status Codes:
        200: Update successful
        400: Validation error
        403: Insufficient permissions
        404: Room not found
        500: Internal server error
    """
    try:
        data = request.get_json()

        if not data or 'status' not in data:
            return jsonify({
                'error': 'Missing required field',
                'required': ['status']
            }), 400

        status = data.get('status')

        # Update room status
        room = RoomService.set_room_status(room_id, status)

        return jsonify({
            'message': 'Room status updated successfully',
            'room': room.to_dict()
        }), 200

    except ValidationError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 404 if 'not found' in str(e) else 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
