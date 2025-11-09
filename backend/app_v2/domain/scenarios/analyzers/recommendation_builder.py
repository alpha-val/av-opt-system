"""
Recommendation builder for scenarios.

Analyzes objectives and constraints to generate approach options and rank them.
"""

from typing import Dict, Any, List, Optional
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from ....adapters.config import SETTINGS
from ....domain.scenarios.schemas import (
    ScenarioRecommendation,
    ApproachOption,
    ExpectedEffect,
    ScenarioAnalysis,
    SystemResizing,
    UserConstraint,
)
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)


class RecommendationBuilder:
    """Build system recommendations with approach options."""
    
    def __init__(self):
        """Initialize recommendation builder with LLM configuration."""
        self.llm = ChatOpenAI(
            model=SETTINGS.llm_model_name or "gpt-4o",
            api_key=SETTINGS.openai_api_key,
            timeout=180,
            max_retries=2,
            temperature=0,
            max_tokens=2048,
        )
    
    def build(
        self,
        global_objective: Dict[str, Any],
        analysis: ScenarioAnalysis,
        resizing: Optional[SystemResizing] = None,
        user_constraints: List[UserConstraint] = None,
    ) -> ScenarioRecommendation:
        """
        Build system recommendation with approach options.
        
        Args:
            global_objective: Global objective specification
            analysis: ScenarioAnalysis with local objectives
            resizing: Optional SystemResizing with resized parameters
            user_constraints: Optional user constraints
        
        Returns:
            ScenarioRecommendation with approach options
        """
        logger.info("Building scenario recommendation")
        
        try:
            # Use LLM to generate approach options
            options = self._generate_approach_options(
                global_objective, analysis, resizing, user_constraints
            )
            
            # Rank options by feasibility and impact
            ranked_options = self._rank_options(options, analysis, resizing)
            
            # Select recommended option (highest ranked)
            recommended_option_id = ranked_options[0].option_id if ranked_options else None
            
            # Generate summary
            summary = self._generate_recommendation_summary(
                global_objective, ranked_options, recommended_option_id
            )
            
            # Identify uncertainties
            uncertainties = self._identify_uncertainties(analysis, resizing)
            
            return ScenarioRecommendation(
                approach_options=ranked_options,
                recommended_option_id=recommended_option_id,
                recommendation_summary=summary,
                uncertainties=uncertainties,
                recommendation_timestamp=datetime.now(timezone.utc),
            )
            
        except Exception as e:
            logger.error(f"Error building recommendation: {e}", exc_info=True)
            return ScenarioRecommendation(
                approach_options=[],
                recommendation_summary=f"Recommendation generation failed: {str(e)}",
                uncertainties=[],
            )
    
    def _generate_approach_options(
        self,
        global_objective: Dict[str, Any],
        analysis: ScenarioAnalysis,
        resizing: Optional[SystemResizing],
        user_constraints: List[UserConstraint],
    ) -> List[ApproachOption]:
        """Use LLM to generate approach options."""
        
        # Build prompt for LLM
        prompt = f"""
You are an expert process engineer. Generate approach options for achieving the following scenario goal:

Global Objective:
- Goal Type: {global_objective.get('goal_type')}
- Change Direction: {global_objective.get('change_direction')}
- Change Magnitude: {global_objective.get('change_magnitude')} {global_objective.get('change_unit')}
- Description: {global_objective.get('description')}

Relevant Entities:
{chr(10).join([f"- {lo.entity_name} ({lo.entity_type}): {lo.parameter} = {lo.base_value} {lo.base_unit or ''}" for lo in analysis.local_objectives[:10]])}

Resized Parameters:
{chr(10).join([f"- {rp.entity_id}: {rp.parameter} = {rp.resized_value} {rp.unit or ''} (from {rp.original_value})" for rp in (resizing.resized_parameters[:10] if resizing else [])])}

Generate 3-5 approach options. Each option should:
1. Have a clear title and rationale
2. Specify expected effects on throughput, capex, opex, quality
3. List dependencies (e.g., "TDH validation", "electrical capacity")
4. Be feasible and practical

Return JSON with this structure:
{{
  "approach_options": [
    {{
      "option_id": "option-1",
      "title": "Short descriptive title",
      "rationale": "Why this option helps achieve the goal",
      "expected_effects": {{
        "throughput": {{"direction": "increase|decrease|neutral", "estimate_pct": "8%", "notes": ""}},
        "capex": {{"direction": "increase|decrease|neutral", "notes": "cost impact description"}},
        "opex": {{"direction": "increase|decrease|neutral", "notes": "operating cost impact"}},
        "quality": {{"direction": "increase|decrease|neutral", "notes": "quality impact"}}
      }},
      "dependencies": ["dependency1", "dependency2"],
      "refs": []
    }}
  ]
}}

Return only valid JSON, no additional text.
"""
        
        try:
            messages = [SystemMessage(content=prompt)]
            response = self.llm.invoke(messages)
            response_text = response.content
            
            # Parse JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            data = json.loads(response_text)
            options_data = data.get("approach_options", [])
            
            # Convert to ApproachOption schemas
            options = []
            for opt_data in options_data:
                expected_effects = {}
                for metric, effect_data in opt_data.get("expected_effects", {}).items():
                    expected_effects[metric] = ExpectedEffect(**effect_data)
                
                options.append(
                    ApproachOption(
                        option_id=opt_data.get("option_id", f"option-{len(options)+1}"),
                        title=opt_data.get("title", "Untitled Option"),
                        rationale=opt_data.get("rationale", ""),
                        expected_effects=expected_effects,
                        dependencies=opt_data.get("dependencies", []),
                        refs=opt_data.get("refs", []),
                    )
                )
            
            return options
            
        except Exception as e:
            logger.error(f"Failed to generate approach options: {e}", exc_info=True)
            # Return default options based on local objectives
            return self._generate_default_options(analysis, resizing)
    
    def _generate_default_options(
        self, analysis: ScenarioAnalysis, resizing: Optional[SystemResizing]
    ) -> List[ApproachOption]:
        """Generate default options if LLM fails."""
        options = []
        
        # Group entities by type
        equipment_entities = [lo for lo in analysis.local_objectives if lo.entity_type == "Equipment"]
        
        if equipment_entities:
            options.append(
                ApproachOption(
                    option_id="option-1",
                    title="Modify Equipment",
                    rationale="Adjust equipment parameters to achieve goal",
                    expected_effects={
                        "throughput": ExpectedEffect(direction="increase", estimate_pct="5-10%"),
                        "capex": ExpectedEffect(direction="increase", notes="Equipment modification costs"),
                    },
                    dependencies=["Equipment specifications", "Vendor quotes"],
                )
            )
        
        return options
    
    def _rank_options(
        self,
        options: List[ApproachOption],
        analysis: ScenarioAnalysis,
        resizing: Optional[SystemResizing],
    ) -> List[ApproachOption]:
        """Rank options by feasibility and impact scores."""
        
        for option in options:
            # Calculate feasibility score (based on dependencies and constraints)
            feasibility = 0.7  # Default
            if len(option.dependencies) == 0:
                feasibility = 0.9
            elif len(option.dependencies) <= 2:
                feasibility = 0.7
            else:
                feasibility = 0.5
            
            # Calculate impact score (based on expected effects)
            impact = 0.5  # Default
            throughput_effect = option.expected_effects.get("throughput")
            if throughput_effect:
                if throughput_effect.direction == "increase":
                    impact = 0.8
                elif throughput_effect.direction == "decrease":
                    impact = 0.3
            
            option.feasibility_score = feasibility
            option.impact_score = impact
        
        # Sort by combined score (feasibility * impact)
        ranked = sorted(
            options,
            key=lambda o: (o.feasibility_score or 0.5) * (o.impact_score or 0.5),
            reverse=True,
        )
        
        return ranked
    
    def _generate_recommendation_summary(
        self,
        global_objective: Dict[str, Any],
        options: List[ApproachOption],
        recommended_id: Optional[str],
    ) -> str:
        """Generate summary of recommendation."""
        if not options:
            return "No approach options generated."
        
        recommended = next((o for o in options if o.option_id == recommended_id), options[0])
        
        summary = f"Recommended approach: {recommended.title}\n\n"
        summary += f"Rationale: {recommended.rationale}\n\n"
        summary += f"Expected effects:\n"
        
        for metric, effect in recommended.expected_effects.items():
            summary += f"- {metric}: {effect.direction}"
            if effect.estimate_pct:
                summary += f" ({effect.estimate_pct})"
            if effect.notes:
                summary += f" - {effect.notes}"
            summary += "\n"
        
        if recommended.dependencies:
            summary += f"\nDependencies: {', '.join(recommended.dependencies)}"
        
        return summary
    
    def _identify_uncertainties(
        self, analysis: ScenarioAnalysis, resizing: Optional[SystemResizing]
    ) -> List[Dict[str, Any]]:
        """Identify uncertainties and gaps."""
        uncertainties = []
        
        # Check for missing data in local objectives
        for lo in analysis.local_objectives:
            if lo.base_value is None:
                uncertainties.append({
                    "gap": f"Missing base value for {lo.entity_name}.{lo.parameter}",
                    "impact": "Medium",
                    "action": "Obtain base case value or estimate",
                })
        
        # Check for low confidence resizing
        if resizing:
            for rp in resizing.resized_parameters:
                if rp.confidence < 0.7:
                    uncertainties.append({
                        "gap": f"Low confidence in resizing {rp.parameter}",
                        "impact": "High" if "cost" in rp.parameter.lower() else "Medium",
                        "action": "Validate calculation method and assumptions",
                    })
        
        return uncertainties

