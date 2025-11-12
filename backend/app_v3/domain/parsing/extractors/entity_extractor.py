"""
LLM-based entity extraction from text chunks.

Uses OpenAI via LangChain to extract entities and edges that map to MSIO ontology.
"""

from typing import List, Dict, Any, Optional
from app_v2.adapters.config import SETTINGS
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
import uuid
import logging
from ..prompts.entity_extraction_prompt import get_entity_extraction_prompt
from ..utils.llm_tools import (
    TOOLS,
    is_valid_json,
    sanitize_for_json,
)

logger = logging.getLogger(__name__)

# Fixed namespace for deterministic UUID generation
NAMESPACE = uuid.UUID("6d978d8b-9e1b-4d3e-9f0a-2cfd5f9a9d9a")


class EntityExtractor:
    """Extract entities and edges using LLM with MSIO ontology awareness."""

    def __init__(self):
        """Initialize extractor with LLM configuration."""
        self.llm = ChatOpenAI(
            model=SETTINGS.llm_model_name or "gpt-4o",
            api_key=SETTINGS.openai_api_key,
            timeout=300,
            max_retries=3,
            temperature=0,
            max_tokens=4096,
            model_kwargs={
                "tools": TOOLS,
                "tool_choice": "auto",
            },
        )

    def extract(
        self, chunks: List[Dict[str, Any]], rules: Optional[List[str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract entities and edges from text chunks.

        Args:
            chunks: List of chunk dictionaries with 'text' field
            rules: Optional list of extraction rules to enable
                   (e.g., ["MSIO_ONTOLOGY", "NODES_AND_RELATIONS", "TABLE_EXTRACTION"])

        Returns:
            Dictionary with keys:
            - nodes: List of extracted entity nodes
            - edges: List of extracted edges/relations
            - scenarios: List of extracted scenarios (if applicable)
            - summaries: List of structured summaries (if applicable)
        """
        if not chunks:
            logger.warning("No chunks provided for entity extraction")
            return {"nodes": [], "edges": [], "scenarios": [], "summaries": []}

        logger.info(f"Starting entity extraction for {len(chunks)} chunks")

        # Default rules if not provided
        if rules is None:
            rules = [
                "MSIO_ONTOLOGY",
                "NODES_AND_RELATIONS",
                "PROVENANCE_AND_CONFIDENCE",
                "UNITS_NORMALIZATION",
                # "TABLE_EXTRACTION",
            ]

        # Build prompt with rules
        user_prompt = get_entity_extraction_prompt(rules=rules)
        system_prompt = SystemMessage(content=user_prompt)

        # Collect all extracted data
        all_nodes, all_edges, all_scenarios, all_summaries = [], [], [], []

        # Process each chunk
        for idx, chunk in enumerate(chunks):
            text = chunk.get("text", "")
            if not text.strip():
                logger.warning(f"Skipping empty chunk {idx+1}/{len(chunks)}")
                continue

            try:
                messages = [system_prompt, HumanMessage(content=text)]

                # Call LLM
                resp = self.llm.invoke(messages)

                # Process tool calls
                for call in resp.additional_kwargs.get("tool_calls", []):
                    fn = call.get("function", {})
                    name = fn.get("name")

                    try:
                        arguments = fn.get("arguments", "{}")
                        if not is_valid_json(arguments):
                            logger.error(f"Invalid JSON received: {arguments}")
                            continue

                        payload = json.loads(arguments)
                        payload = sanitize_for_json(payload)

                        if name == "extract_nodes":
                            all_nodes.extend(payload.get("nodes", []))
                        elif name == "extract_edges":
                            all_edges.extend(payload.get("edges", []))
                        # elif name == "extract_scenarios":
                        #     scenarios = payload.get("scenarios", [])
                        #     if isinstance(scenarios, list):
                        #         all_scenarios.extend(scenarios)
                        elif name == "extract_structured_report":
                            summaries = payload.get("base_case_extract", {})
                            if summaries:
                                all_summaries.append(summaries)
                        elif name == "extract_recommendations":
                            # Handle recommendations extraction
                            # This will be processed separately in orchestration
                            pass

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse LLM JSON: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing tool call {name}: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error processing chunk {idx+1}: {e}")
                continue

        logger.info(
            f"Extracted {len(all_nodes)} nodes, {len(all_edges)} edges "
            f"from {len(chunks)} chunks"
        )

        # Merge summaries if multiple chunks produced them
        merged_summary = {}
        if all_summaries:
            # Take the first summary as base, merge others if needed
            merged_summary = all_summaries[0] if isinstance(all_summaries[0], dict) else {}
            # For now, we'll use the first comprehensive summary
            # In the future, we could merge multiple summaries
        
        return {
            "nodes": all_nodes,
            "edges": all_edges,
            "scenarios": all_scenarios,
            "summaries": merged_summary if merged_summary else None,
        }

    def create_hierarchy_edges(
        self, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create PART_OF edges for MSIO hierarchy.

        For each entity, creates edges:
        - Entity →PART_OF→ Subcategory
        - Subcategory →PART_OF→ Category
        - Category →PART_OF→ Discipline

        Args:
            entities: List of entity dictionaries with MSIO fields in properties

        Returns:
            List of PART_OF edge dictionaries
        """
        edges = []
        created_nodes = {}  # Track created hierarchy nodes

        for entity in entities:
            props = entity.get("properties", {})
            discipline = props.get("discipline")
            category = props.get("category")
            subcategory = props.get("subcategory")
            entity_name = props.get("entity")

            if not all([discipline, category, subcategory, entity_name]):
                continue

            entity_id = entity.get("id")

            # Create hierarchy nodes if needed
            subcat_id = f"subcategory_{discipline}_{category}_{subcategory}"
            cat_id = f"category_{discipline}_{category}"
            disc_id = f"discipline_{discipline}"

            if subcat_id not in created_nodes:
                created_nodes[subcat_id] = {
                    "id": subcat_id,
                    "type": "Subcategory",
                    "properties": {
                        "name": subcategory,
                        "discipline": discipline,
                        "category": category,
                    },
                }

            if cat_id not in created_nodes:
                created_nodes[cat_id] = {
                    "id": cat_id,
                    "type": "Category",
                    "properties": {
                        "name": category,
                        "discipline": discipline,
                    },
                }

            if disc_id not in created_nodes:
                created_nodes[disc_id] = {
                    "id": disc_id,
                    "type": "Discipline",
                    "properties": {
                        "name": discipline,
                    },
                }

            # Create edges
            # Entity →PART_OF→ Subcategory
            edges.append(
                {
                    "id": f"{entity_id}_partof_{subcat_id}",
                    "source": entity_id,
                    "target": subcat_id,
                    "type": "PART_OF",
                    "properties": {
                        "confidence": 1.0,
                        "created_at": entity.get("properties", {}).get("created_at"),
                    },
                }
            )

            # Subcategory →PART_OF→ Category
            edges.append(
                {
                    "id": f"{subcat_id}_partof_{cat_id}",
                    "source": subcat_id,
                    "target": cat_id,
                    "type": "PART_OF",
                    "properties": {
                        "confidence": 1.0,
                    },
                }
            )

            # Category →PART_OF→ Discipline
            edges.append(
                {
                    "id": f"{cat_id}_partof_{disc_id}",
                    "source": cat_id,
                    "target": disc_id,
                    "type": "PART_OF",
                    "properties": {
                        "confidence": 1.0,
                    },
                }
            )

        logger.info(
            f"Created {len(edges)} hierarchy edges and {len(created_nodes)} hierarchy nodes"
        )

        # Return edges and any created hierarchy nodes that should be added to entities
        # Note: Hierarchy nodes could be added to entities list separately if needed
        return edges
