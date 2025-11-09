"""
Entity analyzer for scenario analysis.

Queries entities from base case and uses LLM to analyze relevance to global objective.
"""

from typing import Dict, Any, List, Optional
import json
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from ....adapters.config import SETTINGS
from ...projects.repository import get_project_entities_relations
from ..schemas import ScenarioAnalysis, LocalObjective, Assumption, Policy, Constraint
from .scenario_analysis_prompt import get_scenario_analysis_prompt

logger = logging.getLogger(__name__)


class EntityAnalyzer:
    """Analyze entities from base case to identify local objectives for a scenario."""
    
    def __init__(self):
        """Initialize analyzer with LLM configuration."""
        self.llm = ChatOpenAI(
            model=SETTINGS.llm_model_name or "gpt-4o",
            api_key=SETTINGS.openai_api_key,
            timeout=300,
            max_retries=3,
            temperature=0,
            max_tokens=4096,
        )
    
    async def analyze(
        self,
        project_id: str,
        global_objective: Dict[str, Any],
        base_case_text: Optional[str] = None,
    ) -> ScenarioAnalysis:
        """
        Analyze entities from base case to identify local objectives.
        
        Args:
            project_id: Project identifier
            global_objective: Dictionary with goal_type, change_direction, change_magnitude, change_unit, description
            base_case_text: Optional full base case text for context
        
        Returns:
            ScenarioAnalysis with local objectives and related data
        """
        logger.info(f"Starting entity analysis for project {project_id} with goal: {global_objective.get('goal_type')}")
        
        try:
            # Query entities from base case
            entities_data = await get_project_entities_relations(project_id)
            entities = entities_data.entities
            
            # Convert entities to dict format for filtering
            entities_list = [e.model_dump() if hasattr(e, 'model_dump') else e for e in entities]
            
            # Filter to base case entities only
            base_case_entities = [
                e for e in entities_list
                if (isinstance(e, dict) and e.get("properties", {}).get("artifact_type") == "base_case")
                or (hasattr(e, 'properties') and getattr(e.properties, 'artifact_type', None) == "base_case")
            ]
            
            logger.info(f"Found {len(base_case_entities)} base case entities to analyze")
            
            # Format entities summary for LLM
            entities_summary = self._format_entities_summary(base_case_entities)
            
            # Get base case text if not provided (extract from chunks if needed)
            if not base_case_text:
                base_case_text = self._extract_base_case_text(project_id)
            
            # Build prompt
            prompt = get_scenario_analysis_prompt(
                global_objective=global_objective,
                entities_summary=entities_summary,
                base_case_text=base_case_text or "",
            )
            
            # Call LLM
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=f"Analyze entities for global objective: {global_objective.get('description', '')}"),
            ]
            
            logger.info("Calling LLM for scenario analysis...")
            response = self.llm.invoke(messages)
            response_text = response.content
            
            # Parse JSON response
            try:
                # Extract JSON from response (handle markdown code blocks)
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                analysis_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}")
                logger.error(f"Response text: {response_text[:500]}")
                # Return empty analysis on parse error
                return ScenarioAnalysis(
                    scenario_summary="Analysis failed: Could not parse LLM response",
                    local_objectives=[],
                    confidence=0.0,
                )
            
            # Convert to ScenarioAnalysis schema
            local_objectives = []
            for lo_data in analysis_data.get("local_objectives", []):
                try:
                    local_objectives.append(LocalObjective(**lo_data))
                except Exception as e:
                    logger.warning(f"Failed to parse local objective: {e}, data: {lo_data}")
                    continue
            
            assumptions = [
                Assumption(**a) for a in analysis_data.get("assumptions", [])
            ]
            
            policies = [
                Policy(**p) for p in analysis_data.get("policies", [])
            ]
            
            constraints = [
                Constraint(**c) for c in analysis_data.get("constraints", [])
            ]
            
            from datetime import datetime, timezone
            return ScenarioAnalysis(
                scenario_summary=analysis_data.get("scenario_summary"),
                local_objectives=local_objectives,
                assumptions=assumptions,
                policies=policies,
                constraints=constraints,
                related_sections=analysis_data.get("related_sections", []),
                confidence=analysis_data.get("confidence", 0.0),
                analysis_timestamp=datetime.now(timezone.utc),
            )
            
        except Exception as e:
            logger.error(f"Error in entity analysis: {e}", exc_info=True)
            # Return error analysis
            return ScenarioAnalysis(
                scenario_summary=f"Analysis failed: {str(e)}",
                local_objectives=[],
                confidence=0.0,
            )
    
    def _format_entities_summary(self, entities: List[Dict[str, Any]]) -> str:
        """Format entities list into a summary string for LLM."""
        if not entities:
            return "No entities found in base case."
        
        summary_parts = []
        for entity in entities[:50]:  # Limit to first 50 entities
            entity_id = str(entity.get("_id") or entity.get("id", "unknown"))
            entity_name = entity.get("name") or entity.get("properties", {}).get("name", "Unnamed")
            entity_type = entity.get("type") or entity.get("properties", {}).get("type", "Unknown")
            properties = entity.get("properties", {})
            
            # Extract key parameters
            key_params = []
            for key in ["flow_rate", "capacity", "power", "cost_value", "throughput", "efficiency"]:
                if key in properties:
                    value = properties[key]
                    unit = properties.get(f"{key}_unit") or properties.get("unit")
                    key_params.append(f"{key}: {value} {unit or ''}".strip())
            
            # Include attributes if present
            attributes = properties.get("attributes", [])
            if attributes:
                attr_strs = []
                for attr in attributes[:5]:  # Limit attributes
                    if isinstance(attr, dict):
                        name = attr.get("name", "")
                        value = attr.get("value", "")
                        unit = attr.get("unit", "")
                        if name and value:
                            attr_strs.append(f"{name}: {value} {unit}".strip())
                if attr_strs:
                    key_params.extend(attr_strs)
            
            entity_str = f"ID: {entity_id}, Name: {entity_name}, Type: {entity_type}"
            if key_params:
                entity_str += f", Parameters: {', '.join(key_params)}"
            
            summary_parts.append(entity_str)
        
        if len(entities) > 50:
            summary_parts.append(f"... and {len(entities) - 50} more entities")
        
        return "\n".join(summary_parts)
    
    def _extract_base_case_text(self, project_id: str) -> Optional[str]:
        """Extract base case text from chunks if available."""
        try:
            from ...adapters.mongo.client import db
            chunks_collection = db().chunks
            
            # Get chunks from base case documents
            chunks = chunks_collection.find({
                "properties.project_id": project_id,
                "properties.artifact_type": "base_case",
            }).limit(20)  # Limit chunks for context
            
            texts = [chunk.get("text", "") for chunk in chunks if chunk.get("text")]
            return "\n\n".join(texts) if texts else None
            
        except Exception as e:
            logger.warning(f"Failed to extract base case text: {e}")
            return None

