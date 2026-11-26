"""Basic smoke tests for ShopPilot."""

import re
import pytest


def get_csrf_token(html):
    """Extract CSRF token from HTML response."""
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    return match.group(1) if match else None


class TestAuthentication:
    """Test authentication flow."""

    def test_login_page(self, client):
        """Login page should be accessible."""
        response = client.get("/auth/login")
        assert response.status_code == 200

    def test_default_login_redirects_to_change_password(self, client):
        """Default admin login should redirect to change password."""
        # Get CSRF token
        response = client.get("/auth/login")
        csrf_token = get_csrf_token(response.data.decode("utf-8"))

        response = client.post(
            "/auth/login",
            data={
                "csrf_token": csrf_token,
                "username": "Admin",
                "password": "admin123",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "change-password" in response.request.path

    def test_password_change(self, client):
        """Password change should work."""
        # Login first (defaults to must_change_password=True)
        response = client.get("/auth/login")
        csrf_token = get_csrf_token(response.data.decode("utf-8"))

        client.post(
            "/auth/login",
            data={
                "csrf_token": csrf_token,
                "username": "Admin",
                "password": "admin123",
            },
        )

        # Get CSRF token from change password page
        response = client.get("/auth/change-password")
        csrf_token = get_csrf_token(response.data.decode("utf-8"))

        # Change password
        response = client.post(
            "/auth/change-password",
            data={
                "csrf_token": csrf_token,
                "current_password": "admin123",
                "new_password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        # After password change, must_change_password=False, so goes to profile
        assert response.request.path == "/settings/profile"

    def test_dashboard_access(self, client):
        """Dashboard should be accessible after login and password change."""
        self.test_password_change(client)
        response = client.get("/")
        assert response.status_code == 200

    def test_logout(self, client):
        """Logout should work."""
        self.test_dashboard_access(client)
        response = client.get("/auth/logout", follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == "/auth/login"


class TestRoutes:
    """Test that all main routes are accessible."""

    def test_all_routes(self, client):
        """All main pages should return 200 after login."""
        # Login and change password
        client.post(
            "/auth/login",
            data={
                "csrf_token": get_csrf_token(
                    client.get("/auth/login").data.decode("utf-8")
                ),
                "username": "Admin",
                "password": "admin123",
            },
        )
        response = client.get("/auth/change-password")
        csrf_token = get_csrf_token(response.data.decode("utf-8"))
        client.post(
            "/auth/change-password",
            data={
                "csrf_token": csrf_token,
                "current_password": "admin123",
                "new_password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
            },
        )

        routes = [
            "/",
            "/orders/",
            "/products/",
            "/inventory/",
            "/reports/",
            "/administrators/",
            "/logs/",
            "/settings/profile",
        ]

        for route in routes:
            response = client.get(route)
            assert response.status_code == 200, f"Route {route} returned {response.status_code}"