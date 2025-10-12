import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def call_llm_for_tables(prompt: str, ontology: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call OpenAI to extract structured KG from table data.

    Args:
        prompt: Full prompt with rules and table data
        ontology: Domain ontology

    Returns:
        Dict with nodes and edges lists
    """
    try:
        import openai
        from ..config_adapter import SETTINGS

        if not SETTINGS.openai_api_key:
            logger.error("OpenAI API key not configured")
            return {"nodes": [], "edges": [], "error": "No API key"}

        client = openai.OpenAI(api_key=SETTINGS.openai_api_key)

        print("====================================================")
        print("[DEBUG] Starting text ingestion from table...")
        print("====================================================")
        logger.info(f"[TABULAR DATA] Sending {len(prompt)} chars to OpenAI")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a knowledge graph extraction expert. Extract structured entities and relationships from table data.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        logger.info(f"Received {len(content)} chars from OpenAI")

        # Parse JSON
        result = json.loads(content)

        # Normalize structure
        raw_nodes = result.get("extract_nodes", [])
        raw_edges = result.get("extract_edges", [])

        # Handle nested structure: extract_nodes might be {"nodes": [...]}
        if isinstance(raw_nodes, dict) and "nodes" in raw_nodes:
            raw_nodes = raw_nodes["nodes"]
        if isinstance(raw_edges, dict) and "edges" in raw_edges:
            raw_edges = raw_edges["edges"]

        # Ensure we have lists
        if not isinstance(raw_nodes, list):
            raw_nodes = []
        if not isinstance(raw_edges, list):
            raw_edges = []

        normalized = {
            "nodes": raw_nodes,
            "edges": raw_edges,
        }
        logger.info(
            f"Extracted {len(normalized['nodes'])} nodes, {len(normalized['edges'])} edges"
        )

        return normalized

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON: {e}")
        return {"nodes": [], "edges": [], "error": f"JSON parse error: {str(e)}"}

    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        import traceback

        traceback.print_exc()
        return {"nodes": [], "edges": [], "error": str(e)}
