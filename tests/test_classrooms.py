"""
Tests for classroom endpoints.
"""
import pytest
from httpx import AsyncClient


class TestClassrooms:
    """Test classroom functionality."""
    
    async def test_get_classrooms(self, client: AsyncClient, auth_headers):
        """Test getting list of classrooms."""
        response = await client.get(
            "/classrooms/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check classroom structure
        classroom = data[0]
        assert "id" in classroom
        assert "name" in classroom
        assert "code" in classroom
        assert "capacity" in classroom
        assert "is_active" in classroom
    
    async def test_get_classroom_by_id(self, client: AsyncClient, auth_headers):
        """Test getting classroom by ID."""
        response = await client.get(
            "/classrooms/1",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert "name" in data
        assert "code" in data
        assert "capacity" in data
    
    async def test_get_classroom_not_found(self, client: AsyncClient, auth_headers):
        """Test getting non-existent classroom."""
        response = await client.get(
            "/classrooms/999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    async def test_create_classroom(self, client: AsyncClient, auth_headers, test_classroom_data):
        """Test creating a new classroom."""
        response = await client.post(
            "/classrooms/",
            json=test_classroom_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == test_classroom_data["name"]
        assert data["code"] == test_classroom_data["code"]
        assert data["capacity"] == test_classroom_data["capacity"]
        assert "id" in data
    
    async def test_create_classroom_duplicate_name(self, client: AsyncClient, auth_headers):
        """Test creating classroom with duplicate name."""
        classroom_data = {
            "name": "Aula de Informática 1",  # Already exists
            "code": "NEW1",
            "capacity": 30
        }
        
        response = await client.post(
            "/classrooms/",
            json=classroom_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    async def test_create_classroom_duplicate_code(self, client: AsyncClient, auth_headers):
        """Test creating classroom with duplicate code."""
        classroom_data = {
            "name": "New Classroom",
            "code": "INF1",  # Already exists
            "capacity": 30
        }
        
        response = await client.post(
            "/classrooms/",
            json=classroom_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    async def test_update_classroom(self, client: AsyncClient, auth_headers):
        """Test updating classroom information."""
        update_data = {
            "name": "Updated Classroom Name",
            "capacity": 40
        }
        
        response = await client.put(
            "/classrooms/1",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["capacity"] == update_data["capacity"]
    
    async def test_update_classroom_not_found(self, client: AsyncClient, auth_headers):
        """Test updating non-existent classroom."""
        update_data = {"name": "Updated Name"}
        
        response = await client.put(
            "/classrooms/999",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    async def test_delete_classroom(self, client: AsyncClient, auth_headers):
        """Test deleting a classroom."""
        # First create a classroom
        classroom_data = {
            "name": "Test Classroom for Deletion",
            "code": "DELETE1",
            "capacity": 20
        }
        
        create_response = await client.post(
            "/classrooms/",
            json=classroom_data,
            headers=auth_headers
        )
        
        assert create_response.status_code == 200
        classroom_id = create_response.json()["id"]
        
        # Then delete it
        delete_response = await client.delete(
            f"/classrooms/{classroom_id}",
            headers=auth_headers
        )
        
        assert delete_response.status_code == 200
        assert "deleted successfully" in delete_response.json()["message"]
    
    async def test_delete_classroom_not_found(self, client: AsyncClient, auth_headers):
        """Test deleting non-existent classroom."""
        response = await client.delete(
            "/classrooms/999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    async def test_classroom_unauthorized_access(self, client: AsyncClient):
        """Test accessing classrooms without authentication."""
        response = await client.get("/classrooms/")
        
        assert response.status_code == 401

