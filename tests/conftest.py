"""Pytest configuration and fixtures."""

import os
import tempfile
import pytest
from app import create_app


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    # Use a unique temporary database file for each test session
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    # Override the database URI for testing
    import config as config_module
    config_module.TestingConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

    app = create_app("testing")
    with app.app_context():
        yield app

    # Cleanup test database after tests
    try:
        os.unlink(db_path)
    except (PermissionError, OSError):
        pass


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()