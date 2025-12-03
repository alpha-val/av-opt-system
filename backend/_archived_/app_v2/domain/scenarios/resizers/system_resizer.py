"""
System resizing component for scenarios.

Hybrid approach: LLM identifies what to resize, algorithms calculate new values.
"""

from typing import Dict, Any, List, Optional
import logging
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from ....adapters.config import SETTINGS
from ...projects.repository import get_project_entities_relations
from ..schemas import SystemResizing, ResizedParameter, UserConstraint, ScenarioAnalysis
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class SystemResizer:
    """Resize system parameters based on global objective and user constraints."""
    
    def __init__(self):
        """Initialize resizer with LLM configuration."""
        self.llm = ChatOpenAI(
            model=SETTINGS.llm_model_name or "gpt-4o",
            api_key=SETTINGS.openai_api_key,
            timeout=180,
            max_retries=2,
            temperature=0,
            max_tokens=2048,
        )
    
    def resize(
        self,
        project_id: str,
        global_objective: Dict[str, Any],
        analysis: ScenarioAnalysis,
        user_constraints: List[UserConstraint] = None,
    ) -> SystemResizing:
        """
        Resize system parameters based on global objective.
        
        Hybrid approach:
        1. LLM identifies which entities/parameters need resizing
        2. Algorithms calculate new values using scaling rules
        
        Args:
            project_id: Project identifier
            global_objective: Dictionary with goal_type, change_direction, change_magnitude, change_unit
            analysis: ScenarioAnalysis with local objectives
            user_constraints: Optional user-provided constraints
        
        Returns:
            SystemResizing with resized parameters
        """
        logger.info(f"Starting system resizing for project {project_id}")
        
        if not analysis or not analysis.local_objectives:
            logger.warning("No local objectives to resize")
            return SystemResizing(
                resized_parameters=[],
                calculation_summary="No local objectives available for resizing",
            )
        
        user_constraints = user_constraints or []
        constraints_dict = {f"{uc.entity_id}:{uc.parameter}": uc for uc in user_constraints}
        
        # Step 1: LLM identifies what to resize
        resize_targets = self._identify_resize_targets(global_objective, analysis)
        
        # Step 2: Calculate new values using algorithms
        resized_parameters = []
        for target in resize_targets:
            entity_id = target.get("entity_id")
            parameter = target.get("parameter")
            base_value = target.get("base_value")
            base_unit = target.get("base_unit")
            
            # Check for user constraint
            constraint_key = f"{entity_id}:{parameter}"
            constraint = constraints_dict.get(constraint_key)
            
            if constraint:
                # Apply user constraint
                if constraint.constraint_type == "FIXED":
                    resized_value = constraint.value
                    method = "user_fixed"
                    details = {"constraint_type": "FIXED"}
                elif constraint.constraint_type == "VARIABLE":
                    # Use constraint range, but still calculate based on objective
                    calculated = self._calculate_resized_value(
                        base_value, global_objective, parameter
                    )
                    # Clamp to constraint range
                    if constraint.min_value is not None and calculated < constraint.min_value:
                        resized_value = constraint.min_value
                    elif constraint.max_value is not None and calculated > constraint.max_value:
                        resized_value = constraint.max_value
                    else:
                        resized_value = calculated
                    method = "user_constrained"
                    details = {
                        "constraint_type": "VARIABLE",
                        "min": constraint.min_value,
                        "max": constraint.max_value,
                        "calculated": calculated,
                    }
                else:
                    resized_value = self._calculate_resized_value(
                        base_value, global_objective, parameter
                    )
                    method = "scaling"
                    details = {}
            else:
                # Calculate based on global objective
                resized_value = self._calculate_resized_value(
                    base_value, global_objective, parameter
                )
                method = self._determine_calculation_method(parameter, global_objective)
                details = self._get_calculation_details(
                    base_value, resized_value, global_objective, parameter
                )
            
            resized_parameters.append(
                ResizedParameter(
                    entity_id=entity_id,
                    parameter=parameter,
                    original_value=base_value,
                    resized_value=resized_value,
                    unit=base_unit,
                    calculation_method=method,
                    calculation_details=details,
                    confidence=target.get("confidence", 0.8),
                )
            )
        
        calculation_summary = f"Resized {len(resized_parameters)} parameters using {len(set(p.calculation_method for p in resized_parameters))} different methods"
        
        return SystemResizing(
            resized_parameters=resized_parameters,
            resizing_timestamp=datetime.now(timezone.utc),
            calculation_summary=calculation_summary,
        )
    
    def _identify_resize_targets(
        self, global_objective: Dict[str, Any], analysis: ScenarioAnalysis
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to identify which entities/parameters should be resized.
        
        Returns list of targets with entity_id, parameter, base_value, base_unit, confidence.
        """
        # For now, use local objectives directly (they're already identified as relevant)
        # In future, could use LLM to further refine which ones actually need resizing
        
        targets = []
        for lo in analysis.local_objectives:
            if lo.relevance_score >= 0.5:  # Only resize highly relevant entities
                targets.append({
                    "entity_id": lo.entity_id,
                    "parameter": lo.parameter,
                    "base_value": lo.base_value,
                    "base_unit": lo.base_unit,
                    "confidence": lo.relevance_score,
                })
        
        return targets
    
    def _calculate_resized_value(
        self, base_value: Any, global_objective: Dict[str, Any], parameter: str
    ) -> Any:
        """
        Calculate resized value using appropriate algorithm.
        
        Args:
            base_value: Original value
            global_objective: Global objective with change_magnitude, change_direction, change_unit
            parameter: Parameter name (e.g., "flow_rate", "capacity", "power")
        
        Returns:
            Resized value
        """
        if base_value is None:
            return None
        
        try:
            # Convert base_value to float if possible
            if isinstance(base_value, str):
                # Extract numeric value from string
                numeric_match = re.search(r'[\d.]+', str(base_value))
                if numeric_match:
                    base_numeric = float(numeric_match.group())
                else:
                    return base_value  # Can't parse, return as-is
            elif isinstance(base_value, (int, float)):
                base_numeric = float(base_value)
            else:
                return base_value  # Can't process, return as-is
            
            change_magnitude = global_objective.get("change_magnitude", 0)
            change_direction = global_objective.get("change_direction", "increase")
            change_unit = global_objective.get("change_unit", "%")
            
            # Handle percentage changes
            if change_unit == "%" or "%" in str(change_unit):
                if change_direction == "increase":
                    scale_factor = 1.0 + (change_magnitude / 100.0)
                else:  # decrease
                    scale_factor = 1.0 - (change_magnitude / 100.0)
                
                resized = base_numeric * scale_factor
            
            # Handle absolute changes (for same unit)
            else:
                if change_direction == "increase":
                    resized = base_numeric + change_magnitude
                else:  # decrease
                    resized = base_numeric - change_magnitude
            
            # Apply parameter-specific scaling rules
            resized = self._apply_parameter_scaling(parameter, base_numeric, resized, global_objective)
            
            return resized
            
        except Exception as e:
            logger.warning(f"Failed to calculate resized value: {e}")
            return base_value
    
    def _apply_parameter_scaling(
        self, parameter: str, base_value: float, linear_resized: float, global_objective: Dict[str, Any]
    ) -> float:
        """
        Apply parameter-specific scaling rules (e.g., cost exponents).
        
        Common rules:
        - Flow/capacity: Linear scaling (already applied)
        - Power: Often scales with flow^3 (pump affinity laws) or flow^2.5
        - Cost: Often scales with capacity^0.6-0.8 (cost exponent)
        - Area: Scales with capacity^0.67 (2/3 power)
        """
        goal_type = global_objective.get("goal_type", "")
        scale_ratio = linear_resized / base_value if base_value != 0 else 1.0
        
        # Cost-related parameters use cost exponent
        if "cost" in parameter.lower() or goal_type == "reduce_capex":
            # Typical cost exponent: 0.6-0.8
            exponent = 0.65
            resized = base_value * (scale_ratio ** exponent)
            return resized
        
        # Power parameters often scale non-linearly
        if "power" in parameter.lower() or "hp" in parameter.lower() or "kw" in parameter.lower():
            # Pump affinity: power ∝ flow^3, but often closer to flow^2.5 in practice
            exponent = 2.5
            resized = base_value * (scale_ratio ** exponent)
            return resized
        
        # Area/volume parameters scale with 2/3 power
        if "area" in parameter.lower() or "volume" in parameter.lower():
            exponent = 0.67
            resized = base_value * (scale_ratio ** exponent)
            return resized
        
        # Default: linear scaling (already applied)
        return linear_resized
    
    def _determine_calculation_method(
        self, parameter: str, global_objective: Dict[str, Any]
    ) -> str:
        """Determine the calculation method used."""
        if "cost" in parameter.lower():
            return "cost_exponent"
        elif "power" in parameter.lower() or "hp" in parameter.lower():
            return "power_scaling"
        elif "area" in parameter.lower() or "volume" in parameter.lower():
            return "area_scaling"
        else:
            return "percentage_scaling"
    
    def _get_calculation_details(
        self, base_value: Any, resized_value: Any, global_objective: Dict[str, Any], parameter: str
    ) -> Dict[str, Any]:
        """Get details about the calculation."""
        try:
            base_num = float(base_value) if base_value else 0
            resized_num = float(resized_value) if resized_value else 0
            
            if base_num != 0:
                scale_factor = resized_num / base_num
                change_pct = (scale_factor - 1.0) * 100.0
            else:
                scale_factor = 1.0
                change_pct = 0.0
            
            details = {
                "scale_factor": round(scale_factor, 4),
                "change_percentage": round(change_pct, 2),
            }
            
            # Add method-specific details
            method = self._determine_calculation_method(parameter, global_objective)
            if method == "cost_exponent":
                details["exponent"] = 0.65
            elif method == "power_scaling":
                details["exponent"] = 2.5
            elif method == "area_scaling":
                details["exponent"] = 0.67
            
            return details
            
        except Exception:
            return {}

