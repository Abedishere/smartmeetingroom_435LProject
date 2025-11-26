"""
Rooms Service Application Entry Point

This module initializes and configures the Flask application for the Rooms Service.
It handles meeting room management with Facility Manager support.
"""

from flask import Flask, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import logging
import json
import time
from datetime import datetime

db = SQLAlchemy()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


class StructuredLogger:
    """Structured JSON logger for API requests and responses."""

    def __init__(self, app=None):
        self.logger = logging.getLogger('rooms_service')
        self.logger.setLevel(logging.INFO)

        # JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)

        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize logging middleware."""

        @app.before_request
        def before_request():
            g.start_time = time.time()

        @app.after_request
        def after_request(response):
            if request.path == '/favicon.ico':
                return response

            duration = time.time() - g.start_time

            # Get user identity if authenticated
            user_id = None
            username = None
            try:
                identity = get_jwt_identity()
                if identity:
                    user_id = identity.get('id')
                    username = identity.get('username')
            except:
                pass

            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'service': 'rooms_service',
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'user_id': user_id,
                'username': username
            }

            self.logger.info(json.dumps(log_data))
            return response


structured_logger = StructuredLogger()


def create_app():
    """
    Create and configure the Flask application.

    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://admin:admin123@db:5432/meetingroom'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # 1 hour

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    structured_logger.init_app(app)

    with app.app_context():
        # Import models
        from rooms_service.domain import models

        # Create tables
        db.create_all()

        # Register blueprints
        from rooms_service.presentation import routes
        app.register_blueprint(routes.rooms_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5002, debug=True)
