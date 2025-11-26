Bookings Service
==================

The Bookings Service manages meeting room reservations with conflict detection,
availability checking, and comprehensive RBAC support.

API Endpoints
-------------

The service runs on port **5003** and provides the following endpoints:

Health Check
~~~~~~~~~~~~

.. code-block:: none

   GET /health

Returns the service health status.

List All Bookings
~~~~~~~~~~~~~~~~~~

.. code-block:: none

   GET /bookings

Returns all bookings in the system with user and room information.

**Authorization:** Admin, Facility Manager, or Auditor role required

Get Booking by ID
~~~~~~~~~~~~~~~~~~

.. code-block:: none

   GET /bookings/{booking_id}

Retrieves a specific booking by its ID.

**Authorization:** Admin, Facility Manager, or Auditor role required

Get User Booking History
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: none

   GET /bookings/user/{username}

Returns booking history for a specific user.

**Authorization:** Users can view their own bookings. Admin/FM/Auditor can view any user's bookings.

Create Booking
~~~~~~~~~~~~~~~

.. code-block:: none

   POST /bookings

Creates a new booking after validating room availability.

**Request Body:**

.. code-block:: json

   {
       "user_id": 1,
       "room_id": 1,
       "start_time": "2025-12-01T10:00:00",
       "end_time": "2025-12-01T12:00:00"
   }

**Validation:**
- Checks for time conflicts with existing bookings
- Verifies room and user exist
- Ensures end_time is after start_time

**Authorization:** Regular user, Facility Manager, Admin, or Service Account

Update Booking
~~~~~~~~~~~~~~~

.. code-block:: none

   PUT /bookings/{booking_id}

Updates an existing booking's time or room.

**Request Body (all fields optional):**

.. code-block:: json

   {
       "start_time": "2025-12-01T14:00:00",
       "end_time": "2025-12-01T16:00:00",
       "room_id": 2
   }

**Authorization:** Booking owner, Admin, or Facility Manager

Cancel Booking
~~~~~~~~~~~~~~~

.. code-block:: none

   DELETE /bookings/{booking_id}

Cancels a booking by setting its status to "cancelled".

**Authorization:** Booking owner, Admin, or Facility Manager

**Response:** 204 No Content

Check Room Availability
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: none

   GET /bookings/check-availability

Checks if a room is available for a given time window.

**Query Parameters:**
- ``room_id`` (required): Room identifier
- ``start_time`` (required): Proposed start time
- ``end_time`` (required): Proposed end time

**Response:**

.. code-block:: json

   {
       "available": true
   }

Modules
-------

.. automodule:: bookings_service.main
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: bookings_service.routes
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: bookings_service.models
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: bookings_service.schemas
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: bookings_service.auth
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: bookings_service.database
   :members:
   :undoc-members:
   :show-inheritance:
