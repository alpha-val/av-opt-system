"""
Tests for cost estimator service.

Tests cost estimation engine with full provenance tracking.
"""

import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase

from app_v2.services.cost_estimator import CostEstimator
from app_v2.repositories.table_repo import TableRepository


@pytest.mark.asyncio
class TestCostEstimator:
    """Test cost estimator service."""
    
    async def test_estimate_equipment_cost_basic(
        self,
        test_db: AsyncIOMotorDatabase,
        sample_cost_table: dict,
        sample_equipment_option: dict
    ):
        """Test basic equipment cost estimation."""
        # Setup
        table_repo = TableRepository(test_db)
        await table_repo.create(sample_cost_table)
        
        estimator = CostEstimator(test_db)
        
        # Execute
        cost_data = await estimator.estimate_equipment_cost(
            entity_type="gyratory_crusher",
            equipment_specs=sample_equipment_option,
            target_year=2024
        )
        
        # Assert
        assert cost_data is not None
        assert "purchase_cost_base" in cost_data
        assert "purchase_cost_escalated" in cost_data
        assert "installed_equipment_cost" in cost_data
        assert cost_data["purchase_cost_escalated"] > cost_data["purchase_cost_base"]
        assert cost_data["installed_equipment_cost"] > cost_data["purchase_cost_escalated"]
    
    async def test_cost_breakdown_structure(
        self,
        test_db: AsyncIOMotorDatabase,
        sample_cost_table: dict,
        sample_equipment_option: dict
    ):
        """Test cost breakdown structure and categories."""
        # Setup
        table_repo = TableRepository(test_db)
        await table_repo.create(sample_cost_table)
        
        estimator = CostEstimator(test_db)
        
        # Execute
        cost_data = await estimator.estimate_equipment_cost(
            entity_type="gyratory_crusher",
            equipment_specs=sample_equipment_option,
            target_year=2024
        )
        
        # Assert breakdown structure
        assert "installed_cost_items" in cost_data
        assert len(cost_data["installed_cost_items"]) > 0
        
        # Check for expected categories
        categories = [item["category"] for item in cost_data["installed_cost_items"]]
        assert "Equipment" in categories
        assert "Civil & Structural" in categories
        assert "Mechanical Installation" in categories
    
    async def test_cost_provenance(
        self,
        test_db: AsyncIOMotorDatabase,
        sample_cost_table: dict,
        sample_equipment_option: dict
    ):
        """Test cost provenance tracking."""
        # Setup
        table_repo = TableRepository(test_db)
        table_id = await table_repo.create(sample_cost_table)
        
        estimator = CostEstimator(test_db)
        
        # Execute
        cost_data = await estimator.estimate_equipment_cost(
            entity_type="gyratory_crusher",
            equipment_specs=sample_equipment_option,
            target_year=2024
        )
        
        # Assert provenance
        assert "cost_sources" in cost_data
        assert len(cost_data["cost_sources"]) > 0
        
        # Check provenance details
        source = cost_data["cost_sources"][0]
        assert "source" in source
        assert "cost_year" in source
        assert "confidence" in source
    
    async def test_lang_factor_application(
        self,
        test_db: AsyncIOMotorDatabase,
        sample_cost_table: dict,
        sample_equipment_option: dict
    ):
        """Test Lang factor application."""
        # Setup
        table_repo = TableRepository(test_db)
        await table_repo.create(sample_cost_table)
        
        estimator = CostEstimator(test_db)
        
        # Execute
        cost_data = await estimator.estimate_equipment_cost(
            entity_type="gyratory_crusher",
            equipment_specs=sample_equipment_option,
            target_year=2024
        )
        
        # Assert Lang factor
        assert "lang_factor_applied" in cost_data
        assert cost_data["lang_factor_applied"] > 1.0
        
        # Verify installed cost is purchase cost * lang factor (approximately)
        purchase = cost_data["purchase_cost_escalated"]
        installed = cost_data["installed_equipment_cost"]
        lang = cost_data["lang_factor_applied"]
        
        # Allow 5% tolerance for rounding and indirect costs
        expected_installed = purchase * lang
        assert abs(installed - expected_installed) / expected_installed < 0.05
    
    async def test_opex_estimation(
        self,
        test_db: AsyncIOMotorDatabase,
        sample_equipment_option: dict
    ):
        """Test OPEX estimation."""
        estimator = CostEstimator(test_db)
        
        # Execute
        opex_data = await estimator.estimate_opex(
            equipment_specs=sample_equipment_option,
            operating_hours_per_year=8000,
            power_cost_per_kwh=0.10
        )
        
        # Assert
        assert opex_data is not None
        assert "power_cost_annual" in opex_data
        assert "maintenance_cost_annual" in opex_data
        assert "total_opex_per_year" in opex_data
        assert opex_data["total_opex_per_year"] > 0
    
    async def test_cost_escalation(
        self,
        test_db: AsyncIOMotorDatabase,
        mock_escalation_index: dict
    ):
        """Test cost escalation calculation."""
        estimator = CostEstimator(test_db)
        
        # Execute
        escalated_cost = await estimator.escalate_cost(
            base_cost=1000000,
            base_year=2020,
            target_year=2024,
            index_values=mock_escalation_index
        )
        
        # Assert
        assert escalated_cost > 1000000  # Should be higher due to inflation
        
        # Check escalation factor is reasonable
        escalation_factor = escalated_cost / 1000000
        assert 1.0 < escalation_factor < 2.0  # Reasonable range
    
    async def test_cost_confidence_calculation(
        self,
        test_db: AsyncIOMotorDatabase,
        sample_cost_table: dict,
        sample_equipment_option: dict
    ):
        """Test cost confidence scoring."""
        # Setup
        table_repo = TableRepository(test_db)
        await table_repo.create(sample_cost_table)
        
        estimator = CostEstimator(test_db)
        
        # Execute
        cost_data = await estimator.estimate_equipment_cost(
            entity_type="gyratory_crusher",
            equipment_specs=sample_equipment_option,
            target_year=2024
        )
        
        # Assert
        assert "overall_confidence" in cost_data
        assert cost_data["overall_confidence"] in ["high", "medium", "low"]