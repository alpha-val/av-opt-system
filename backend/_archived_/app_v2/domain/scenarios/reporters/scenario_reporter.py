"""
Report generator for scenarios.

Formats scenario analysis as JSON or markdown reports.
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime
from ..schemas import (
    ScenarioWithAnalysis,
    ScenarioReport,
    ScenarioAnalysis,
    SystemResizing,
    CostEstimationData,
    ScenarioRecommendation,
)

logger = logging.getLogger(__name__)


class ScenarioReporter:
    """Generate formatted reports for scenarios."""
    
    def generate_report(
        self, scenario: ScenarioWithAnalysis, format: str = "json"
    ) -> ScenarioReport:
        """
        Generate a formatted report for a scenario.
        
        Args:
            scenario: Complete scenario with all analysis data
            format: Report format ("json" or "markdown")
        
        Returns:
            ScenarioReport with formatted content
        """
        logger.info(f"Generating {format} report for scenario {scenario.id}")
        
        if format == "markdown":
            content = self._generate_markdown_report(scenario)
        else:
            content = self._generate_json_report(scenario)
        
        sections = self._extract_sections(scenario)
        
        return ScenarioReport(
            format=format,
            content=content,
            sections=sections,
            generated_timestamp=datetime.now(),
        )
    
    def _generate_json_report(self, scenario: ScenarioWithAnalysis) -> str:
        """Generate JSON format report."""
        import json
        
        report_data = {
            "scenario": {
                "id": scenario.id,
                "name": scenario.name,
                "description": scenario.description,
                "project_id": scenario.project_id,
                "status": scenario.status,
                "global_objective": scenario.global_objective.model_dump() if scenario.global_objective else None,
            },
            "analysis": scenario.analysis.model_dump() if scenario.analysis else None,
            "resizing": scenario.resizing.model_dump() if scenario.resizing else None,
            "cost_estimation": scenario.cost_estimation.model_dump() if scenario.cost_estimation else None,
            "recommendation": scenario.recommendation.model_dump() if scenario.recommendation else None,
            "user_constraints": [uc.model_dump() for uc in scenario.user_constraints],
            "generated_at": datetime.now().isoformat(),
        }
        
        return json.dumps(report_data, indent=2, default=str)
    
    def _generate_markdown_report(self, scenario: ScenarioWithAnalysis) -> str:
        """Generate markdown format report."""
        lines = []
        
        # Header
        lines.append(f"# Scenario Analysis Report: {scenario.name}\n")
        lines.append(f"**Project ID:** {scenario.project_id}  ")
        lines.append(f"**Status:** {scenario.status}  ")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Description
        if scenario.description:
            lines.append(f"## Description\n\n{scenario.description}\n")
        
        # Global Objective
        if scenario.global_objective:
            go = scenario.global_objective
            lines.append("## Global Objective\n")
            lines.append(f"- **Goal Type:** {go.goal_type}")
            lines.append(f"- **Change Direction:** {go.change_direction}")
            lines.append(f"- **Change Magnitude:** {go.change_magnitude} {go.change_unit}")
            if go.description:
                lines.append(f"- **Description:** {go.description}")
            lines.append("")
        
        # Analysis Summary
        if scenario.analysis:
            lines.append("## Analysis Summary\n")
            if scenario.analysis.scenario_summary:
                lines.append(scenario.analysis.scenario_summary)
                lines.append("")
            
            # Local Objectives
            if scenario.analysis.local_objectives:
                lines.append("### Local Objectives\n")
                for lo in scenario.analysis.local_objectives:
                    lines.append(f"- **{lo.entity_name}** ({lo.entity_type})")
                    lines.append(f"  - Parameter: {lo.parameter}")
                    lines.append(f"  - Base Value: {lo.base_value} {lo.base_unit or ''}")
                    lines.append(f"  - Relevance Score: {lo.relevance_score:.2f}")
                    if lo.rationale:
                        lines.append(f"  - Rationale: {lo.rationale}")
                    lines.append("")
        
        # Resizing Results
        if scenario.resizing and scenario.resizing.resized_parameters:
            lines.append("## System Resizing Results\n")
            for rp in scenario.resizing.resized_parameters:
                lines.append(f"- **{rp.parameter}**")
                lines.append(f"  - Original: {rp.original_value} {rp.unit or ''}")
                lines.append(f"  - Resized: {rp.resized_value} {rp.unit or ''}")
                lines.append(f"  - Method: {rp.calculation_method}")
                if rp.calculation_details:
                    change_pct = rp.calculation_details.get("change_percentage", 0)
                    lines.append(f"  - Change: {change_pct:.2f}%")
                lines.append("")
        
        # Recommendations
        if scenario.recommendation:
            lines.append("## Recommendations\n")
            if scenario.recommendation.recommendation_summary:
                lines.append(scenario.recommendation.recommendation_summary)
                lines.append("")
            
            if scenario.recommendation.approach_options:
                lines.append("### Approach Options\n")
                for i, option in enumerate(scenario.recommendation.approach_options, 1):
                    lines.append(f"#### Option {i}: {option.title}")
                    if option.option_id == scenario.recommendation.recommended_option_id:
                        lines.append("**⭐ RECOMMENDED**\n")
                    lines.append(f"**Rationale:** {option.rationale}\n")
                    
                    if option.expected_effects:
                        lines.append("**Expected Effects:**")
                        for metric, effect in option.expected_effects.items():
                            lines.append(f"- {metric}: {effect.direction}")
                            if effect.estimate_pct:
                                lines.append(f"  ({effect.estimate_pct})")
                            if effect.notes:
                                lines.append(f" - {effect.notes}")
                        lines.append("")
                    
                    if option.dependencies:
                        lines.append(f"**Dependencies:** {', '.join(option.dependencies)}\n")
        
        # Cost Estimation
        if scenario.cost_estimation:
            lines.append("## Cost Estimation\n")
            if scenario.cost_estimation.cost_guidelines:
                lines.append("### Cost Guidelines\n")
                for guideline in scenario.cost_estimation.cost_guidelines[:10]:
                    lines.append(f"- **{guideline.item}**")
                    if guideline.base_cost_value:
                        lines.append(f"  - Base Cost: {guideline.base_cost_value} {guideline.currency or 'USD'}")
                    if guideline.scaling_rule:
                        lines.append(f"  - Scaling Rule: {guideline.scaling_rule}")
                    lines.append("")
        
        # Uncertainties
        if scenario.recommendation and scenario.recommendation.uncertainties:
            lines.append("## Uncertainties and Gaps\n")
            for unc in scenario.recommendation.uncertainties:
                lines.append(f"- **{unc.get('gap', 'Unknown gap')}**")
                lines.append(f"  - Impact: {unc.get('impact', 'Unknown')}")
                lines.append(f"  - Action: {unc.get('action', 'No action specified')}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _extract_sections(self, scenario: ScenarioWithAnalysis) -> Dict[str, Any]:
        """Extract structured sections from scenario."""
        sections = {
            "scenario_info": {
                "id": scenario.id,
                "name": scenario.name,
                "status": scenario.status,
            },
            "global_objective": scenario.global_objective.model_dump() if scenario.global_objective else None,
            "analysis": scenario.analysis.model_dump() if scenario.analysis else None,
            "resizing": scenario.resizing.model_dump() if scenario.resizing else None,
            "recommendation": scenario.recommendation.model_dump() if scenario.recommendation else None,
            "cost_estimation": scenario.cost_estimation.model_dump() if scenario.cost_estimation else None,
        }
        
        return sections

