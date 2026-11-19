"""Pytest configuration and fixtures."""

import os
import pytest
from app import create_app


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = create_app("testing")
    with app.app_context():
        yield app
    # Cleanup test database after tests
    test_db = os.path.join(app.instance_path, "shop_pilot_test.db")
    if os.path.exists(test_db):
        os.remove(test_db)


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()