"""Pytest configuration and fixtures."""

import pytest
from app import create_app


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = create_app("testing")
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()