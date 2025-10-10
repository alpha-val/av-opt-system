"""
Pytest configuration and shared fixtures.

Provides fixtures for database, test data, and common test utilities.
"""

import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import AsyncGenerator, Dict, Any, List
from datetime import datetime
import os

# Set test environment
os.environ["TESTING"] = "1"
os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB_NAME"] = "av_opt_test"


# ============================================================================
# EVENT LOOP FIXTURE
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
async def mongodb_client() -> AsyncGenerator[AsyncIOMotorClient, None]:
    """
    Provide MongoDB client for tests.
    
    Uses a separate test database.
    """
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    yield client
    client.close()


@pytest.fixture
async def test_db(mongodb_client: AsyncIOMotorClient) -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Provide clean test database for each test.
    
    Drops all collections before and after each test.
    """
    db = mongodb_client[os.getenv("MONGODB_DB_NAME")]
    
    # Clean before test
    collection_names = await db.list_collection_names()
    for collection_name in collection_names:
        await db[collection_name].drop()
    
    yield db
    
    # Clean after test
    collection_names = await db.list_collection_names()
    for collection_name in collection_names:
        await db[collection_name].drop()


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_project() -> Dict[str, Any]:
    """Sample project data."""
    return {
        "name": "Test Mining Project",
        "location": "Test Site",
        "project_type": "greenfield",
        "status": "active",
        "throughput_tpd": 100000,
        "ore_type": "copper",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_entity() -> Dict[str, Any]:
    """Sample equipment entity."""
    return {
        "name": "Primary Gyratory Crusher",
        "entity_type": "gyratory_crusher",
        "entity_category": "crushing",
        "tag_number": "CR-001",
        "process_stage": "primary_crushing",
        "status": "existing",
        "is_base_case": True,
        "specifications": {
            "manufacturer": "Metso",
            "model": "Superior MKII 60-89",
            "capacity_tph": 5000,
            "feed_opening_in": 60.0,
            "closed_side_setting_in": 8.0,
            "power_kw": 1120,
            "reduction_ratio": 7.5
        },
        "cost_data": {
            "purchase_cost": 3500000,
            "purchase_cost_year": 2020,
            "purchase_cost_currency": "USD",
            "total_installed_cost": 12250000,
            "total_annual_opex": 850000
        },
        "relationships": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_parameter_change() -> Dict[str, Any]:
    """Sample parameter change."""
    return {
        "parameter_name": "closed_side_setting_in",
        "original_value": 8.0,
        "new_value": 6.0,
        "unit": "inches",
        "affected_entity_name": "Primary Gyratory Crusher",
        "rationale": "Reduce product size to improve SAG mill performance"
    }


@pytest.fixture
def sample_scenario(sample_project, sample_parameter_change) -> Dict[str, Any]:
    """Sample scenario data."""
    return {
        "project_id": "507f1f77bcf86cd799439011",
        "name": "Reduce Crusher Product Size",
        "description": "Test scenario for reducing primary crusher product size",
        "parameter_changes": [sample_parameter_change],
        "max_options_to_generate": 10,
        "analysis_assumptions": {
            "discount_rate": 0.10,
            "project_life_years": 20,
            "escalation_rate": 0.03
        },
        "status": "draft",
        "compute_state": "not_started",
        "option_count": 0,
        "tags": ["test", "crushing"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_equipment_option() -> Dict[str, Any]:
    """Sample equipment option."""
    return {
        "manufacturer": "Metso",
        "model": "Superior MKII 54-75",
        "capacity_tph": 4500,
        "feed_opening_in": 54.0,
        "closed_side_setting_in": 6.0,
        "power_kw": 750,
        "specifications": {
            "reduction_ratio": 9.0,
            "weight_kg": 285000,
            "eccentric_speed_rpm": 185
        }
    }


@pytest.fixture
def sample_cost_breakdown() -> Dict[str, Any]:
    """Sample cost breakdown."""
    return {
        "purchase_cost_base": 2500000,
        "purchase_cost_base_year": 2020,
        "purchase_cost_escalated": 2750000,
        "escalation_details": {
            "base_year": 2020,
            "target_year": 2024,
            "escalation_factor": 1.10,
            "index": "CEPCI"
        },
        "installed_cost_items": [
            {
                "category": "Equipment",
                "amount": 2750000,
                "calculation_method": "direct_quote"
            },
            {
                "category": "Civil & Structural",
                "amount": 3850000,
                "calculation_method": "lang_factor"
            },
            {
                "category": "Mechanical Installation",
                "amount": 1925000,
                "calculation_method": "lang_factor"
            },
            {
                "category": "Electrical & I&C",
                "amount": 1100000,
                "calculation_method": "lang_factor"
            }
        ],
        "total_direct_cost": 8525000,
        "total_indirect_cost": 1100000,
        "installed_equipment_cost": 9625000,
        "lang_factor_applied": 3.5,
        "currency": "USD"
    }


@pytest.fixture
def sample_sizing_table() -> Dict[str, Any]:
    """Sample sizing table."""
    return {
        "table_name": "Gyratory Crusher Sizing",
        "table_type": "equipment_sizing",
        "entity_type": "gyratory_crusher",
        "version": "1.0",
        "data_source": "Metso Technical Manual",
        "column_definitions": [
            {
                "name": "model",
                "data_type": "string",
                "is_required": True
            },
            {
                "name": "feed_opening_in",
                "data_type": "number",
                "unit": "inches",
                "is_required": True
            },
            {
                "name": "capacity_tph",
                "data_type": "number",
                "unit": "tph",
                "is_required": True
            },
            {
                "name": "power_kw",
                "data_type": "number",
                "unit": "kW",
                "is_required": True
            }
        ],
        "rows": [
            {
                "model": "Superior MKII 54-75",
                "feed_opening_in": 54.0,
                "capacity_tph": 4500,
                "power_kw": 750
            },
            {
                "model": "Superior MKII 60-89",
                "feed_opening_in": 60.0,
                "capacity_tph": 5000,
                "power_kw": 1120
            }
        ],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_cost_table() -> Dict[str, Any]:
    """Sample cost table."""
    return {
        "table_name": "Gyratory Crusher Costs",
        "table_type": "equipment_cost",
        "entity_type": "gyratory_crusher",
        "version": "1.0",
        "cost_year": 2020,
        "currency": "USD",
        "column_definitions": [
            {
                "name": "model",
                "data_type": "string",
                "is_required": True
            },
            {
                "name": "purchase_cost",
                "data_type": "number",
                "unit": "USD",
                "is_required": True
            },
            {
                "name": "lang_factor",
                "data_type": "number",
                "is_required": True
            }
        ],
        "rows": [
            {
                "model": "Superior MKII 54-75",
                "purchase_cost": 2500000,
                "lang_factor": 3.5
            },
            {
                "model": "Superior MKII 60-89",
                "purchase_cost": 3500000,
                "lang_factor": 3.5
            }
        ],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
async def create_test_entities(test_db: AsyncIOMotorDatabase, sample_entity: Dict[str, Any]) -> List[str]:
    """
    Create multiple test entities in database.
    
    Returns list of entity IDs.
    """
    entity_ids = []
    
    for i in range(5):
        entity = sample_entity.copy()
        entity["name"] = f"Test Entity {i+1}"
        entity["tag_number"] = f"TE-{i+1:03d}"
        
        result = await test_db.entities.insert_one(entity)
        entity_ids.append(str(result.inserted_id))
    
    return entity_ids


@pytest.fixture
async def create_test_scenario(
    test_db: AsyncIOMotorDatabase,
    sample_scenario: Dict[str, Any]
) -> str:
    """
    Create test scenario in database.
    
    Returns scenario ID.
    """
    result = await test_db.scenarios.insert_one(sample_scenario)
    return str(result.inserted_id)


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_escalation_index() -> Dict[int, float]:
    """Mock escalation index data (CEPCI)."""
    return {
        2018: 603.1,
        2019: 607.5,
        2020: 596.2,
        2021: 708.0,
        2022: 816.0,
        2023: 800.0,
        2024: 820.0
    }


@pytest.fixture
def mock_lang_factors() -> Dict[str, float]:
    """Mock Lang factors by equipment type."""
    return {
        "crusher": 3.5,
        "mill": 4.0,
        "conveyor": 2.5,
        "pump": 3.0,
        "screen": 2.8,
        "cyclone": 2.5,
        "thickener": 3.2,
        "flotation": 4.5
    }