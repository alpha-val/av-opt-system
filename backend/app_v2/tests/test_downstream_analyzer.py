"""
Tests for downstream analyzer service.

Tests downstream impact analysis (core USP feature).
"""

import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app_v2.services.downstream_analyzer import DownstreamAnalyzer
from app_v2.repositories.entity_repo import EntityRepository


@pytest.mark.asyncio
class TestDownstreamAnalyzer:
    """Test downstream analyzer service."""
    
    async def test_analyze_downstream_impacts_basic(
        self,
        test_db: AsyncIOMotorDatabase,
        sample_entity: dict
    ):
        """Test basic downstream impact analysis."""
        # Setup - create upstream entity
        entity_repo = EntityRepository(test_db)
        upstream_id = await entity_repo.create(sample_entity)
        
        # Create downstream entity
        downstream = sample_entity.copy()
        downstream["name"] = "Secondary Crusher"
        downstream["entity_type"] = "cone_crusher"
        downstream["specifications"]["capacity_tph"] = 3000
        downstream_id = await entity_repo.create(downstream)
        
        # Add relationship
        await entity_repo.add_relationship(
            from_entity_id=upstream_id,
            to_entity_id=downstream_id,
            relationship_type="feeds_to",
            material_flow_tph=5000
        )
        
        analyzer = DownstreamAnalyzer(test_db)
        
        # Execute
        impact_analysis = await analyzer.analyze_downstream_impacts(
            changed_entity_id=upstream_id,
            parameter_changes={
                "capacity_tph": 4500,  # Reduced from 5000
                "product_size_in": 6.0  # Reduced from 8.0
            }
        )
        
        # Assert
        assert impact_analysis is not None
        assert "total_entities_analyzed" in impact_analysis
        assert "affected_entities" in impact_analysis
        assert impact_analysis["total_entities_analyzed"] > 0
    
    async def test_capacity_impact_propagation(
        self,
        test_db: AsyncIOMotorDatabase,
        sample_entity: dict
    ):
        """Test capacity impact propagation through process flow."""
        # Setup - create process chain
        entity_repo = EntityRepository(test_db)
        
        # Primary crusher
        primary_id = await entity_repo.create(sample_entity)
        
        # Secondary crusher
        secondary = sample_entity.copy()
        secondary["name"] = "Secondary Crusher"
        secondary["entity_type"] = "cone_crusher"
        secondary_id = await entity_repo.create(secondary)
        
        # Tertiary crusher
        tertiary = sample_entity.copy()
        tertiary["name"] = "Tertiary Crusher"
        tertiary["entity_type"] = "cone_crusher"
        tertiary_id = await entity_repo.create(tertiary)
        
        # Link them
        await entity_repo.add_relationship(primary_id, secondary_id, "feeds_to")
        await entity_repo.add_relationship(secondary_id, tertiary_id, "feeds_to")
        
        analyzer = DownstreamAnalyzer(test_db)
        
        # Execute - reduce primary capacity
        impact_analysis = await analyzer.analyze_downstream_impacts(
            changed_entity_id=primary_id,
            parameter_changes={"capacity_tph": 4000}  # Reduced from 5000
        )
        
        # Assert
        assert len(impact_analysis["affected_entities"]) >= 2
        
        # Check both downstream entities are affected
        affected_names = [e["entity_name"] for e in impact_analysis["affected_entities"]]
        assert "Secondary Crusher" in affected_names
        assert "Tertiary Crusher" in affected_names
    
    async def test_size_reduction_impact(
        self,
        test_db: AsyncIOMotorDatabase,
        sample_entity: dict
    ):
        """Test impact of size reduction on downstream equipment."""
        # Setup
        entity_repo = EntityRepository(test_db)
        
        # Crusher
        crusher_id = await entity_repo.create(sample_entity)
        
        # Mill (downstream)
        mill = sample_entity.copy()
        mill["name"] = "SAG Mill"
        mill["entity_type"] = "sag_mill"
        mill["specifications"] = {
            "diameter_m": 10.0,
            "length_m": 5.0,
            "power_kw": 15000,
            "capacity_tph": 5000,
            "feed_size_f80_mm": 200  # Expects 200mm feed
        }
        mill_id = await entity_repo.create(mill)
        
        await entity_repo.add_relationship(crusher_id, mill_id, "feeds_to")
        
        analyzer = DownstreamAnalyzer(test_db)
        
        # Execute - reduce crusher product size
        impact_analysis = await analyzer.analyze_downstream_impacts(
            changed_entity_id=crusher_id,
            parameter_changes={
                "product_p80": 150  # Reduced from 200mm
            }
        )
        
        # Assert
        assert len(impact_analysis["affected_entities"]) > 0
        
        # Mill should be affected positively (finer feed = more throughput)
        mill_impact = next(
            (e for e in impact_analysis["affected_entities"] if e["entity_name"] == "SAG Mill"),
            None
        )
        assert mill_impact is not None
        assert mill_impact["impact_type"] in ["capacity_change", "no_change"]
    
    async def test_cost_impact_calculation(
        self,
        test_db: AsyncIOMotorDatabase,
        sample_entity: dict
    ):
        """Test downstream cost impact calculation."""
        # Setup
        entity_repo = EntityRepository(test_db)
        
        # Create entities with cost data
        primary_id = await entity_repo.create(sample_entity)
        
        secondary = sample_entity.copy()
        secondary["name"] = "Secondary Crusher"
        secondary["cost_data"]["total_installed_cost"] = 8000000
        secondary_id = await entity_repo.create(secondary)
        
        await entity_repo.add_relationship(primary_id, secondary_id, "feeds_to")
        
        analyzer = DownstreamAnalyzer(test_db)
        
        # Execute
        impact_analysis = await analyzer.analyze_downstream_impacts(
            changed_entity_id=primary_id,
            parameter_changes={"capacity_tph": 6000}  # Increased from 5000
        )
        
        # Assert
        assert "total_capex_delta" in impact_analysis
        assert isinstance(impact_analysis["total_capex_delta"], (int, float))
    
    async def test_confidence_scoring(
        self,
        test_db: AsyncIOMotorDatabase,
        sample_entity: dict
    ):
        """Test confidence scoring for impact analysis."""
        # Setup
        entity_repo = EntityRepository(test_db)
        entity_id = await entity_repo.create(sample_entity)
        
        analyzer = DownstreamAnalyzer(test_db)
        
        # Execute
        impact_analysis = await analyzer.analyze_downstream_impacts(
            changed_entity_id=entity_id,
            parameter_changes={"capacity_tph": 4500}
        )
        
        # Assert
        assert "overall_confidence" in impact_analysis
        assert impact_analysis["overall_confidence"] in ["high", "medium", "low"]
        
        # Each affected entity should have confidence
        for entity in impact_analysis["affected_entities"]:
            assert "confidence" in entity
            assert entity["confidence"] in ["high", "medium", "low"]