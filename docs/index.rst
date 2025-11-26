Smart Meeting Room Management System Documentation
==================================================

Welcome to the Smart Meeting Room Management System documentation. This system provides
comprehensive backend services for managing meeting rooms, users, and bookings with role-based
access control.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   users_service
   rooms_service
   bookings_service
   reviews_service
   api_reference

Overview
--------

The Smart Meeting Room Management System consists of four main microservices:

1. **Users Service** - Handles user authentication, authorization, and profile management
2. **Rooms Service** - Manages meeting room inventory, availability, and search
3. **Bookings Service** - Manages room reservations with conflict detection and availability checking
4. **Reviews Service** - Handles room reviews with ratings, comments, and moderation

Features
--------

* JWT-based authentication and authorization
* Role-based access control (RBAC)
* Input validation and sanitization
* RESTful API design
* Docker containerization
* PostgreSQL database
* Comprehensive unit tests

User Roles
----------

Admin
~~~~~
Full system access including user management, role assignment, and system configuration.

Regular User
~~~~~~~~~~~~
Basic access to view rooms, manage own profile, and make bookings.

Facility Manager
~~~~~~~~~~~~~~~~
Manages room inventory, equipment, and availability. Can create, update, and delete rooms.

Moderator
~~~~~~~~~
Reviews and moderates user-generated content and reviews.

Auditor
~~~~~~~
Read-only access to all system data for auditing and compliance purposes.

Quick Start
-----------

1. Clone the repository
2. Run with Docker Compose::

    docker-compose up --build

3. Access the services:

   - Users Service: http://localhost:5001
   - Rooms Service: http://localhost:5002
   - Bookings Service: http://localhost:5003
   - Reviews Service: http://localhost:5004

4. Use the Postman collection to test API endpoints

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
