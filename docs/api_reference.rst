API Reference
=============

Authentication
--------------

All API endpoints (except registration, login, and health checks) require JWT authentication.
Include the access token in the Authorization header:

.. code-block:: http

    Authorization: Bearer <your_access_token>

Tokens expire after 1 hour and must be refreshed by logging in again.

Error Responses
---------------

All endpoints return consistent error responses:

.. code-block:: json

    {
        "error": "Error message describing what went wrong"
    }

HTTP Status Codes
~~~~~~~~~~~~~~~~~

* **200 OK**: Request succeeded
* **201 Created**: Resource created successfully
* **400 Bad Request**: Invalid input or validation error
* **401 Unauthorized**: Missing or invalid authentication
* **403 Forbidden**: Insufficient permissions
* **404 Not Found**: Resource not found
* **500 Internal Server Error**: Server error

Role-Based Access Control
--------------------------

The system implements role-based access control with the following permissions:

Admin
~~~~~

* Full access to all endpoints
* Can manage users, rooms, bookings, and reviews
* Can assign and change user roles
* Can delete any resource

Regular User
~~~~~~~~~~~~

* Can register and login
* Can view and update own profile
* Can view all rooms
* Can search for available rooms
* Can make and manage own bookings
* Can create and manage own reviews

Facility Manager
~~~~~~~~~~~~~~~~

* All Regular User permissions
* Can create, update, and delete rooms
* Can manage room equipment and availability
* Can set rooms as out_of_service
* Can view all bookings

Moderator
~~~~~~~~~

* Can moderate reviews
* Can flag and remove inappropriate content
* Read access to reviews

Auditor
~~~~~~~

* Read-only access to all resources
* Can view all users, rooms, bookings, and reviews
* Cannot modify any data
* Used for compliance and auditing

Input Validation
----------------

All user inputs are validated and sanitized to prevent security vulnerabilities:

Username
~~~~~~~~

* 3-50 characters
* Alphanumeric and underscores only
* Must be unique

Password
~~~~~~~~

* Minimum 8 characters
* Maximum 128 characters
* Must contain at least one uppercase letter
* Must contain at least one lowercase letter
* Must contain at least one digit

Email
~~~~~

* Must be valid email format
* Must be unique
* Automatically normalized

Room Name
~~~~~~~~~

* 2-100 characters
* Alphanumeric, spaces, hyphens, and underscores

Capacity
~~~~~~~~

* Integer between 1 and 1000

Security Features
-----------------

* **Password Hashing**: All passwords are hashed using bcrypt
* **JWT Authentication**: Secure token-based authentication
* **Input Sanitization**: HTML tags removed from all inputs
* **SQL Injection Prevention**: Parameterized queries via SQLAlchemy ORM
* **XSS Prevention**: Input sanitization using bleach library
* **HTTPS Ready**: Can be deployed with HTTPS for encrypted communication
