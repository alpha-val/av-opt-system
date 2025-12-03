"""
Cost estimation preparation component.

Identifies cost reference data and prepares cost estimation data.
Optionally generates cost estimates if user preference enabled.
"""

from typing import Dict, Any, List, Optional
import logging
from ....adapters.mongo.client import db
from ....domain.projects.repository import get_project_entities_relations
from ..schemas import CostEstimationData, CostGuideline, SystemResizing, ScenarioAnalysis
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class CostPreparator:
    """Prepare cost estimation data for scenarios."""
    
    async def prepare(
        self,
        project_id: str,
        analysis: ScenarioAnalysis,
        resizing: Optional[SystemResizing] = None,
        generate_estimates: bool = False,
    ) -> CostEstimationData:
        """
        Prepare cost estimation data.
        
        Args:
            project_id: Project identifier
            analysis: ScenarioAnalysis with local objectives
            resizing: Optional SystemResizing with resized parameters
            generate_estimates: If True, generate and store cost estimates
        
        Returns:
            CostEstimationData with guidelines and drivers
        """
        logger.info(f"Preparing cost estimation data for project {project_id}")
        
        try:
            # Get entities from base case and tabular data
            entities_data = await get_project_entities_relations(project_id)
            entities = entities_data.entities
            # Convert to dict format
            entities_list = [e.model_dump() if hasattr(e, 'model_dump') else e for e in entities]
            
            # Extract cost guidelines from entities
            cost_guidelines = self._extract_cost_guidelines(entities_list)
            
            # Identify cost drivers from local objectives
            cost_drivers = self._identify_cost_drivers(analysis, resizing)
            
            # Perform sensitivity analysis if resizing data available
            sensitivity_analysis = None
            if resizing:
                sensitivity_analysis = self._calculate_sensitivity(analysis, resizing)
            
            # Optionally generate cost estimates
            cost_estimate_id = None
            if generate_estimates:
                cost_estimate_id = self._generate_cost_estimates(
                    project_id, analysis, resizing, cost_guidelines
                )
            
            return CostEstimationData(
                cost_guidelines=cost_guidelines,
                cost_drivers=cost_drivers,
                sensitivity_analysis=sensitivity_analysis,
                cost_estimate_id=cost_estimate_id,
                prepared_timestamp=datetime.now(timezone.utc),
            )
            
        except Exception as e:
            logger.error(f"Error preparing cost estimation data: {e}", exc_info=True)
            return CostEstimationData(
                cost_guidelines=[],
                cost_drivers=[],
                prepared_timestamp=datetime.now(timezone.utc),
            )
    
    def _extract_cost_guidelines(self, entities: List[Dict[str, Any]]) -> List[CostGuideline]:
        """Extract cost guidelines from entities (especially from tabular data)."""
        guidelines = []
        
        for entity in entities:
            properties = entity.get("properties", {})
            
            # Look for cost-related entities
            cost_value = properties.get("cost_value")
            if cost_value is None:
                # Check attributes
                attributes = properties.get("attributes", [])
                for attr in attributes:
                    if isinstance(attr, dict) and "cost" in attr.get("name", "").lower():
                        cost_value = attr.get("value")
                        break
            
            if cost_value is not None:
                entity_name = entity.get("name") or properties.get("name", "Unknown")
                entity_type = entity.get("type") or properties.get("type", "Unknown")
                
                # Extract scaling rule if available
                scaling_rule = properties.get("scaling_rule") or properties.get("cost_scaling_rule")
                
                guidelines.append(
                    CostGuideline(
                        item=f"{entity_type}: {entity_name}",
                        base_cost_value=float(cost_value) if isinstance(cost_value, (int, float)) else None,
                        currency=properties.get("currency") or properties.get("cost_currency"),
                        basis_year=properties.get("basis_year") or properties.get("cost_basis_year"),
                        scaling_rule=scaling_rule,
                        risk_notes=properties.get("cost_risk_notes"),
                        estimation_note=properties.get("cost_estimation_note"),
                    )
                )
        
        return guidelines
    
    def _identify_cost_drivers(
        self, analysis: ScenarioAnalysis, resizing: Optional[SystemResizing]
    ) -> List[Dict[str, Any]]:
        """Identify entities/parameters that drive costs."""
        drivers = []
        
        # Cost-related local objectives are cost drivers
        for lo in analysis.local_objectives:
            if "cost" in lo.parameter.lower() or lo.entity_type in ["Equipment", "Material", "Civil", "Electrical"]:
                driver = {
                    "entity_id": lo.entity_id,
                    "entity_name": lo.entity_name,
                    "entity_type": lo.entity_type,
                    "parameter": lo.parameter,
                    "relevance_score": lo.relevance_score,
                    "base_value": lo.base_value,
                    "base_unit": lo.base_unit,
                }
                
                # Add resized value if available
                if resizing:
                    for rp in resizing.resized_parameters:
                        if rp.entity_id == lo.entity_id and rp.parameter == lo.parameter:
                            driver["resized_value"] = rp.resized_value
                            driver["change_percentage"] = rp.calculation_details.get("change_percentage")
                            break
                
                drivers.append(driver)
        
        return drivers
    
    def _calculate_sensitivity(
        self, analysis: ScenarioAnalysis, resizing: SystemResizing
    ) -> Dict[str, Any]:
        """Calculate cost sensitivity to parameter changes."""
        sensitivity = {
            "high_impact_parameters": [],
            "moderate_impact_parameters": [],
            "low_impact_parameters": [],
        }
        
        for rp in resizing.resized_parameters:
            change_pct = abs(rp.calculation_details.get("change_percentage", 0))
            
            param_info = {
                "entity_id": rp.entity_id,
                "parameter": rp.parameter,
                "change_percentage": change_pct,
                "calculation_method": rp.calculation_method,
            }
            
            if change_pct >= 10:
                sensitivity["high_impact_parameters"].append(param_info)
            elif change_pct >= 5:
                sensitivity["moderate_impact_parameters"].append(param_info)
            else:
                sensitivity["low_impact_parameters"].append(param_info)
        
        return sensitivity
    
    def _generate_cost_estimates(
        self,
        project_id: str,
        analysis: ScenarioAnalysis,
        resizing: Optional[SystemResizing],
        cost_guidelines: List[CostGuideline],
    ) -> Optional[str]:
        """
        Generate cost estimates and store in cost_estimates collection.
        
        Returns cost_estimate_id if generated, None otherwise.
        """
        try:
            from ...adapters.mongo.client import db
            import uuid
            
            cost_estimates_collection = db().cost_estimates
            
            # Calculate total cost impact
            total_cost_impact = 0.0
            cost_items = []
            
            for guideline in cost_guidelines:
                if guideline.base_cost_value and resizing:
                    # Find corresponding resized parameter
                    for rp in resizing.resized_parameters:
                        if guideline.item.lower() in rp.entity_id.lower() or rp.entity_id.lower() in guideline.item.lower():
                            # Apply scaling
                            scale_factor = rp.calculation_details.get("scale_factor", 1.0)
                            resized_cost = guideline.base_cost_value * scale_factor
                            cost_change = resized_cost - guideline.base_cost_value
                            
                            cost_items.append({
                                "item": guideline.item,
                                "base_cost": guideline.base_cost_value,
                                "resized_cost": resized_cost,
                                "cost_change": cost_change,
                                "currency": guideline.currency,
                            })
                            
                            total_cost_impact += cost_change
                            break
            
            # Create cost estimate document
            estimate_id = str(uuid.uuid4())
            estimate_doc = {
                "id": estimate_id,
                "estimate_id": estimate_id,
                "project_id": project_id,
                "cost_items": cost_items,
                "total_cost_impact": total_cost_impact,
                "currency": cost_guidelines[0].currency if cost_guidelines else "USD",
                "basis_year": cost_guidelines[0].basis_year if cost_guidelines else None,
                "created_at": datetime.now(timezone.utc),
                "created_by": None,  # Will be set by service layer
            }
            
            cost_estimates_collection.insert_one(estimate_doc)
            logger.info(f"Generated cost estimate {estimate_id}")
            
            return estimate_id
            
        except Exception as e:
            logger.error(f"Failed to generate cost estimates: {e}", exc_info=True)
            return None

