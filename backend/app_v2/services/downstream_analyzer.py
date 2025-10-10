"""
Downstream impact analyzer service.

This is a CORE USP FEATURE that automatically analyzes how changing one piece
of equipment affects everything downstream in the process flow.

Key capabilities:
1. Process flow traversal following material flow relationships
2. Capacity impact analysis (bottleneck detection)
3. Size distribution impact (crushing/grinding circuits)
4. Equipment replacement/modification assessment
5. Cost impact estimation (CAPEX and OPEX deltas)
6. Confidence scoring for impact predictions

Example use case:
- User reduces primary crusher product size from 8" to 6"
- System analyzes:
  * SAG mill may handle increased throughput (positive impact)
  * Secondary crushers may need capacity increase (negative impact)
  * Conveyors may need modification for changed tonnage
  * Total downstream CAPEX delta: +$2.5M
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any, List, Optional, Tuple, Set
from bson import ObjectId
import logging
from datetime import datetime

from ..repositories.entity_repo import EntityRepository
from ..models.entity import Entity

logger = logging.getLogger(__name__)


class DownstreamAnalyzer:
    """
    Analyzes downstream impacts of equipment changes.
    
    This service traverses the process flow graph and evaluates how
    changes to one equipment affect downstream equipment.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize downstream analyzer.
        
        Args:
            db: Database connection
        """
        self.db = db
        self.entity_repo = EntityRepository(db)
        
        # Impact analysis rules by entity type
        self.impact_rules = self._initialize_impact_rules()
    
    def _initialize_impact_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize impact analysis rules for different entity types.
        
        Returns:
            Dictionary of impact rules by entity type
        """
        return {
            "crusher": {
                "sensitive_to": ["capacity", "product_size", "feed_size"],
                "affects": ["capacity", "product_size"],
                "capacity_tolerance_pct": 10.0,
                "size_tolerance_pct": 15.0
            },
            "mill": {
                "sensitive_to": ["capacity", "feed_size", "product_size"],
                "affects": ["capacity", "product_size", "power_draw"],
                "capacity_tolerance_pct": 15.0,
                "size_tolerance_pct": 20.0
            },
            "conveyor": {
                "sensitive_to": ["capacity", "material_size"],
                "affects": ["capacity"],
                "capacity_tolerance_pct": 20.0,
                "size_tolerance_pct": 10.0
            },
            "screen": {
                "sensitive_to": ["capacity", "feed_size"],
                "affects": ["capacity", "product_size"],
                "capacity_tolerance_pct": 15.0,
                "size_tolerance_pct": 25.0
            },
            "pump": {
                "sensitive_to": ["flow_rate", "head"],
                "affects": ["flow_rate"],
                "capacity_tolerance_pct": 10.0
            },
            "cyclone": {
                "sensitive_to": ["flow_rate", "feed_size"],
                "affects": ["product_size"],
                "capacity_tolerance_pct": 20.0,
                "size_tolerance_pct": 30.0
            },
            "thickener": {
                "sensitive_to": ["flow_rate", "solids_content"],
                "affects": ["flow_rate"],
                "capacity_tolerance_pct": 15.0
            },
            "flotation": {
                "sensitive_to": ["flow_rate", "feed_size"],
                "affects": ["flow_rate"],
                "capacity_tolerance_pct": 10.0,
                "size_tolerance_pct": 15.0
            }
        }
    
    async def analyze_downstream_impacts(
        self,
        changed_entity_id: str,
        parameter_changes: Dict[str, Any],
        max_depth: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze downstream impacts of parameter changes to an entity.
        
        This is the main entry point for downstream analysis.
        
        Args:
            changed_entity_id: ID of entity being changed
            parameter_changes: Dictionary of parameter changes
            max_depth: Maximum depth to traverse (prevent infinite loops)
            
        Returns:
            Impact analysis with affected entities and cost deltas
            
        Example:
            analyzer = DownstreamAnalyzer(db)
            impacts = await analyzer.analyze_downstream_impacts(
                changed_entity_id="507f1f77bcf86cd799439011",
                parameter_changes={
                    "capacity_tph": 4500,  # Reduced from 5000
                    "product_p80": 6.0     # Reduced from 8.0 inches
                }
            )
        """
        try:
            logger.info(
                f"Starting downstream impact analysis",
                extra={
                    "entity_id": changed_entity_id,
                    "changes": list(parameter_changes.keys())
                }
            )
            
            # Get the changed entity
            changed_entity = await self.entity_repo.find_by_id(changed_entity_id)
            if not changed_entity:
                raise ValueError(f"Entity {changed_entity_id} not found")
            
            # Initialize analysis result
            analysis = {
                "changed_entity_id": changed_entity_id,
                "changed_entity_name": changed_entity.get("name", "Unknown"),
                "parameter_changes": parameter_changes,
                "total_entities_analyzed": 0,
                "entities_affected": 0,
                "affected_entities": [],
                "total_capex_delta": 0.0,
                "total_opex_delta_annual": 0.0,
                "analysis_method": "process_flow_traversal",
                "analysis_assumptions": {},
                "analysis_date": datetime.utcnow(),
                "overall_confidence": "medium",
                "warnings": []
            }
            
            # Traverse downstream and analyze impacts
            visited_entities: Set[str] = set()
            
            await self._traverse_and_analyze(
                entity_id=changed_entity_id,
                upstream_changes=parameter_changes,
                analysis=analysis,
                visited=visited_entities,
                depth=0,
                max_depth=max_depth
            )
            
            # Calculate totals
            analysis["total_capex_delta"] = sum(
                e.get("capex_delta", 0.0)
                for e in analysis["affected_entities"]
            )
            
            analysis["total_opex_delta_annual"] = sum(
                e.get("opex_delta_annual", 0.0)
                for e in analysis["affected_entities"]
            )
            
            # Calculate overall confidence
            analysis["overall_confidence"] = self._calculate_overall_confidence(
                analysis["affected_entities"]
            )
            
            logger.info(
                f"Downstream analysis complete",
                extra={
                    "entities_analyzed": analysis["total_entities_analyzed"],
                    "entities_affected": analysis["entities_affected"],
                    "capex_delta": analysis["total_capex_delta"]
                }
            )
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error in downstream analysis: {e}", exc_info=True)
            raise
    
    async def _traverse_and_analyze(
        self,
        entity_id: str,
        upstream_changes: Dict[str, Any],
        analysis: Dict[str, Any],
        visited: Set[str],
        depth: int,
        max_depth: int
    ):
        """
        Recursively traverse downstream entities and analyze impacts.
        
        Args:
            entity_id: Current entity ID
            upstream_changes: Changes from upstream entity
            analysis: Analysis result (modified in place)
            visited: Set of visited entity IDs (prevent cycles)
            depth: Current depth
            max_depth: Maximum depth to traverse
        """
        # Check depth limit
        if depth >= max_depth:
            analysis["warnings"].append(
                f"Maximum traversal depth ({max_depth}) reached"
            )
            return
        
        # Check if already visited (prevent cycles)
        if entity_id in visited:
            return
        
        visited.add(entity_id)
        
        # Get current entity
        entity = await self.entity_repo.find_by_id(entity_id)
        if not entity:
            return
        
        analysis["total_entities_analyzed"] += 1
        
        # Get downstream entities (entities that this one feeds)
        downstream_entities = await self.entity_repo.get_downstream_entities(
            entity_id
        )
        
        if not downstream_entities:
            return
        
        # Analyze impact on each downstream entity
        for downstream in downstream_entities:
            downstream_id = str(downstream["_id"])
            
            # Skip if already visited
            if downstream_id in visited:
                continue
            
            # Assess impact
            impact = await self._assess_impact(
                upstream_entity=entity,
                downstream_entity=downstream,
                upstream_changes=upstream_changes
            )
            
            if impact["has_impact"]:
                analysis["entities_affected"] += 1
                analysis["affected_entities"].append({
                    "entity_id": downstream_id,
                    "entity_name": downstream.get("name", "Unknown"),
                    "entity_type": downstream.get("entity_type", "Unknown"),
                    "impact_type": impact["impact_type"],
                    "impact_description": impact["description"],
                    "capex_delta": impact["capex_delta"],
                    "opex_delta_annual": impact["opex_delta_annual"],
                    "confidence": impact["confidence"],
                    "details": impact.get("details", {})
                })
                
                # Propagate changes downstream
                propagated_changes = impact.get("propagated_changes", {})
                
                if propagated_changes:
                    await self._traverse_and_analyze(
                        entity_id=downstream_id,
                        upstream_changes=propagated_changes,
                        analysis=analysis,
                        visited=visited,
                        depth=depth + 1,
                        max_depth=max_depth
                    )
    
    async def _assess_impact(
        self,
        upstream_entity: Dict[str, Any],
        downstream_entity: Dict[str, Any],
        upstream_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess impact of upstream changes on a downstream entity.
        
        Args:
            upstream_entity: Entity being changed
            downstream_entity: Downstream entity to assess
            upstream_changes: Changes to upstream entity
            
        Returns:
            Impact assessment dictionary
        """
        impact = {
            "has_impact": False,
            "impact_type": "no_change",
            "description": "No significant impact detected",
            "capex_delta": 0.0,
            "opex_delta_annual": 0.0,
            "confidence": "medium",
            "propagated_changes": {},
            "details": {}
        }
        
        try:
            downstream_type = downstream_entity.get("entity_type", "").lower()
            downstream_specs = downstream_entity.get("specifications", {})
            
            # Get impact rules for this entity type
            rules = self._get_entity_rules(downstream_type)
            
            # Check capacity impact
            if "capacity_tph" in upstream_changes or "capacity" in upstream_changes:
                capacity_impact = await self._assess_capacity_impact(
                    upstream_entity,
                    downstream_entity,
                    upstream_changes,
                    rules
                )
                
                if capacity_impact["has_impact"]:
                    impact.update(capacity_impact)
                    return impact
            
            # Check size impact
            if any(k in upstream_changes for k in [
                "product_size", "product_p80", "closed_side_setting_in"
            ]):
                size_impact = await self._assess_size_impact(
                    upstream_entity,
                    downstream_entity,
                    upstream_changes,
                    rules
                )
                
                if size_impact["has_impact"]:
                    impact.update(size_impact)
                    return impact
            
            # Check power impact
            if "power_kw" in upstream_changes:
                power_impact = await self._assess_power_impact(
                    upstream_entity,
                    downstream_entity,
                    upstream_changes,
                    rules
                )
                
                if power_impact["has_impact"]:
                    impact.update(power_impact)
                    return impact
            
        except Exception as e:
            logger.error(f"Error assessing impact: {e}", exc_info=True)
            impact["warnings"] = [str(e)]
        
        return impact
    
    async def _assess_capacity_impact(
        self,
        upstream_entity: Dict[str, Any],
        downstream_entity: Dict[str, Any],
        upstream_changes: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess capacity impact on downstream entity.
        
        Args:
            upstream_entity: Upstream entity
            downstream_entity: Downstream entity
            upstream_changes: Changes to upstream
            rules: Impact rules for entity type
            
        Returns:
            Capacity impact assessment
        """
        impact = {
            "has_impact": False,
            "impact_type": "no_change",
            "description": "",
            "capex_delta": 0.0,
            "opex_delta_annual": 0.0,
            "confidence": "medium",
            "propagated_changes": {},
            "details": {}
        }
        
        # Get capacities
        upstream_specs = upstream_entity.get("specifications", {})
        downstream_specs = downstream_entity.get("specifications", {})
        
        upstream_capacity_old = upstream_specs.get("capacity_tph", 0)
        upstream_capacity_new = upstream_changes.get(
            "capacity_tph",
            upstream_changes.get("capacity", upstream_capacity_old)
        )
        
        downstream_capacity = downstream_specs.get("capacity_tph", 0)
        
        if upstream_capacity_old == 0 or downstream_capacity == 0:
            return impact
        
        # Calculate capacity change
        capacity_change_pct = (
            (upstream_capacity_new - upstream_capacity_old) / upstream_capacity_old * 100
        )
        
        # Check if change exceeds tolerance
        tolerance = rules.get("capacity_tolerance_pct", 10.0)
        
        if abs(capacity_change_pct) < tolerance:
            return impact
        
        # Determine impact type
        if upstream_capacity_new > downstream_capacity:
            # Upstream increased beyond downstream capacity - bottleneck
            impact["has_impact"] = True
            impact["impact_type"] = "capacity_change"
            impact["description"] = (
                f"Upstream capacity increase ({capacity_change_pct:.1f}%) "
                f"exceeds downstream capacity. Downstream equipment may become bottleneck."
            )
            
            # Estimate cost to increase downstream capacity
            impact["capex_delta"] = await self._estimate_capacity_increase_cost(
                downstream_entity,
                required_capacity=upstream_capacity_new
            )
            
            impact["confidence"] = "medium"
            impact["details"] = {
                "upstream_capacity_old": upstream_capacity_old,
                "upstream_capacity_new": upstream_capacity_new,
                "downstream_capacity_current": downstream_capacity,
                "capacity_shortfall_tph": upstream_capacity_new - downstream_capacity,
                "capacity_change_pct": capacity_change_pct
            }
            
            # Propagate capacity change
            impact["propagated_changes"] = {
                "capacity_tph": upstream_capacity_new
            }
        
        elif upstream_capacity_new < upstream_capacity_old:
            # Upstream decreased - downstream may have excess capacity
            impact["has_impact"] = True
            impact["impact_type"] = "capacity_change"
            impact["description"] = (
                f"Upstream capacity decreased ({capacity_change_pct:.1f}%). "
                f"Downstream equipment may have excess capacity."
            )
            
            # Generally no CAPEX impact (existing equipment can handle less)
            # But may affect OPEX (lower utilization, different operating point)
            impact["capex_delta"] = 0.0
            impact["opex_delta_annual"] = await self._estimate_opex_change(
                downstream_entity,
                capacity_change_pct=capacity_change_pct
            )
            
            impact["confidence"] = "high"
            impact["details"] = {
                "upstream_capacity_old": upstream_capacity_old,
                "upstream_capacity_new": upstream_capacity_new,
                "downstream_capacity_current": downstream_capacity,
                "capacity_change_pct": capacity_change_pct,
                "utilization_pct": (upstream_capacity_new / downstream_capacity * 100)
            }
            
            # Propagate capacity change
            impact["propagated_changes"] = {
                "capacity_tph": upstream_capacity_new
            }
        
        return impact
    
    async def _assess_size_impact(
        self,
        upstream_entity: Dict[str, Any],
        downstream_entity: Dict[str, Any],
        upstream_changes: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess size distribution impact on downstream entity.
        
        Particularly important for crushing and grinding circuits.
        
        Args:
            upstream_entity: Upstream entity
            downstream_entity: Downstream entity
            upstream_changes: Changes to upstream
            rules: Impact rules for entity type
            
        Returns:
            Size impact assessment
        """
        impact = {
            "has_impact": False,
            "impact_type": "no_change",
            "description": "",
            "capex_delta": 0.0,
            "opex_delta_annual": 0.0,
            "confidence": "medium",
            "propagated_changes": {},
            "details": {}
        }
        
        # Get size parameters
        upstream_specs = upstream_entity.get("specifications", {})
        downstream_specs = downstream_entity.get("specifications", {})
        
        # Determine which size parameter changed
        size_param_old = None
        size_param_new = None
        param_name = None
        
        for param in ["product_p80", "product_size", "closed_side_setting_in"]:
            if param in upstream_changes:
                size_param_old = upstream_specs.get(param, 0)
                size_param_new = upstream_changes[param]
                param_name = param
                break
        
        if size_param_old is None or size_param_new is None:
            return impact
        
        # Calculate size change
        if size_param_old == 0:
            return impact
        
        size_change_pct = (
            (size_param_new - size_param_old) / size_param_old * 100
        )
        
        # Check tolerance
        tolerance = rules.get("size_tolerance_pct", 15.0)
        
        if abs(size_change_pct) < tolerance:
            return impact
        
        # Determine impact based on downstream entity type
        downstream_type = downstream_entity.get("entity_type", "").lower()
        
        if "mill" in downstream_type or "grinding" in downstream_type:
            # Finer feed to mill generally improves throughput
            if size_param_new < size_param_old:
                impact["has_impact"] = True
                impact["impact_type"] = "capacity_change"
                impact["description"] = (
                    f"Finer feed size ({size_change_pct:.1f}% reduction) "
                    f"may increase mill throughput by 5-15%."
                )
                
                # Estimate throughput benefit
                throughput_increase_pct = min(abs(size_change_pct) * 0.3, 15.0)
                
                impact["capex_delta"] = 0.0  # No CAPEX for existing mill
                impact["opex_delta_annual"] = 0.0  # May slightly increase power
                
                impact["confidence"] = "medium"
                impact["details"] = {
                    "feed_size_old": size_param_old,
                    "feed_size_new": size_param_new,
                    "size_change_pct": size_change_pct,
                    "estimated_throughput_increase_pct": throughput_increase_pct
                }
                
                # Propagate size change
                impact["propagated_changes"] = {
                    "feed_size": size_param_new,
                    "capacity_increase_pct": throughput_increase_pct
                }
            else:
                # Coarser feed may reduce throughput
                impact["has_impact"] = True
                impact["impact_type"] = "capacity_change"
                impact["description"] = (
                    f"Coarser feed size ({size_change_pct:.1f}% increase) "
                    f"may decrease mill throughput."
                )
                
                impact["confidence"] = "medium"
        
        elif "crusher" in downstream_type:
            # Finer feed to crusher may increase capacity
            if size_param_new < size_param_old:
                impact["has_impact"] = True
                impact["impact_type"] = "capacity_change"
                impact["description"] = (
                    f"Finer feed size ({size_change_pct:.1f}% reduction) "
                    f"may allow increased crusher capacity."
                )
                
                impact["confidence"] = "low"  # Complex relationship
        
        elif "conveyor" in downstream_type:
            # Size change may affect conveyor handling
            max_lump = downstream_specs.get("max_lump_size_mm", 0)
            
            if size_param_new > max_lump and max_lump > 0:
                impact["has_impact"] = True
                impact["impact_type"] = "modification_required"
                impact["description"] = (
                    f"Increased product size exceeds conveyor max lump size. "
                    f"Conveyor modification required."
                )
                
                impact["capex_delta"] = await self._estimate_conveyor_modification_cost(
                    downstream_entity
                )
                
                impact["confidence"] = "high"
        
        return impact
    
    async def _assess_power_impact(
        self,
        upstream_entity: Dict[str, Any],
        downstream_entity: Dict[str, Any],
        upstream_changes: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess power-related impact on downstream entity.
        
        Args:
            upstream_entity: Upstream entity
            downstream_entity: Downstream entity
            upstream_changes: Changes to upstream
            rules: Impact rules for entity type
            
        Returns:
            Power impact assessment
        """
        impact = {
            "has_impact": False,
            "impact_type": "no_change",
            "description": "",
            "capex_delta": 0.0,
            "opex_delta_annual": 0.0,
            "confidence": "medium",
            "propagated_changes": {},
            "details": {}
        }
        
        # Power changes generally don't directly impact downstream
        # unless it affects throughput/capacity
        
        return impact
    
    async def _estimate_capacity_increase_cost(
        self,
        entity: Dict[str, Any],
        required_capacity: float
    ) -> float:
        """
        Estimate cost to increase entity capacity.
        
        Args:
            entity: Entity to modify
            required_capacity: Required capacity in tph
            
        Returns:
            Estimated CAPEX delta
        """
        try:
            current_capacity = entity.get("specifications", {}).get("capacity_tph", 0)
            
            if current_capacity == 0:
                return 0.0
            
            capacity_ratio = required_capacity / current_capacity
            
            # If ratio < 1.3, may be able to modify existing equipment
            if capacity_ratio < 1.3:
                # Estimate modification cost (10-20% of installed cost)
                current_cost = entity.get("cost_data", {}).get(
                    "total_installed_cost", 0
                )
                return current_cost * 0.15
            
            # If ratio >= 1.3, likely need new equipment
            else:
                # Estimate new equipment cost using scaling law
                # Cost scales approximately with capacity^0.6
                current_cost = entity.get("cost_data", {}).get(
                    "total_installed_cost", 0
                )
                
                if current_cost == 0:
                    return 0.0
                
                new_cost = current_cost * (capacity_ratio ** 0.6)
                
                # Delta is new cost minus salvage value of old
                salvage_value = current_cost * 0.2  # Assume 20% salvage
                
                return new_cost - salvage_value
        
        except Exception as e:
            logger.error(f"Error estimating capacity increase cost: {e}")
            return 0.0
    
    async def _estimate_conveyor_modification_cost(
        self,
        conveyor: Dict[str, Any]
    ) -> float:
        """
        Estimate cost to modify conveyor for larger material.
        
        Args:
            conveyor: Conveyor entity
            
        Returns:
            Estimated CAPEX delta
        """
        try:
            # Conveyor modification typically 5-15% of installed cost
            installed_cost = conveyor.get("cost_data", {}).get(
                "total_installed_cost", 0
            )
            
            return installed_cost * 0.10
        
        except Exception as e:
            logger.error(f"Error estimating conveyor modification cost: {e}")
            return 0.0
    
    async def _estimate_opex_change(
        self,
        entity: Dict[str, Any],
        capacity_change_pct: float
    ) -> float:
        """
        Estimate OPEX change due to capacity change.
        
        Args:
            entity: Entity
            capacity_change_pct: Capacity change percentage
            
        Returns:
            Annual OPEX delta
        """
        try:
            current_opex = entity.get("cost_data", {}).get(
                "total_annual_opex", 0
            )
            
            if current_opex == 0:
                return 0.0
            
            # OPEX scales roughly linearly with capacity
            # But with some fixed costs, so use 0.7 factor
            opex_delta = current_opex * (capacity_change_pct / 100) * 0.7
            
            return opex_delta
        
        except Exception as e:
            logger.error(f"Error estimating OPEX change: {e}")
            return 0.0
    
    def _get_entity_rules(self, entity_type: str) -> Dict[str, Any]:
        """
        Get impact rules for entity type.
        
        Args:
            entity_type: Type of entity
            
        Returns:
            Impact rules dictionary
        """
        # Try exact match
        if entity_type in self.impact_rules:
            return self.impact_rules[entity_type]
        
        # Try partial match
        for rule_type, rules in self.impact_rules.items():
            if rule_type in entity_type or entity_type in rule_type:
                return rules
        
        # Return default rules
        return {
            "sensitive_to": ["capacity"],
            "affects": ["capacity"],
            "capacity_tolerance_pct": 10.0,
            "size_tolerance_pct": 15.0
        }
    
    def _calculate_overall_confidence(
        self,
        affected_entities: List[Dict[str, Any]]
    ) -> str:
        """
        Calculate overall confidence for impact analysis.
        
        Args:
            affected_entities: List of affected entities
            
        Returns:
            Confidence level: "high", "medium", or "low"
        """
        if not affected_entities:
            return "high"
        
        # Count confidence levels
        confidence_counts = {"high": 0, "medium": 0, "low": 0}
        
        for entity in affected_entities:
            confidence = entity.get("confidence", "medium")
            confidence_counts[confidence] += 1
        
        total = len(affected_entities)
        
        # If majority are high confidence
        if confidence_counts["high"] / total > 0.7:
            return "high"
        
        # If any are low confidence
        elif confidence_counts["low"] > 0:
            return "low"
        
        else:
            return "medium"
    
    async def get_impact_summary(
        self,
        scenario_id: str
    ) -> Dict[str, Any]:
        """
        Get impact summary for all options in a scenario.
        
        Args:
            scenario_id: Scenario ID
            
        Returns:
            Impact summary
        """
        try:
            # This would aggregate impacts across all options
            # For now, return placeholder
            return {
                "scenario_id": scenario_id,
                "total_options": 0,
                "avg_entities_affected": 0,
                "avg_capex_delta": 0.0,
                "impact_range": {
                    "min_capex": 0.0,
                    "max_capex": 0.0
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting impact summary: {e}")
            return {}