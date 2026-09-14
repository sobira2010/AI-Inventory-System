import pytest


class TestAuth:
    def test_register_user(self, client):
        """Test user registration."""
        response = client.post("/api/auth/register", json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpass123",
            "role": "STAFF",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test User"
        assert data["email"] == "test@example.com"
        assert data["role"] == "STAFF"
        assert "id" in data

    def test_register_duplicate_email(self, client, admin_user):
        """Test registration with existing email."""
        response = client.post("/api/auth/register", json={
            "name": "Another User",
            "email": "admin@test.com",
            "password": "testpass123",
            "role": "STAFF",
        })
        assert response.status_code == 409

    def test_login_success(self, client, admin_user):
        """Test successful login."""
        response = client.post("/api/auth/login", data={
            "username": "admin@test.com",
            "password": "admin123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client, admin_user):
        """Test login with wrong password."""
        response = client.post("/api/auth/login", data={
            "username": "admin@test.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_get_current_user(self, client, admin_headers, admin_user):
        """Test getting current user profile."""
        response = client.get("/api/auth/me", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@test.com"
        assert data["role"] == "ADMIN"

    def test_protected_endpoint_no_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_refresh_token(self, client, admin_user):
        """Test token refresh."""
        # First login
        login_response = client.post("/api/auth/login", data={
            "username": "admin@test.com",
            "password": "admin123",
        })
        refresh_token = login_response.json()["refresh_token"]

        # Refresh
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_refresh_invalid_token(self, client):
        """Test refresh with invalid token."""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid_token",
        })
        assert response.status_code == 401
