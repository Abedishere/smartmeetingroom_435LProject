"""
Users Service Application Entry Point

This module initializes and configures the Flask application for the Users Service.
It handles user management with Admin role support.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
import os

db = SQLAlchemy()
jwt = JWTManager()


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

    with app.app_context():
        # Import models
        from users_service.domain import models

        # Create tables
        db.create_all()

        # Register blueprints
        from users_service.presentation import routes
        app.register_blueprint(routes.users_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)
