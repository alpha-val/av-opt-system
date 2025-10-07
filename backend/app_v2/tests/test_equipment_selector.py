"""
Tests for equipment selector service.

Tests equipment selection logic and sizing table queries.
"""

import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app_v2.services.equipment_selector import EquipmentSelector
from app_v2.repositories.table_repo import TableRepository
from app_v2.repositories.entity_repo import EntityRepository


@pytest.mark.asyncio
class TestEquipmentSelector:
    """Test equipment selector service."""
    
    async def test_select_equipment_basic(
        self,
        test_db: AsyncIOMotorDatabase,
        sample_sizing_table: dict
    ):
        """Test basic equipment selection."""
        # Setup
        table_repo = TableRepository(test_db)
        await table_repo.create(sample_sizing_table)
        
        selector = EquipmentSelector(test_db)
        
        # Execute
        equipment_list = await selector.select_equipment(
            entity_type="gyratory_crusher",
            required_capacity_tph=4000
        )
        
        # Assert
        assert len(equipment_list) > 0
        assert all(e["capacity_tph"] >= 4000 for e in equipment_list)
    
    async def test_select_equipment_with_constraints(
        self,
        test_db: AsyncIOMotorDatabase,
        sample_sizing_table: dict
    ):
        """Test equipment selection with constraints."""
        # Setup
        table_repo = TableRepository(test_db)
        await table_repo.create(sample_sizing_table)
        
        selector = EquipmentSelector(test_db)
        
        # Execute
        equipment_list = await selector.select_equipment(
            entity_type="gyratory_crusher",
            required_capacity_tph=4000,
            constraints={
                "max_power_kw": 800,
                "min_feed_opening_in": 50.0
            }
        )
        
        # Assert
        assert len(equipment_list) > 0
        for equipment in equipment_list:
            assert equipment["power_kw"] <= 800
            assert equipment["feed_opening_in"] >= 50.0
    
    async def test_select_equipment_no_matches(
        self,
        test_db: AsyncIOMotorDatabase,
        sample_sizing_table: dict
    ):
        """Test equipment selection with no matches."""
        # Setup
        table_repo = TableRepository(test_db)
        await table_repo.create(sample_sizing_table)
        
        selector = EquipmentSelector(test_db)
        
        # Execute
        equipment_list = await selector.select_equipment(
            entity_type="gyratory_crusher",
            required_capacity_tph=10000  # Too high
        )
        
        # Assert
        assert len(equipment_list) == 0
    
    async def test_find_similar_equipment(
        self,
        test_db: AsyncIOMotorDatabase,
        sample_entity: dict
    ):
        """Test finding similar equipment."""
        # Setup
        entity_repo = EntityRepository(test_db)
        entity_id = await entity_repo.create(sample_entity)
        
        # Create similar entities
        for i in range(3):
            similar = sample_entity.copy()
            similar["specifications"]["capacity_tph"] = 4800 + (i * 100)
            similar["specifications"]["power_kw"] = 1000 + (i * 50)
            await entity_repo.create(similar)
        
        selector = EquipmentSelector(test_db)
        
        # Execute
        similar_equipment = await selector.find_similar_equipment(
            entity_id=entity_id,
            tolerance_pct=10.0
        )
        
        # Assert
        assert len(similar_equipment) > 0
    
    async def test_get_equipment_specifications(
        self,
        test_db: AsyncIOMotorDatabase,
        sample_sizing_table: dict
    ):
        """Test retrieving equipment specifications."""
        # Setup
        table_repo = TableRepository(test_db)
        await table_repo.create(sample_sizing_table)
        
        selector = EquipmentSelector(test_db)
        
        # Execute
        specs = await selector.get_equipment_specifications(
            entity_type="gyratory_crusher",
            model="Superior MKII 54-75"
        )
        
        # Assert
        assert specs is not None
        assert specs["model"] == "Superior MKII 54-75"
        assert "capacity_tph" in specs
        assert "power_kw" in specs
    
    async def test_validate_equipment_selection(
        self,
        test_db: AsyncIOMotorDatabase
    ):
        """Test equipment selection validation."""
        selector = EquipmentSelector(test_db)
        
        # Valid selection
        is_valid, errors = selector.validate_equipment_selection(
            entity_type="gyratory_crusher",
            specifications={
                "capacity_tph": 4500,
                "power_kw": 750,
                "feed_opening_in": 54.0
            }
        )
        
        assert is_valid
        assert len(errors) == 0
        
        # Invalid selection (negative capacity)
        is_valid, errors = selector.validate_equipment_selection(
            entity_type="gyratory_crusher",
            specifications={
                "capacity_tph": -1000
            }
        )
        
        assert not is_valid
        assert len(errors) > 0