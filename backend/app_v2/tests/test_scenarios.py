"""
Tests for scenario API endpoints.

Tests scenario creation, retrieval, and option generation.
"""

import pytest
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorDatabase

from app_v2.main import app


@pytest.mark.asyncio
class TestScenarioAPI:
    """Test scenario API endpoints."""
    
    async def test_create_scenario_success(
        self,
        test_db: AsyncIOMotorDatabase,
        sample_scenario: dict
    ):
        """Test successful scenario creation."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Remove fields that should be auto-generated
            request_data = sample_scenario.copy()
            request_data.pop("_id", None)
            request_data.pop("created_at", None)
            request_data.pop("updated_at", None)
            request_data.pop("status", None)
            request_data.pop("compute_state", None)
            request_data.pop("option_count", None)
            
            response = await client.post("/api/v1/scenarios", json=request_data)
            
            assert response.status_code == 201
            data = response.json()
            assert "_id" in data
            assert data["name"] == sample_scenario["name"]
            assert data["status"] == "draft"
    
    async def test_create_scenario_validation_error(self):
        """Test scenario creation with invalid data."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Missing required fields
            response = await client.post(
                "/api/v1/scenarios",
                json={"name": "Test"}
            )
            
            assert response.status_code == 422  # Validation error
    
    async def test_get_scenario(
        self,
        test_db: AsyncIOMotorDatabase,
        create_test_scenario: str
    ):
        """Test retrieving a scenario."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/scenarios/{create_test_scenario}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["_id"] == create_test_scenario
    
    async def test_get_scenario_not_found(self):
        """Test retrieving non-existent scenario."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            fake_id = "507f1f77bcf86cd799439011"
            response = await client.get(f"/api/v1/scenarios/{fake_id}")
            
            assert response.status_code == 404
    
    async def test_list_scenarios(
        self,
        test_db: AsyncIOMotorDatabase,
        sample_scenario: dict
    ):
        """Test listing scenarios."""
        # Create multiple scenarios
        project_id = sample_scenario["project_id"]
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/scenarios?project_id={project_id}"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "scenarios" in data
            assert "total" in data
            assert isinstance(data["scenarios"], list)
    
    async def test_update_scenario(
        self,
        test_db: AsyncIOMotorDatabase,
        create_test_scenario: str
    ):
        """Test updating a scenario."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            update_data = {
                "name": "Updated Scenario Name",
                "description": "Updated description"
            }
            
            response = await client.patch(
                f"/api/v1/scenarios/{create_test_scenario}",
                json=update_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Scenario Name"
    
    async def test_delete_scenario(
        self,
        test_db: AsyncIOMotorDatabase,
        create_test_scenario: str
    ):
        """Test deleting a scenario."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete(
                f"/api/v1/scenarios/{create_test_scenario}"
            )
            
            assert response.status_code == 204
            
            # Verify it's gone
            get_response = await client.get(
                f"/api/v1/scenarios/{create_test_scenario}"
            )
            assert get_response.status_code == 404