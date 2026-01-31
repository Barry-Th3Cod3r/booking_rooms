"""
Tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient


class TestAuth:
    """Test authentication functionality."""
    
    async def test_login_success(self, client: AsyncClient):
        """Test successful login."""
        response = await client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        response = await client.post(
            "/auth/login",
            json={"username": "admin", "password": "wrongpassword"}
        )
        
        assert response.status_code == 401
        assert "detail" in response.json()
    
    async def test_login_missing_fields(self, client: AsyncClient):
        """Test login with missing fields."""
        response = await client.post(
            "/auth/login",
            json={"username": "admin"}
        )
        
        assert response.status_code == 422
    
    async def test_register_success(self, client: AsyncClient, test_user_data):
        """Test successful user registration."""
        response = await client.post(
            "/auth/register",
            json=test_user_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert "id" in data
        assert "hashed_password" not in data
    
    async def test_register_duplicate_username(self, client: AsyncClient):
        """Test registration with duplicate username."""
        user_data = {
            "username": "admin",  # Already exists
            "email": "new@example.com",
            "full_name": "New User",
            "password": "password123"
        }
        
        response = await client.post(
            "/auth/register",
            json=user_data
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    async def test_register_duplicate_email(self, client: AsyncClient):
        """Test registration with duplicate email."""
        user_data = {
            "username": "newuser",
            "email": "admin@instituto.edu",  # Already exists
            "full_name": "New User",
            "password": "password123"
        }
        
        response = await client.post(
            "/auth/register",
            json=user_data
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    async def test_get_current_user(self, client: AsyncClient, auth_headers):
        """Test getting current user information."""
        response = await client.get(
            "/auth/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"
        assert data["is_admin"] is True
        assert "hashed_password" not in data
    
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/auth/me")
        
        assert response.status_code == 401

