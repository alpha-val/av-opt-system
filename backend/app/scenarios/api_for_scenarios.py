from __future__ import annotations
from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Depends,
    UploadFile,
    File,
    Form,
)
from typing import Optional, Dict, List, Any
from datetime import datetime
import uuid
from bson import ObjectId
import json

from ..bronze_store import db
from ..pipeline_users import get_current_user
from app.etl_base.extract_with_openai import openai_extract_scenario_data
from .schemas_for_scenario import (
    ScenarioBase,
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioResponse,
)
from .utils_for_scenarios import extract_scenario_entities
from app.text_clean import (
    extract_and_clean,
    chunk_by_page,
    chunk_by_character_limit,
    extract_fulltext,
    NAMESPACE,
)

import logging

logger = logging.getLogger(__name__)
router_costing = APIRouter()

# from .scenario_estimate import estimate_scenario_cost, get_scenario_cost_estimate

router_scenarios = APIRouter()

# ============================================================================
# ENDPOINTS
# ============================================================================


def _analyze_scenarios_in_base_report(
    scenario: str,
    file: UploadFile,
    doc_id: str,
    artifact_type: str,
    project_id: str,
    user_id: str,
) -> Dict[str, Any]:
    """
    Extract scenario data from chunks using OpenAI.
    """
    try:
        # Parse the scenario string into a dictionary
        scenario_dict = json.loads(scenario)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid JSON for 'scenario': {str(e)}"
        )

    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(400, "Please upload a valid PDF file")

    try:
        pdf_bytes = file.file.read()
        filename = file.filename or "uploaded.pdf"

        # Validate PDF file
        some_id, file_sha, pages_raw, pages_clean = extract_and_clean(
            pdf_bytes, filename
        )
    except Exception as e:
        logger.error(f"[Scenarios analysis] Failed to process PDF file: {e}")
        raise HTTPException(
            status_code=400,
            detail="Failed to process PDF file. Ensure it is a valid PDF.",
        )

    chunks = chunk_by_page(pages_clean, doc_id)
    raw_by_page = {p: t for p, t in pages_raw}
    for c in chunks:
        c["text_raw"] = raw_by_page.get(c["page"])
        # Add artifact_type, project_id, user_id to properties
        if "properties" not in c or not isinstance(c["properties"], dict):
            c["properties"] = {}
        c["properties"]["artifact_type"] = artifact_type
        c["properties"]["project_id"] = project_id
        c["properties"]["user_id"] = user_id
        c["properties"]["doc_id"] = doc_id

    try:
        # Use OpenAI to extract scenario mapping from the base case document
        scenarios = openai_extract_scenario_data(chunks, scenario=scenario_dict)
        return scenarios
    except Exception as e:
        logger.error(
            f"[Scenarios analysis] Failed to extract scenario data: {e}", exc_info=True
        )
        raise HTTPException(500, f"Failed to extract scenario data: {str(e)}")


# Create a new scenario
@router_scenarios.post(
    "/scenarios/add",
    response_model=ScenarioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_scenario(
    project_id: str = Form(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    goal: str = Form(...),
    change_type: str = Form(...),
    status: str = Form("draft"),
    # file: UploadFile = File(None),  # Accept file upload
    current_user: dict = Depends(get_current_user),
):
    """Create a new scenario"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token",
            )

        scenarios = []
        # Create scenario dictionary
        scenario_dict = {
            "id": str(uuid.uuid4()),
            "properties": {
                "project_id": project_id,
                "doc_id": "None",
                "name": name,
                "description": description,
                "goal": goal,
                "change_type": change_type,
                "status": status,
                "user_id": user_id,
                "created_by": user_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "scenarios": scenarios,  # Default to an empty list
                "compute_state": "idle",  # Default value for compute_state
                "target": {},  # Default value for target
                "constraints": {},  # Default value for constraints
            },
        }
        logger.debug(f"[DEBUG] scenario_dict before insert: {scenario_dict}")

        # Insert into database
        result = db().scenarios.insert_one(scenario_dict)

        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create scenario",
            )

        logger.info(
            f"[DEBUG] Successfully inserted scenario with id: {scenario_dict['id']}"
        )

        # Remove MongoDB _id before returning
        scenario_dict.pop("_id", None)

        return ScenarioResponse(**scenario_dict)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Create scenario failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# List scenarios for a project
@router_scenarios.get(
    "/projects/{project_id}/scenarios",
    response_model=List[ScenarioResponse],
    status_code=status.HTTP_200_OK,
)
def list_scenarios(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """List scenarios for a specific project"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token",
            )

        query = {"properties.project_id": project_id, "properties.created_by": user_id}

        scenarios_cursor = (
            db().scenarios.find(query, {"_id": 0}).skip(skip).limit(limit)
        )
        scenarios = list(scenarios_cursor)

        # Ensure default values for missing fields
        for scenario in scenarios:
            props = scenario.get("properties", {})
            props.setdefault("compute_state", "idle")
            props.setdefault("target", {})
            props.setdefault("constraints", {})
            props.setdefault("scenarios", [])
            props.setdefault("relevant_entities", [])
            scenario["properties"] = props

        return [ScenarioResponse(**scenario) for scenario in scenarios]

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] List scenarios failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# Get a single scenario by ID
@router_scenarios.get("/scenarios/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(scenario_id: str, current_user: dict = Depends(get_current_user)):
    """Get a scenario by ID"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token",
            )

        scenario_data = db().scenarios.find_one(
            {"id": scenario_id, "created_by": user_id}, {"_id": 0}
        )

        if not scenario_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found",
            )

        return ScenarioResponse(**scenario_data)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Get scenario failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# Update a scenario
@router_scenarios.put("/scenarios/{scenario_id}", response_model=ScenarioResponse)
def update_scenario(
    scenario_id: str,
    update_data: ScenarioUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a scenario"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token",
            )

        # Verify scenario exists and belongs to user
        existing = db().scenarios.find_one(
            {"id": scenario_id, "created_by": user_id}, {"_id": 0}
        )

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found",
            )

        # Build update dict
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)

        # # Ensure required fields are not removed
        # if "compute_state" not in update_dict:
        #     update_dict["compute_state"] = existing.get("compute_state", "idle")
        # if "target" not in update_dict:
        #     update_dict["target"] = existing.get("target", {})
        # if "constraints" not in update_dict:
        #     update_dict["constraints"] = existing.get("constraints", {})

        update_dict["properties"]["updated_at"] = datetime.utcnow()

        # Update in database
        result = db().scenarios.update_one(
            {"id": scenario_id, "created_by": user_id}, {"$set": update_dict}
        )

        if result.modified_count == 0 and result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update scenario {scenario_id}",
            )

        # Fetch updated scenario
        updated_scenario = db().scenarios.find_one(
            {"id": scenario_id, "created_by": user_id}, {"_id": 0}
        )

        return ScenarioResponse(**updated_scenario)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Update scenario failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# Delete a scenario
@router_scenarios.delete(
    "/scenarios/{scenario_id}",
    status_code=status.HTTP_200_OK,
)
def delete_scenario(scenario_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a scenario by ID"""
    try:
        user_id = (
            current_user.get("user_id")
            or current_user.get("sub")
            or current_user.get("id")
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extract user_id from authentication token",
            )


        # Verify scenario exists and belongs to user
        scenario = db().scenarios.find_one(
            {
                "id": scenario_id,
                "properties.created_by": user_id,
            },
            {"_id": 0, "properties.name": 1},
        )

        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found",
            )

        # Delete scenario
        result = db().scenarios.delete_one(
            {"id": scenario_id, "properties.created_by": user_id}
        )

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete scenario {scenario_id}",
            )

        print(f"[DEBUG] Deleted scenario {scenario_id}")

        return {
            "message": f"Scenario '{scenario.get('properties', {}).get('name', scenario_id)}' deleted successfully",
            "scenario_id": scenario_id,
            "scenario_name": scenario.get("properties", {}).get("name"),
            "deleted_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Delete scenario failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# Helper function to convert MongoDB ObjectId to string
def convert_objectid_to_str(data):
    """
    Recursively convert MongoDB ObjectId to string in nested dicts/lists
    """
    if isinstance(data, dict):
        return {key: convert_objectid_to_str(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    elif isinstance(data, ObjectId):
        return str(data)
    else:
        return data


@router_scenarios.post("/scenarios/extract-scenario-data")
async def extract_scenario_data(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    artifact_type: str = Form(...),
    user_id: str = Form(...),
    scenario: str = Form(...),
):
    """
    Extract scenario data from chunks using OpenAI.
    """
    try:
        # Parse the scenario string into a dictionary
        scenario_dict = json.loads(scenario)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid JSON for 'scenario': {str(e)}"
        )

    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(400, "Please upload a PDF file")

    pdf_bytes = file.file.read()
    filename = file.filename or "uploaded.pdf"
    project_id = scenario_dict.get("project_id", project_id)
    scenario_id = scenario_dict.get("id")
    print(f"[DEBUG] Received scenario: {scenario_dict}")
    if scenario_id is not None and not isinstance(scenario_id, str):
        raise Exception("scenario id is missing or not a string")
        return {"error": "scenario id is missing or not a string"}
    chunks = []
    print(f"[DEBUG] scenario_dict: {scenario_id}")

    # 1) Text extract + clean
    some_id, file_sha, pages_raw, pages_clean = extract_and_clean(pdf_bytes, filename)

    # find the document using file_sha
    existing_doc = db().documents.find_one(
        {"file_sha": file_sha, "project_id": project_id}, {"_id": 0, "id": 1}
    )
    found_doc_id = "not-applicable"
    if existing_doc:
        found_doc_id = existing_doc["id"]

    # ----- Extract full text for logging or other purposes -----
    full_text = extract_fulltext(pages_clean)

    process_full_text = scenario_dict.get("process_full_text", False)

    if process_full_text:
        logger.debug("[SCENARIO EXTRACTION] Processing full text only as per flag.")
        chunks: List[Dict[str, Any]] = []
        chunk_id = str(uuid.uuid5(NAMESPACE, f"{project_id}|{1}"))
        chunks.append(
            {
                "chunk_id": chunk_id,
                "doc_id": found_doc_id,
                "seq": 1,
                "page": 0,
                "text": full_text,
                "properties": {
                    "artifact_type": "base_case_full_text",
                    "project_id": project_id,
                    "user_id": user_id,
                    "doc_id": found_doc_id,
                },
            }
        )
        # ----- End full text extraction -----
    else:
        logger.debug("[SCENARIO EXTRACTION] Processing by character limit as per flag.")
        # Chunk by character limit
        chunks = chunk_by_character_limit(full_text, found_doc_id, char_limit=5000)
        for c in chunks:
            c["text_raw"] = c.get(c["text"])
            # Add artifact_type, project_id, user_id to properties
            if "properties" not in c or not isinstance(c["properties"], dict):
                c["properties"] = {}
            c["properties"]["artifact_type"] = artifact_type
            c["properties"]["project_id"] = project_id
            c["properties"]["user_id"] = user_id
            c["properties"]["doc_id"] = found_doc_id

    try:
        # Use OpenAI to extract scenario mapping from the base case document
        local_objectives = openai_extract_scenario_data(chunks, scenario=scenario_dict)

        # all_entities = extract_scenario_entities(scenarios)

        # Set all required fields
        scenario_dict["properties"]["doc_id"] = found_doc_id
        scenario_dict["properties"]["updated_at"] = datetime.utcnow()
        scenario_dict["properties"]["local_objectives"] = local_objectives
        scenario_dict["properties"]["doc_name"] = filename
        scenario_dict["properties"]["doc_size"] = len(pdf_bytes)
        scenario_dict["properties"]["status"] = "ready"
        scenario_dict["properties"]["file_sha256"] = file_sha
        # scenario_dict["properties"]["relevant_entities"] = local_objectives

        # Update the existing scenario in the database
        if scenario_id:
            result = db().scenarios.update_one(
                {"id": scenario_id}, {"$set": scenario_dict}
            )

            if result.modified_count == 0 and result.matched_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update scenario",
                )

            print(
                f"[DEBUG] Successfully updated scenario with id: {scenario_dict['id']}"
            )

            # Fetch updated scenario
            updated_scenario = db().scenarios.find_one({"id": scenario_id}, {"_id": 0})

            return ScenarioResponse(**updated_scenario)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scenario ID is required for update",
            )

    except Exception as e:
        logger.error(
            f"[COST_ESTIMATE] Failed to extract scenario data: {e}", exc_info=True
        )
        raise HTTPException(500, f"Failed to extract scenario data: {str(e)}")

    except Exception as e:
        logger.error(
            f"[COST_ESTIMATE] Failed to extract scenario data: {e}", exc_info=True
        )
        raise HTTPException(500, f"Failed to extract scenario data: {str(e)}")
