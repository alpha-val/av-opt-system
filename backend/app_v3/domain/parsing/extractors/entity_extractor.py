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
from ..prompts.entity_extraction_prompt import (
    generate_prompt,
)
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
        self, chunks: List[Dict[str, Any]], artifact_type: str = "base_case", rules: Optional[List[str]] = None
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
        user_prompt = generate_prompt(artifact_type=artifact_type, rules=rules)
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

    def extract_targeted(
        self,
        chunks: List[Dict[str, Any]],
        relevant_entities: Optional[List[Dict[str, Any]]] = None,
        extraction_scope: str = "exact",
        rules: Optional[List[str]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract entities and edges from text chunks in targeted mode.
        
        This method focuses on extracting only the entities specified in relevant_entities,
        with optional scope expansion based on extraction_scope parameter.

        Args:
            chunks: List of chunk dictionaries with 'text' field
            relevant_entities: List of entity specifications from recommendations
            extraction_scope: "exact" (only specified entities), "with_relationships" 
                            (entities + direct relationships), or "with_context" 
                            (entities + related entities in same context)
            rules: Optional list of extraction rules to enable

        Returns:
            Dictionary with keys:
            - nodes: List of extracted entity nodes (filtered to relevant entities)
            - edges: List of extracted edges/relations
            - scenarios: List of extracted scenarios (if applicable)
            - summaries: List of structured summaries (if applicable)
        """
        if not chunks:
            logger.warning("No chunks provided for targeted entity extraction")
            return {"nodes": [], "edges": [], "scenarios": [], "summaries": []}

        logger.info(
            f"Starting targeted entity extraction for {len(chunks)} chunks, "
            f"{len(relevant_entities) if relevant_entities else 0} relevant entities, "
            f"scope: {extraction_scope}"
        )

        # Default rules if not provided
        if rules is None:
            rules = [
                "MSIO_ONTOLOGY",
                "NODES_AND_RELATIONS",
                "PROVENANCE_AND_CONFIDENCE",
                "UNITS_NORMALIZATION",
            ]

        # # Build targeted prompt
        # user_prompt = get_targeted_entity_extraction_prompt(
        #     relevant_entities=relevant_entities,
        #     extraction_scope=extraction_scope,
        #     rules=rules,
        # )
        user_prompt = ""
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
                            nodes = payload.get("nodes", [])
                            # Filter nodes based on relevant_entities if extraction_scope is "exact"
                            if extraction_scope == "exact" and relevant_entities:
                                filtered_nodes = self._filter_nodes_by_specs(
                                    nodes, relevant_entities
                                )
                                all_nodes.extend(filtered_nodes)
                            else:
                                all_nodes.extend(nodes)
                        elif name == "extract_edges":
                            all_edges.extend(payload.get("edges", []))
                        elif name == "extract_structured_report":
                            summaries = payload.get("base_case_extract", {})
                            if summaries:
                                all_summaries.append(summaries)

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse LLM JSON: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing tool call {name}: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error processing chunk {idx+1}: {e}")
                continue

        # Filter edges to only include those connecting extracted nodes if scope is "exact"
        if extraction_scope == "exact" and relevant_entities:
            node_ids = {node.get("id") for node in all_nodes}
            all_edges = [
                edge
                for edge in all_edges
                if edge.get("source") in node_ids or edge.get("target") in node_ids
            ]

        logger.info(
            f"Extracted {len(all_nodes)} nodes, {len(all_edges)} edges "
            f"from {len(chunks)} chunks (targeted mode)"
        )

        # Merge summaries if multiple chunks produced them
        merged_summary = {}
        if all_summaries:
            merged_summary = (
                all_summaries[0] if isinstance(all_summaries[0], dict) else {}
            )

        return {
            "nodes": all_nodes,
            "edges": all_edges,
            "scenarios": all_scenarios,
            "summaries": merged_summary if merged_summary else None,
        }

    def _filter_nodes_by_specs(
        self,
        nodes: List[Dict[str, Any]],
        relevant_entities: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Filter nodes to match relevant entity specifications.
        
        Args:
            nodes: List of extracted nodes
            relevant_entities: List of entity specifications (full node structures)
            
        Returns:
            Filtered list of nodes that match the specifications
        """
        if not relevant_entities:
            return nodes

        # Build matching criteria from relevant_entities (full node structures)
        matching_criteria = []
        for entity_spec in relevant_entities:
            # Handle full node structure
            entity_id = entity_spec.get("id", "")
            entity_type = entity_spec.get("type", "")
            entity_props = entity_spec.get("properties", {})
            
            entity_name = entity_props.get("name", "").lower()
            discipline = entity_props.get("discipline", "").lower()
            category = entity_props.get("category", "").lower()
            subcategory = entity_props.get("subcategory", "").lower()
            msio_entity = entity_props.get("entity", "").lower()
            
            criteria = {
                "id": entity_id,
                "name": entity_name,
                "type": entity_type,
                "discipline": discipline,
                "category": category,
                "subcategory": subcategory,
                "entity": msio_entity,
            }
            matching_criteria.append(criteria)

        filtered_nodes = []
        for node in nodes:
            node_id = node.get("id", "")
            node_type = node.get("type", "")
            node_props = node.get("properties", {})
            node_name = node_props.get("name", "").lower()
            node_discipline = node_props.get("discipline", "").lower()
            node_category = node_props.get("category", "").lower()
            node_subcategory = node_props.get("subcategory", "").lower()
            node_entity = node_props.get("entity", "").lower()

            # Check if node matches any of the criteria
            for criteria in matching_criteria:
                # Match by ID (exact), name (fuzzy), or by MSIO classification
                id_match = node_id == criteria["id"] if criteria["id"] else False
                name_match = (
                    criteria["name"] in node_name or node_name in criteria["name"]
                ) if criteria["name"] else False
                type_match = node_type == criteria["type"] if criteria["type"] else True
                msio_match = (
                    node_discipline == criteria["discipline"]
                    and node_category == criteria["category"]
                    and node_subcategory == criteria["subcategory"]
                    and node_entity == criteria["entity"]
                ) if all([criteria["discipline"], criteria["category"], criteria["subcategory"], criteria["entity"]]) else False

                if (id_match or name_match or msio_match) and type_match:
                    filtered_nodes.append(node)
                    break

        return filtered_nodes
