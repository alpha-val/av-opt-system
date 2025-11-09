"""
Test cases for scenario analysis functionality.

Tests CRUD operations, analysis, resizing, recommendations, and cost estimation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from ..domain.scenarios.schemas import (
    ScenarioCreate,
    ScenarioUpdate,
    GlobalObjective,
    ScenarioAnalysis,
    SystemResizing,
    CostEstimationData,
    ScenarioRecommendation,
    UserConstraint,
    LocalObjective,
    ResizedParameter,
)
from ..domain.scenarios.services import ScenarioService
from ..domain.scenarios.repository import (
    create_scenario,
    get_scenario,
    update_scenario,
    delete_scenario,
)


# Mock data
MOCK_PROJECT_ID = "test-project-123"
MOCK_SCENARIO_ID = "test-scenario-456"


@pytest.fixture
def mock_global_objective():
    """Create a mock global objective."""
    return GlobalObjective(
        goal_type="increase_production",
        change_direction="increase",
        change_magnitude=8.0,
        change_unit="%",
        description="Increase production by 8%",
    )


@pytest.fixture
def mock_scenario_create(mock_global_objective):
    """Create a mock scenario create request."""
    return ScenarioCreate(
        name="Test Scenario",
        description="Test scenario description",
        project_id=MOCK_PROJECT_ID,
        global_objective=mock_global_objective,
        status="draft",
    )


@pytest.fixture
def mock_scenario_analysis():
    """Create a mock scenario analysis."""
    return ScenarioAnalysis(
        scenario_summary="Test summary",
        local_objectives=[
            LocalObjective(
                entity_id="entity-1",
                entity_name="Pump A",
                entity_type="Equipment",
                parameter="flow_rate",
                relevance_score=0.9,
                base_value=100.0,
                base_unit="gpm",
                rationale="Directly affects throughput",
            )
        ],
        assumptions=[],
        policies=[],
        constraints=[],
        related_sections=[],
        confidence=0.85,
        analysis_timestamp=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_system_resizing():
    """Create a mock system resizing."""
    return SystemResizing(
        resized_parameters=[
            ResizedParameter(
                entity_id="entity-1",
                parameter="flow_rate",
                original_value=100.0,
                resized_value=108.0,
                unit="gpm",
                calculation_method="percentage_scaling",
                calculation_details={"scale_factor": 1.08, "change_percentage": 8.0},
                confidence=0.9,
            )
        ],
        resizing_timestamp=datetime.now(timezone.utc),
        calculation_summary="Resized 1 parameters",
    )


class TestScenarioCRUD:
    """Test CRUD operations for scenarios."""
    
    @pytest.mark.asyncio
    async def test_create_scenario(self, mock_scenario_create):
        """Test creating a scenario."""
        with patch("app_v2.domain.scenarios.repository._scenarios_collection") as mock_collection:
            mock_collection.insert_one.return_value = Mock(inserted_id="new-id")
            
            result = await create_scenario(mock_scenario_create)
            
            assert result is not None
            assert result.id == "new-id"
            mock_collection.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_scenario(self):
        """Test getting a scenario by ID."""
        with patch("app_v2.domain.scenarios.repository._scenarios_collection") as mock_collection:
            mock_collection.find_one.return_value = {
                "_id": "test-id",
                "name": "Test Scenario",
                "project_id": MOCK_PROJECT_ID,
                "status": "draft",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            
            result = await get_scenario("test-id")
            
            assert result is not None
            assert result.id == "test-id"
            assert result.name == "Test Scenario"
    
    @pytest.mark.asyncio
    async def test_update_scenario(self):
        """Test updating a scenario."""
        update_data = ScenarioUpdate(name="Updated Name")
        
        with patch("app_v2.domain.scenarios.repository._scenarios_collection") as mock_collection:
            mock_collection.find_one_and_update.return_value = {
                "_id": "test-id",
                "name": "Updated Name",
                "project_id": MOCK_PROJECT_ID,
                "status": "draft",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            
            result = await update_scenario("test-id", update_data)
            
            assert result is not None
            assert result.name == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_delete_scenario(self):
        """Test deleting a scenario."""
        with patch("app_v2.domain.scenarios.repository._scenarios_collection") as mock_collection:
            mock_collection.delete_one.return_value = Mock(deleted_count=1)
            
            result = await delete_scenario("test-id")
            
            assert result is True
            mock_collection.delete_one.assert_called_once()


class TestScenarioAnalysis:
    """Test scenario analysis functionality."""
    
    @pytest.mark.asyncio
    async def test_analyze_scenario(self, mock_global_objective):
        """Test analyzing a scenario."""
        service = ScenarioService()
        
        with patch.object(service, "get_scenario") as mock_get, \
             patch.object(service, "update_scenario") as mock_update, \
             patch.object(service.entity_analyzer, "analyze") as mock_analyze, \
             patch("app_v2.domain.scenarios.services.update_scenario_analysis") as mock_update_analysis:
            
            # Mock scenario
            mock_scenario = Mock()
            mock_scenario.project_id = MOCK_PROJECT_ID
            mock_scenario.global_objective = mock_global_objective
            mock_get.return_value = mock_scenario
            
            # Mock analysis
            mock_analysis = Mock()
            mock_analyze.return_value = mock_analysis
            
            # Mock get_scenario_with_analysis
            with patch.object(service, "get_scenario_with_analysis") as mock_get_full:
                mock_get_full.return_value = Mock()
                
                result = await service.analyze_scenario(MOCK_SCENARIO_ID)
                
                assert result is not None
                mock_analyze.assert_called_once()


class TestSystemResizing:
    """Test system resizing functionality."""
    
    @pytest.mark.asyncio
    async def test_resize_system(self, mock_scenario_analysis):
        """Test resizing system parameters."""
        service = ScenarioService()
        
        with patch.object(service, "get_scenario_with_analysis") as mock_get, \
             patch.object(service.system_resizer, "resize") as mock_resize, \
             patch("app_v2.domain.scenarios.services.update_scenario_resizing") as mock_update:
            
            # Mock scenario with analysis
            mock_scenario = Mock()
            mock_scenario.project_id = MOCK_PROJECT_ID
            mock_scenario.analysis = mock_scenario_analysis
            mock_scenario.global_objective = Mock()
            mock_scenario.global_objective.model_dump.return_value = {
                "goal_type": "increase_production",
                "change_direction": "increase",
                "change_magnitude": 8.0,
                "change_unit": "%",
            }
            mock_scenario.user_constraints = []
            mock_get.return_value = mock_scenario
            
            # Mock resizing
            mock_resizing = Mock()
            mock_resize.return_value = mock_resizing
            
            # Mock get_scenario_with_analysis for return
            with patch.object(service, "get_scenario_with_analysis") as mock_get_full:
                mock_get_full.return_value = Mock()
                
                result = await service.resize_system(MOCK_SCENARIO_ID)
                
                assert result is not None
                mock_resize.assert_called_once()


class TestCostEstimation:
    """Test cost estimation preparation."""
    
    @pytest.mark.asyncio
    async def test_prepare_cost_estimation(self, mock_scenario_analysis):
        """Test preparing cost estimation data."""
        service = ScenarioService()
        
        with patch.object(service, "get_scenario_with_analysis") as mock_get, \
             patch.object(service.cost_preparator, "prepare") as mock_prepare, \
             patch("app_v2.domain.scenarios.services.update_scenario_cost_estimation") as mock_update:
            
            # Mock scenario
            mock_scenario = Mock()
            mock_scenario.project_id = MOCK_PROJECT_ID
            mock_scenario.analysis = mock_scenario_analysis
            mock_scenario.resizing = None
            mock_get.return_value = mock_scenario
            
            # Mock cost estimation
            mock_cost_estimation = Mock()
            mock_prepare.return_value = mock_cost_estimation
            
            # Mock get_scenario_with_analysis for return
            with patch.object(service, "get_scenario_with_analysis") as mock_get_full:
                mock_get_full.return_value = Mock()
                
                result = await service.prepare_cost_estimation(MOCK_SCENARIO_ID, generate_estimates=False)
                
                assert result is not None
                mock_prepare.assert_called_once()


class TestRecommendations:
    """Test recommendation building."""
    
    @pytest.mark.asyncio
    async def test_build_recommendation(self, mock_scenario_analysis):
        """Test building recommendations."""
        service = ScenarioService()
        
        with patch.object(service, "get_scenario_with_analysis") as mock_get, \
             patch.object(service.recommendation_builder, "build") as mock_build, \
             patch("app_v2.domain.scenarios.services.update_scenario_recommendation") as mock_update:
            
            # Mock scenario
            mock_scenario = Mock()
            mock_scenario.project_id = MOCK_PROJECT_ID
            mock_scenario.analysis = mock_scenario_analysis
            mock_scenario.resizing = None
            mock_scenario.user_constraints = []
            mock_scenario.global_objective = Mock()
            mock_scenario.global_objective.model_dump.return_value = {
                "goal_type": "increase_production",
                "change_direction": "increase",
                "change_magnitude": 8.0,
                "change_unit": "%",
            }
            mock_get.return_value = mock_scenario
            
            # Mock recommendation
            mock_recommendation = Mock()
            mock_build.return_value = mock_recommendation
            
            # Mock get_scenario_with_analysis for return
            with patch.object(service, "get_scenario_with_analysis") as mock_get_full:
                mock_get_full.return_value = Mock()
                
                result = await service.build_recommendation(MOCK_SCENARIO_ID)
                
                assert result is not None
                mock_build.assert_called_once()


class TestErrorHandling:
    """Test error handling."""
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_scenario(self):
        """Test getting a scenario that doesn't exist."""
        with patch("app_v2.domain.scenarios.repository._scenarios_collection") as mock_collection:
            mock_collection.find_one.return_value = None
            
            result = await get_scenario("nonexistent-id")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_analyze_scenario_without_objective(self):
        """Test analyzing a scenario without a global objective."""
        service = ScenarioService()
        
        with patch.object(service, "get_scenario") as mock_get:
            mock_scenario = Mock()
            mock_scenario.global_objective = None
            mock_get.return_value = mock_scenario
            
            result = await service.analyze_scenario(MOCK_SCENARIO_ID)
            
            assert result is None

