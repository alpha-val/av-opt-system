from typing import List, Optional, Dict, Any
from datetime import datetime
from app.scenario.scenario_model import (
    ScenarioInDB,
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioResponse,
    OptionInDB,
    OptionCreate,
    OptionUpdate,
    OptionResponse,
)
from app.bronze_store import db

# ============================================================================
# SCENARIO DATABASE OPERATIONS
# ============================================================================


def create_scenario_db(scenario: ScenarioCreate, user_id: str) -> ScenarioInDB:
    """Create a new scenario in database"""
    scenario_data = scenario.model_dump()
    scenario_data["created_by"] = user_id
    scenario_data["created_at"] = datetime.utcnow()
    scenario_data["updated_at"] = datetime.utcnow()

    # Generate ID
    import uuid

    scenario_data["id"] = str(uuid.uuid4())

    # Insert into database
    result = db().scenarios.insert_one(scenario_data)

    # Return created scenario
    return ScenarioInDB(**scenario_data)


def get_scenario_db(scenario_id: str) -> Optional[ScenarioInDB]:
    """Get a scenario by ID"""
    scenario_data = db().scenarios.find_one({"id": scenario_id})
    if scenario_data:
        scenario_data.pop("_id", None)  # Remove MongoDB _id
        return ScenarioInDB(**scenario_data)
    return None


def get_scenarios_by_project_db(project_id: str) -> List[ScenarioInDB]:
    """Get all scenarios for a project"""
    cursor = db().scenarios.find({"project_id": project_id})
    scenarios = []
    for scenario_data in cursor:
        scenario_data.pop("_id", None)
        scenarios.append(ScenarioInDB(**scenario_data))
    return scenarios


def update_scenario_db(
    scenario_id: str, update_data: ScenarioUpdate
) -> Optional[ScenarioInDB]:
    """Update a scenario"""
    # Get existing scenario
    existing = get_scenario_db(scenario_id)
    if not existing:
        return None

    # Prepare update data
    update_dict = update_data.model_dump(exclude_unset=True)
    update_dict["updated_at"] = datetime.utcnow()

    # Update in database
    db().scenarios.update_one({"id": scenario_id}, {"$set": update_dict})

    # Return updated scenario
    return get_scenario_db(scenario_id)


def delete_scenario_db(scenario_id: str) -> bool:
    """Delete a scenario and all its options"""
    # Delete all options for this scenario
    db().options.delete_many({"scenario_id": scenario_id})

    # Delete the scenario
    result = db().scenarios.delete_one({"id": scenario_id})
    return result.deleted_count > 0


def update_scenario_option_count_db(scenario_id: str) -> None:
    """Update the option count for a scenario"""
    count = db().options.count_documents({"scenario_id": scenario_id})
    db().scenarios.update_one(
        {"id": scenario_id},
        {"$set": {"option_count": count, "updated_at": datetime.utcnow()}},
    )


# ============================================================================
# OPTION DATABASE OPERATIONS
# ============================================================================


def create_option_db(option: OptionCreate, user_id: str) -> OptionInDB:
    """Create a new option in database"""
    option_data = option.model_dump()
    option_data["created_by"] = user_id
    option_data["created_at"] = datetime.utcnow()
    option_data["updated_at"] = datetime.utcnow()

    # Generate ID
    import uuid

    option_data["id"] = str(uuid.uuid4())

    # Insert into database
    db().options.insert_one(option_data)

    # Update scenario option count
    update_scenario_option_count_db(option.scenario_id)

    # Return created option
    return OptionInDB(**option_data)


def get_option_db(option_id: str) -> Optional[OptionInDB]:
    """Get an option by ID"""
    option_data = db().options.find_one({"id": option_id})
    if option_data:
        option_data.pop("_id", None)
        return OptionInDB(**option_data)
    return None


def get_options_by_scenario_db(scenario_id: str) -> List[OptionInDB]:
    """Get all options for a scenario"""
    cursor = db().options.find({"scenario_id": scenario_id})
    options = []
    for option_data in cursor:
        option_data.pop("_id", None)
        options.append(OptionInDB(**option_data))
    return options


def update_option_db(
    option_id: str, update_data: OptionUpdate
) -> Optional[OptionInDB]:
    """Update an option"""
    # Get existing option
    existing = get_option_db(option_id)
    if not existing:
        return None

    # Prepare update data
    update_dict = update_data.model_dump(exclude_unset=True)
    update_dict["updated_at"] = datetime.utcnow()

    # Update in database
    db().options.update_one({"id": option_id}, {"$set": update_dict})

    # Return updated option
    return get_option_db(option_id)


def delete_option_db(option_id: str) -> bool:
    """Delete an option"""
    # Get the option to find its scenario_id
    option = get_option_db(option_id)
    if not option:
        return False

    scenario_id = option.scenario_id

    # Delete the option
    result = db().options.delete_one({"id": option_id})

    # Update scenario option count
    if result.deleted_count > 0:
        update_scenario_option_count_db(scenario_id)

    return result.deleted_count > 0


def select_option_db(option_id: str) -> Optional[OptionInDB]:
    """Select an option (and deselect others in the same scenario)"""
    option = get_option_db(option_id)
    if not option:
        return None

    # Deselect all options in this scenario
    db().options.update_many(
        {"scenario_id": option.scenario_id},
        {"$set": {"selected": False, "updated_at": datetime.utcnow()}},
    )

    # Select this option
    db().options.update_one(
        {"id": option_id}, {"$set": {"selected": True, "updated_at": datetime.utcnow()}}
    )

    return get_option_db(option_id)
