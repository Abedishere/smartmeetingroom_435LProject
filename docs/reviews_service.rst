Reviews Service
=================

The Reviews Service handles room reviews with rating management, moderation support,
and comprehensive filtering capabilities.

API Endpoints
-------------

The service runs on port **5004** and provides the following endpoints:

Health Check
~~~~~~~~~~~~

.. code-block:: none

   GET /health

Returns the service health status.

Create Review
~~~~~~~~~~~~~~

.. code-block:: none

   POST /reviews

Creates a review for a room with rating and comment.

**Request Body:**

.. code-block:: json

   {
       "room_id": 1,
       "rating": 5,
       "comment": "Excellent conference room with great equipment!"
   }

**Validation:**
- Rating must be between 1-5
- Comment must not be empty
- Comment is sanitized to remove unsafe HTML/scripts

**Authorization:** Regular user, Facility Manager, or Admin

Update Review
~~~~~~~~~~~~~~

.. code-block:: none

   PUT /reviews/{review_id}

Updates an existing review's rating and comment.

**Request Body:**

.. code-block:: json

   {
       "rating": 4,
       "comment": "Updated review: Very good room"
   }

**Authorization:** Review owner or Admin

Delete Review
~~~~~~~~~~~~~~

.. code-block:: none

   DELETE /reviews/{review_id}

Deletes a review permanently.

**Authorization:** Review owner, Moderator, or Admin

**Response:** 204 No Content

Get Reviews for Room
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: none

   GET /reviews/room/{room_id}

Retrieves all reviews for a specific room with optional filtering.

**Query Parameters:**
- ``min_rating`` (optional): Filter by minimum rating (1-5)
- ``flagged_only`` (optional): Show only flagged reviews (default: false)

**Response:**

.. code-block:: json

   [
       {
           "id": 1,
           "room_id": 1,
           "user_id": 1,
           "rating": 5,
           "comment": "Excellent room!",
           "flagged": false,
           "created_at": "2025-11-26T10:00:00",
           "user": {
               "id": 1,
               "username": "alice",
               "role": "regular_user"
           }
       }
   ]

Flag Review
~~~~~~~~~~~~

.. code-block:: none

   POST /reviews/{review_id}/flag

Flags a review as inappropriate for moderation.

**Authorization:** Regular user, Moderator, or Admin

**Effect:** Sets ``flagged=true`` on the review

Unflag Review
~~~~~~~~~~~~~~

.. code-block:: none

   POST /reviews/{review_id}/unflag

Removes a flag from a review after moderation.

**Authorization:** Moderator or Admin only

**Effect:** Sets ``flagged=false`` on the review

Moderation Features
-------------------

The Reviews Service includes comprehensive moderation capabilities:

**Flagging System:**
- Any authenticated user can flag inappropriate reviews
- Moderators and Admins can see all flagged reviews
- Only Moderators and Admins can unflag reviews

**Deletion Permissions:**
- Review owners can delete their own reviews
- Moderators can delete any review
- Admins have full deletion access

**Content Safety:**
- All comments are sanitized using the ``bleach`` library
- HTML tags and scripts are automatically removed
- Preserves safe formatting while preventing XSS attacks

Modules
-------

.. automodule:: reviews_service.main
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: reviews_service.routes
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: reviews_service.models
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: reviews_service.schemas
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: reviews_service.auth
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: reviews_service.database
   :members:
   :undoc-members:
   :show-inheritance:
