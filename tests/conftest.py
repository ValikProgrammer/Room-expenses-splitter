"""Pytest configuration and fixtures."""

import os
import tempfile
import pytest
from flask import Flask

from models import db
from routes import register_routes
from utils import initialize_database


@pytest.fixture
def app():
    """Create and configure a test Flask app."""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    app = Flask(__name__, instance_relative_config=True)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "test-secret-key"
    
    db.init_app(app)
    register_routes(app)
    
    with app.app_context():
        db.create_all()
        # Don't seed default members in tests - let tests create their own
    
    yield app
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()


