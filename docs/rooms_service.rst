Rooms Service
=============

The Rooms Service manages meeting room inventory, availability, equipment tracking, and search
functionality.

Architecture
------------

The service follows clean architecture principles with three main layers:

* **Domain Layer**: Contains the Room entity and business logic
* **Application Layer**: Contains use cases, validators, and services
* **Presentation Layer**: Contains API routes and request/response handling

API Endpoints
-------------

Room Management
~~~~~~~~~~~~~~~

POST /api/rooms/
^^^^^^^^^^^^^^^^

Create a new meeting room (Admin/Facility Manager only).

**Headers:** Authorization: Bearer <token>

**Request Body:**

.. code-block:: json

    {
        "name": "Conference Room A",
        "capacity": 10,
        "equipment": ["Projector", "Whiteboard"],
        "location": "Building 1, Floor 2"
    }

**Response:** 201 Created

GET /api/rooms/
^^^^^^^^^^^^^^^

Get all rooms.

**Headers:** Authorization: Bearer <token>

**Response:** 200 OK with room list

GET /api/rooms/<room_id>
^^^^^^^^^^^^^^^^^^^^^^^^

Get specific room by ID.

**Headers:** Authorization: Bearer <token>

**Response:** 200 OK with room data

PUT /api/rooms/<room_id>
^^^^^^^^^^^^^^^^^^^^^^^^

Update room information (Admin/Facility Manager only).

**Headers:** Authorization: Bearer <token>

**Request Body:** (all optional)

.. code-block:: json

    {
        "name": "Updated Room Name",
        "capacity": 15,
        "equipment": ["Projector", "Whiteboard", "TV"],
        "location": "Building 1, Floor 3",
        "status": "available"
    }

**Response:** 200 OK with updated room

DELETE /api/rooms/<room_id>
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Delete room (Admin/Facility Manager only).

**Headers:** Authorization: Bearer <token>

**Response:** 200 OK

Room Search
~~~~~~~~~~~

GET /api/rooms/search
^^^^^^^^^^^^^^^^^^^^^

Search for available rooms based on criteria.

**Headers:** Authorization: Bearer <token>

**Query Parameters:**

* capacity (int): Minimum capacity required
* location (str): Location filter (partial match)
* equipment (str): Required equipment (comma-separated)

**Example:**

``GET /api/rooms/search?capacity=10&location=Building 1&equipment=Projector,Whiteboard``

**Response:** 200 OK with matching rooms

Room Status
~~~~~~~~~~~

PATCH /api/rooms/<room_id>/status
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Update room status (Admin/Facility Manager only).

**Headers:** Authorization: Bearer <token>

**Request Body:**

.. code-block:: json

    {
        "status": "out_of_service"
    }

**Valid Statuses:**

* available
* booked
* out_of_service

**Response:** 200 OK with updated room

Module Reference
----------------

Domain Models
~~~~~~~~~~~~~

.. automodule:: rooms_service.domain.models
   :members:
   :undoc-members:
   :show-inheritance:

Services
~~~~~~~~

.. automodule:: rooms_service.application.services
   :members:
   :undoc-members:
   :show-inheritance:

Validators
~~~~~~~~~~

.. automodule:: rooms_service.application.validators
   :members:
   :undoc-members:
   :show-inheritance:

Authentication
~~~~~~~~~~~~~~

.. automodule:: rooms_service.application.auth
   :members:
   :undoc-members:
   :show-inheritance:

Routes
~~~~~~

.. automodule:: rooms_service.presentation.routes
   :members:
   :undoc-members:
   :show-inheritance:
