import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from .prompt_for_estimation import _build_cost_estimation_prompt

from typer import prompt

logger = logging.getLogger(__name__)


def estimate_scenario_cost(
    scenario_id: str,
    scenario_description: str,
    project_id: str,
    user_id: str,
) -> Dict[str, Any]:
    """
    Args:
        scenario_id: Scenario identifier
        scenario_description: User's scenario description and goals
        project_id: Project identifier
        user_id: User identifier

    Returns:
        Dict containing cost estimation results
    """
    try:
        import openai
        from app.config_adapter import SETTINGS
        from app.bronze_store import db

        if not SETTINGS.openai_api_key:
            logger.error("OpenAI API key not configured")
            return {
                "error": "OpenAI API key not configured",
                "status": "failed",
            }

        logger.info(f"[COST ESTIMATION] Starting for scenario {scenario_id}")

        base_case_cursor = db().entities.find(
            {
                "properties.project_id": project_id,
                "properties.user_id": user_id,
                "properties.artifact_type": "base_case",
            }
        )
        base_case_entities = list(base_case_cursor)

        tabular_cursor = db().entities.find(
            {
                "properties.project_id": project_id,
                "properties.user_id": user_id,
                "properties.artifact_type": "tabular_data",
            }
        )
        tabular_entities = list(tabular_cursor)

        logger.info(
            f"[COST ESTIMATION] Found {len(base_case_entities)} base case entities, "
            f"{len(tabular_entities)} tabular entities"
        )

        if len(base_case_entities) == 0:
            return {
                "error": "No base case entities found",
                "status": "failed",
                "cost_breakdown": None,
            }

        for entity in base_case_entities:
            if "_id" in entity:
                del entity["_id"]
        for entity in tabular_entities:
            if "_id" in entity:
                del entity["_id"]

        prompt = _build_cost_estimation_prompt(
            scenario_description, base_case_entities, tabular_entities
        )

        logger.info(f"[COST ESTIMATION] Sending {len(prompt)} chars to OpenAI")

        client = openai.OpenAI(api_key=SETTINGS.openai_api_key)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a cost estimation expert for mining and processing equipment. "
                    "Analyze the provided data and return accurate cost estimates in JSON format.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        logger.info(f"[COST ESTIMATION] Received {len(content)} chars from OpenAI")

        result = json.loads(content)

        cost_estimate = {
            "scenario_id": scenario_id,
            "project_id": project_id,
            "estimated_at": datetime.utcnow().isoformat(),
            "status": "completed",
            "relevant_entities": result.get("relevant_entities", {}),
            "cost_breakdown": result.get("cost_breakdown", {}),
            "assumptions": result.get("assumptions", []),
            "confidence": result.get("confidence", "medium"),
            "notes": result.get("notes", ""),
        }

        db().scenario_estimates.insert_one(cost_estimate)

        logger.info(
            f"[COST ESTIMATION] Completed for scenario {scenario_id}. "
            f"Delta: {cost_estimate['cost_breakdown'].get('delta', 0)}"
        )

        return cost_estimate

    except json.JSONDecodeError as e:
        logger.error(f"[COST ESTIMATION] Failed to parse LLM JSON: {e}")
        return {
            "error": f"JSON parse error: {str(e)}",
            "status": "failed",
        }

    except Exception as e:
        logger.error(f"[COST ESTIMATION] Failed: {e}")
        import traceback

        traceback.print_exc()
        return {
            "error": str(e),
            "status": "failed",
        }


def get_scenario_cost_estimate(scenario_id: str) -> Optional[Dict[str, Any]]:
    """
    Args:
        scenario_id: Scenario identifier

    Returns:
        Cost estimate dict or None if not found
    """
    from app.bronze_store import db

    estimate = db().scenario_estimates.find_one(
        {"scenario_id": scenario_id}, sort=[("estimated_at", -1)]
    )

    if estimate:
        estimate.pop("_id", None)
        return estimate

    return None
