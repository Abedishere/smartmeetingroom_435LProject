Users Service
=============

The Users Service handles all user-related operations including registration, authentication,
profile management, and role-based access control.

Architecture
------------

The service follows clean architecture principles with three main layers:

* **Domain Layer**: Contains the User entity and business logic
* **Application Layer**: Contains use cases, validators, and services
* **Presentation Layer**: Contains API routes and request/response handling

API Endpoints
-------------

Authentication
~~~~~~~~~~~~~~

POST /api/users/register
^^^^^^^^^^^^^^^^^^^^^^^^^

Register a new user account.

**Request Body:**

.. code-block:: json

    {
        "name": "John Doe",
        "username": "johndoe",
        "password": "SecurePass123",
        "email": "john@example.com",
        "role": "regular_user"
    }

**Response:** 201 Created

POST /api/users/login
^^^^^^^^^^^^^^^^^^^^^

Authenticate and receive JWT token.

**Request Body:**

.. code-block:: json

    {
        "username": "johndoe",
        "password": "SecurePass123"
    }

**Response:** 200 OK with access_token

User Management
~~~~~~~~~~~~~~~

GET /api/users/
^^^^^^^^^^^^^^^

Get all users (Admin/Auditor only).

**Headers:** Authorization: Bearer <token>

**Response:** 200 OK with user list

GET /api/users/<username>
^^^^^^^^^^^^^^^^^^^^^^^^^

Get specific user by username.

**Headers:** Authorization: Bearer <token>

**Response:** 200 OK with user data

PUT /api/users/<user_id>
^^^^^^^^^^^^^^^^^^^^^^^^

Update user information.

**Headers:** Authorization: Bearer <token>

**Request Body:** (all optional)

.. code-block:: json

    {
        "name": "Updated Name",
        "email": "new@example.com",
        "password": "NewPass123",
        "role": "facility_manager"
    }

**Response:** 200 OK with updated user

DELETE /api/users/<user_id>
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Delete user account (Admin only).

**Headers:** Authorization: Bearer <token>

**Response:** 200 OK

Module Reference
----------------

Domain Models
~~~~~~~~~~~~~

.. automodule:: users_service.domain.models
   :members:
   :undoc-members:
   :show-inheritance:

Services
~~~~~~~~

.. automodule:: users_service.application.services
   :members:
   :undoc-members:
   :show-inheritance:

Validators
~~~~~~~~~~

.. automodule:: users_service.application.validators
   :members:
   :undoc-members:
   :show-inheritance:

Authentication
~~~~~~~~~~~~~~

.. automodule:: users_service.application.auth
   :members:
   :undoc-members:
   :show-inheritance:

Routes
~~~~~~

.. automodule:: users_service.presentation.routes
   :members:
   :undoc-members:
   :show-inheritance:
