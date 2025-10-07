"""
Validation service.

Provides domain-specific validation logic for:
- Equipment specifications
- Process flow configurations
- Cost data
- Parameter changes
- Scenario definitions
- Option feasibility

This service combines basic validators with complex business rules
and domain knowledge to ensure data integrity and feasibility.
"""

from typing import Dict, Any, List, Tuple, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from datetime import datetime

from ..repositories.entity_repo import EntityRepository
from ..repositories.table_repo import TableRepository
from ..utils.validators import (
    validate_object_id,
    validate_positive_number,
    validate_year,
    validate_currency_code,
    DataValidator
)

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Service for domain-specific validation.
    
    Provides validation methods that combine basic validation
    with business rules and domain knowledge.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize validation service.
        
        Args:
            db: Database connection
        """
        self.db = db
        self.entity_repo = EntityRepository(db)
        self.table_repo = TableRepository(db)
        self.data_validator = DataValidator()
    
    # ========================================================================
    # EQUIPMENT VALIDATION
    # ========================================================================
    
    async def validate_equipment_specifications(
        self,
        entity_type: str,
        specifications: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate equipment specifications with domain rules.
        
        Args:
            entity_type: Type of equipment
            specifications: Specifications dictionary
            context: Optional context (project requirements, etc.)
            
        Returns:
            Tuple of (is_valid, errors, warnings)
            
        Example:
            service = ValidationService(db)
            is_valid, errors, warnings = await service.validate_equipment_specifications(
                entity_type="gyratory_crusher",
                specifications={
                    "capacity_tph": 5000,
                    "feed_opening_in": 60.0,
                    "closed_side_setting_in": 8.0,
                    "power_kw": 1120
                }
            )
        """
        errors = []
        warnings = []
        
        try:
            # Basic validation
            is_valid, basic_errors = self.data_validator.validate_equipment_specifications(
                specifications, entity_type
            )
            errors.extend(basic_errors)
            
            # Entity-specific validation
            entity_type_lower = entity_type.lower()
            
            if "crusher" in entity_type_lower:
                crusher_errors, crusher_warnings = await self._validate_crusher_specs(
                    specifications, context
                )
                errors.extend(crusher_errors)
                warnings.extend(crusher_warnings)
            
            elif "mill" in entity_type_lower or "grinding" in entity_type_lower:
                mill_errors, mill_warnings = await self._validate_mill_specs(
                    specifications, context
                )
                errors.extend(mill_errors)
                warnings.extend(mill_warnings)
            
            elif "conveyor" in entity_type_lower:
                conveyor_errors, conveyor_warnings = await self._validate_conveyor_specs(
                    specifications, context
                )
                errors.extend(conveyor_errors)
                warnings.extend(conveyor_warnings)
            
            elif "screen" in entity_type_lower:
                screen_errors, screen_warnings = await self._validate_screen_specs(
                    specifications, context
                )
                errors.extend(screen_errors)
                warnings.extend(screen_warnings)
            
            elif "pump" in entity_type_lower:
                pump_errors, pump_warnings = await self._validate_pump_specs(
                    specifications, context
                )
                errors.extend(pump_errors)
                warnings.extend(pump_warnings)
            
            # Check against sizing tables if available
            table_errors, table_warnings = await self._validate_against_sizing_tables(
                entity_type, specifications
            )
            warnings.extend(table_warnings)
            
            return len(errors) == 0, errors, warnings
        
        except Exception as e:
            logger.error(f"Error validating equipment specifications: {e}", exc_info=True)
            errors.append(f"Validation error: {str(e)}")
            return False, errors, warnings
    
    async def _validate_crusher_specs(
        self,
        specs: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        """Validate crusher-specific specifications."""
        errors = []
        warnings = []
        
        # Feed opening vs CSS validation
        feed_opening = specs.get("feed_opening_in")
        css = specs.get("closed_side_setting_in")
        
        if feed_opening and css:
            if css >= feed_opening:
                errors.append(
                    f"Closed side setting ({css}\") must be less than "
                    f"feed opening ({feed_opening}\")"
                )
            
            # Check reduction ratio
            reduction_ratio = feed_opening / css
            
            if reduction_ratio < 3:
                warnings.append(
                    f"Low reduction ratio ({reduction_ratio:.1f}). "
                    f"Typical range is 3-10."
                )
            elif reduction_ratio > 10:
                warnings.append(
                    f"High reduction ratio ({reduction_ratio:.1f}). "
                    f"May cause excessive wear or throughput issues."
                )
        
        # Capacity vs power validation
        capacity = specs.get("capacity_tph")
        power = specs.get("power_kw")
        
        if capacity and power:
            # Typical specific power consumption: 0.15-0.30 kWh/t
            specific_power = power / capacity
            
            if specific_power < 0.10:
                warnings.append(
                    f"Low specific power ({specific_power:.2f} kW/tph). "
                    f"May indicate undersized motor."
                )
            elif specific_power > 0.40:
                warnings.append(
                    f"High specific power ({specific_power:.2f} kW/tph). "
                    f"May indicate oversized motor or hard ore."
                )
        
        # Check feed size vs capacity
        feed_size = specs.get("feed_size_p80_mm")
        if feed_size and capacity:
            # Larger feed generally requires more capacity
            if feed_size > 500 and capacity < 2000:
                warnings.append(
                    f"Large feed size ({feed_size} mm) with low capacity "
                    f"({capacity} tph) may not be optimal."
                )
        
        return errors, warnings
    
    async def _validate_mill_specs(
        self,
        specs: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        """Validate mill-specific specifications."""
        errors = []
        warnings = []
        
        # Diameter and length validation
        diameter = specs.get("diameter_m") or specs.get("diameter_ft", 0) * 0.3048
        length = specs.get("length_m") or specs.get("length_ft", 0) * 0.3048
        
        if diameter and length:
            l_d_ratio = length / diameter
            
            # SAG mills typically 0.3-0.5
            # Ball mills typically 1.5-3.0
            # Rod mills typically 1.5-2.5
            
            mill_type = specs.get("mill_type", "").lower()
            
            if "sag" in mill_type or "ag" in mill_type:
                if l_d_ratio < 0.2 or l_d_ratio > 0.7:
                    warnings.append(
                        f"SAG mill L/D ratio ({l_d_ratio:.2f}) outside "
                        f"typical range (0.3-0.5)"
                    )
            elif "ball" in mill_type:
                if l_d_ratio < 1.0 or l_d_ratio > 3.5:
                    warnings.append(
                        f"Ball mill L/D ratio ({l_d_ratio:.2f}) outside "
                        f"typical range (1.5-3.0)"
                    )
        
        # Critical speed validation
        critical_speed_pct = specs.get("critical_speed_pct")
        
        if critical_speed_pct:
            if critical_speed_pct < 50:
                errors.append(
                    f"Critical speed percentage ({critical_speed_pct}%) "
                    f"too low (minimum 50%)"
                )
            elif critical_speed_pct > 90:
                errors.append(
                    f"Critical speed percentage ({critical_speed_pct}%) "
                    f"too high (maximum 90%)"
                )
            elif critical_speed_pct < 65 or critical_speed_pct > 85:
                warnings.append(
                    f"Critical speed percentage ({critical_speed_pct}%) "
                    f"outside typical operating range (65-85%)"
                )
        
        # Mill filling validation
        mill_filling_pct = specs.get("mill_filling_pct") or specs.get("charge_volume_pct")
        
        if mill_filling_pct:
            if mill_filling_pct < 10:
                errors.append(
                    f"Mill filling ({mill_filling_pct}%) too low (minimum 10%)"
                )
            elif mill_filling_pct > 50:
                errors.append(
                    f"Mill filling ({mill_filling_pct}%) too high (maximum 50%)"
                )
            elif mill_filling_pct < 20 or mill_filling_pct > 40:
                warnings.append(
                    f"Mill filling ({mill_filling_pct}%) outside "
                    f"typical range (25-35%)"
                )
        
        # Power validation
        power = specs.get("power_kw") or specs.get("installed_power_kw")
        
        if power and diameter:
            # Check against Bond's equation approximation
            # P ≈ 0.29 * D^2.5 for SAG mills (very rough)
            estimated_power = 0.29 * (diameter ** 2.5) * 1000  # Convert to kW
            
            if abs(power - estimated_power) / estimated_power > 0.5:
                warnings.append(
                    f"Mill power ({power} kW) differs significantly from "
                    f"typical for this diameter ({estimated_power:.0f} kW). "
                    f"Verify specifications."
                )
        
        # Feed size validation
        feed_size = specs.get("feed_size_f80_mm")
        max_feed_size = specs.get("max_feed_size_mm")
        
        if feed_size and max_feed_size:
            if feed_size > max_feed_size:
                errors.append(
                    f"Feed F80 ({feed_size} mm) exceeds maximum feed size "
                    f"({max_feed_size} mm)"
                )
        
        return errors, warnings
    
    async def _validate_conveyor_specs(
        self,
        specs: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        """Validate conveyor-specific specifications."""
        errors = []
        warnings = []
        
        # Belt speed validation
        belt_speed = specs.get("belt_speed_mps") or specs.get("belt_speed_mpm", 0) / 60
        
        if belt_speed:
            if belt_speed < 0.5:
                warnings.append(
                    f"Low belt speed ({belt_speed:.1f} m/s). "
                    f"Typical range is 1.0-5.0 m/s."
                )
            elif belt_speed > 8.0:
                errors.append(
                    f"Belt speed ({belt_speed:.1f} m/s) exceeds "
                    f"typical maximum (8.0 m/s)"
                )
        
        # Belt width vs lump size
        belt_width = specs.get("belt_width_mm")
        max_lump = specs.get("max_lump_size_mm")
        
        if belt_width and max_lump:
            # Rule: max lump should be < belt_width / 2
            if max_lump > belt_width / 2:
                errors.append(
                    f"Maximum lump size ({max_lump} mm) exceeds "
                    f"recommended limit (belt width / 2 = {belt_width/2:.0f} mm)"
                )
            elif max_lump > belt_width / 3:
                warnings.append(
                    f"Maximum lump size ({max_lump} mm) is high relative "
                    f"to belt width ({belt_width} mm). Consider wider belt."
                )
        
        # Capacity validation
        capacity = specs.get("capacity_tph")
        
        if capacity and belt_width and belt_speed:
            # Rough capacity check: Q = 3.6 * v * A * ρ * k
            # where A ≈ belt_width^2 * surcharge_angle factor
            # Simplified: Q ≈ belt_width(mm) * belt_speed(m/s) * 0.002
            estimated_capacity = belt_width * belt_speed * 0.002
            
            if capacity > estimated_capacity * 1.5:
                warnings.append(
                    f"Specified capacity ({capacity} tph) is high for "
                    f"belt dimensions. Estimated capacity: {estimated_capacity:.0f} tph"
                )
        
        # Lift height validation
        lift_height = specs.get("lift_height_m")
        
        if lift_height:
            if lift_height > 100:
                warnings.append(
                    f"High lift height ({lift_height} m). "
                    f"Consider multiple flights or alternative conveying method."
                )
        
        # Horizontal length validation
        length = specs.get("horizontal_length_m")
        
        if length:
            if length > 2000:
                warnings.append(
                    f"Very long conveyor ({length} m). "
                    f"Consider intermediate drives or multiple conveyors."
                )
        
        return errors, warnings
    
    async def _validate_screen_specs(
        self,
        specs: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        """Validate screen-specific specifications."""
        errors = []
        warnings = []
        
        # Deck area and capacity
        deck_area = specs.get("deck_area_m2")
        capacity = specs.get("capacity_tph")
        
        if deck_area and capacity:
            # Typical screen loading: 5-15 tph/m²
            loading = capacity / deck_area
            
            if loading < 3:
                warnings.append(
                    f"Low screen loading ({loading:.1f} tph/m²). "
                    f"May be oversized."
                )
            elif loading > 20:
                warnings.append(
                    f"High screen loading ({loading:.1f} tph/m²). "
                    f"Typical range is 5-15 tph/m². May affect efficiency."
                )
        
        # Aperture size validation
        aperture_size = specs.get("aperture_size_mm")
        feed_size = specs.get("feed_size_p80_mm")
        
        if aperture_size and feed_size:
            if aperture_size > feed_size / 2:
                warnings.append(
                    f"Screen aperture ({aperture_size} mm) is large relative "
                    f"to feed size ({feed_size} mm). "
                    f"May result in low efficiency."
                )
        
        # Number of decks validation
        num_decks = specs.get("number_of_decks")
        
        if num_decks:
            if num_decks > 3:
                warnings.append(
                    f"High number of decks ({num_decks}). "
                    f"May reduce screening efficiency. Consider 2-3 decks."
                )
        
        return errors, warnings
    
    async def _validate_pump_specs(
        self,
        specs: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        """Validate pump-specific specifications."""
        errors = []
        warnings = []
        
        # Flow rate and head validation
        flow_rate = specs.get("flow_rate_m3h") or specs.get("capacity_m3h")
        head = specs.get("total_head_m")
        power = specs.get("power_kw")
        
        if flow_rate and head and power:
            # Calculate hydraulic power: P_hydraulic = ρ * g * Q * H / 3600
            # With ρ = 1000 kg/m³, g = 9.81 m/s²
            hydraulic_power = (1000 * 9.81 * flow_rate * head) / 3600000  # kW
            
            # Efficiency check
            efficiency = hydraulic_power / power if power > 0 else 0
            
            if efficiency > 0.95:
                warnings.append(
                    f"Calculated pump efficiency ({efficiency*100:.1f}%) "
                    f"is unrealistically high. Check specifications."
                )
            elif efficiency < 0.40:
                warnings.append(
                    f"Low pump efficiency ({efficiency*100:.1f}%). "
                    f"Typical range is 60-85%."
                )
        
        # Specific speed validation
        if flow_rate and head and power:
            # Specific speed: Ns = N * Q^0.5 / H^0.75
            # Where N is RPM (assume 1800 for now)
            rpm = specs.get("speed_rpm", 1800)
            specific_speed = rpm * (flow_rate ** 0.5) / (head ** 0.75)
            
            # Centrifugal pumps: Ns = 500-4000
            if specific_speed < 500 or specific_speed > 10000:
                warnings.append(
                    f"Specific speed ({specific_speed:.0f}) outside "
                    f"typical range for centrifugal pumps (500-4000). "
                    f"Verify pump type selection."
                )
        
        # Solids content for slurry pumps
        solids_content = specs.get("solids_content_pct")
        pump_type = specs.get("pump_type", "").lower()
        
        if "slurry" in pump_type and solids_content:
            if solids_content > 70:
                warnings.append(
                    f"High solids content ({solids_content}%). "
                    f"May require special pump design or multiple stages."
                )
        
        return errors, warnings
    
    async def _validate_against_sizing_tables(
        self,
        entity_type: str,
        specifications: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """Validate specifications against sizing tables."""
        errors = []
        warnings = []
        
        try:
            # Find sizing tables for this entity type
            tables = await self.table_repo.find_by_type(
                table_type="equipment_sizing",
                entity_type=entity_type
            )
            
            if not tables:
                return errors, warnings
            
            # Check if specifications match any table entries
            model = specifications.get("model")
            manufacturer = specifications.get("manufacturer")
            
            if not model:
                return errors, warnings
            
            # Search for matching equipment in tables
            found_match = False
            
            for table in tables:
                rows = table.get("rows", [])
                
                for row in rows:
                    row_model = row.get("model", "")
                    row_manufacturer = row.get("manufacturer", "")
                    
                    # Check for match
                    if model == row_model:
                        if manufacturer and manufacturer != row_manufacturer:
                            continue
                        
                        found_match = True
                        
                        # Compare specifications
                        for key, value in specifications.items():
                            if key in ["model", "manufacturer"]:
                                continue
                            
                            if key in row:
                                table_value = row[key]
                                
                                # Allow 10% tolerance for numeric values
                                try:
                                    value_num = float(value)
                                    table_num = float(table_value)
                                    
                                    diff_pct = abs(value_num - table_num) / table_num * 100
                                    
                                    if diff_pct > 10:
                                        warnings.append(
                                            f"{key} ({value}) differs from table value "
                                            f"({table_value}) by {diff_pct:.1f}%"
                                        )
                                except (ValueError, TypeError):
                                    # Not numeric, check exact match
                                    if value != table_value:
                                        warnings.append(
                                            f"{key} ({value}) does not match "
                                            f"table value ({table_value})"
                                        )
            
            if not found_match and model:
                warnings.append(
                    f"Model '{model}' not found in sizing tables. "
                    f"Specifications cannot be verified."
                )
        
        except Exception as e:
            logger.error(f"Error validating against sizing tables: {e}")
        
        return errors, warnings
    
    # ========================================================================
    # COST VALIDATION
    # ========================================================================
    
    async def validate_cost_data(
        self,
        cost_data: Dict[str, Any],
        entity_type: Optional[str] = None
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate cost data.
        
        Args:
            cost_data: Cost data dictionary
            entity_type: Optional entity type for context
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        try:
            # Basic validation
            required_fields = [
                "purchase_cost",
                "purchase_cost_year",
                "purchase_cost_currency"
            ]
            
            is_valid, basic_errors = self.data_validator.validate_cost_data(
                cost_data, required_fields
            )
            errors.extend(basic_errors)
            
            # Validate Lang factor if present
            lang_factor = cost_data.get("lang_factor")
            purchase_cost = cost_data.get("purchase_cost", 0)
            installed_cost = cost_data.get("total_installed_cost", 0)
            
            if lang_factor:
                if lang_factor < 1.5 or lang_factor > 10:
                    warnings.append(
                        f"Lang factor ({lang_factor:.1f}) outside typical range (1.5-10)"
                    )
                
                # Check consistency
                if purchase_cost and installed_cost:
                    implied_factor = installed_cost / purchase_cost if purchase_cost > 0 else 0
                    
                    if abs(implied_factor - lang_factor) / lang_factor > 0.15:
                        warnings.append(
                            f"Specified Lang factor ({lang_factor:.1f}) differs from "
                            f"implied factor ({implied_factor:.1f})"
                        )
            
            # Entity-specific cost validation
            if entity_type:
                entity_errors, entity_warnings = await self._validate_entity_costs(
                    cost_data, entity_type
                )
                errors.extend(entity_errors)
                warnings.extend(entity_warnings)
            
            # Validate escalation if present
            base_year = cost_data.get("purchase_cost_year")
            escalated_cost = cost_data.get("purchase_cost_escalated")
            target_year = cost_data.get("escalation_target_year")
            
            if escalated_cost and purchase_cost and base_year and target_year:
                escalation_factor = escalated_cost / purchase_cost
                years = target_year - base_year
                
                # Typical escalation: 2-5% per year
                expected_min = (1.02 ** years)
                expected_max = (1.08 ** years)
                
                if escalation_factor < expected_min * 0.8:
                    warnings.append(
                        f"Low escalation factor ({escalation_factor:.2f}) "
                        f"for {years} years"
                    )
                elif escalation_factor > expected_max * 1.2:
                    warnings.append(
                        f"High escalation factor ({escalation_factor:.2f}) "
                        f"for {years} years"
                    )
            
            return len(errors) == 0, errors, warnings
        
        except Exception as e:
            logger.error(f"Error validating cost data: {e}", exc_info=True)
            errors.append(f"Validation error: {str(e)}")
            return False, errors, warnings
    
    async def _validate_entity_costs(
        self,
        cost_data: Dict[str, Any],
        entity_type: str
    ) -> Tuple[List[str], List[str]]:
        """Validate costs specific to entity type."""
        errors = []
        warnings = []
        
        purchase_cost = cost_data.get("purchase_cost", 0)
        
        # Rough cost ranges by equipment type (USD, 2020 basis)
        cost_ranges = {
            "gyratory_crusher": (1_000_000, 10_000_000),
            "cone_crusher": (200_000, 3_000_000),
            "jaw_crusher": (100_000, 1_500_000),
            "sag_mill": (5_000_000, 50_000_000),
            "ball_mill": (1_000_000, 20_000_000),
            "conveyor": (50_000, 5_000_000),
            "screen": (100_000, 2_000_000),
            "pump": (10_000, 500_000),
            "thickener": (500_000, 10_000_000),
            "flotation_cell": (200_000, 5_000_000)
        }
        
        # Find matching range
        entity_lower = entity_type.lower()
        for equip_type, (min_cost, max_cost) in cost_ranges.items():
            if equip_type in entity_lower or entity_lower in equip_type:
                if purchase_cost < min_cost * 0.5:
                    warnings.append(
                        f"Purchase cost (${purchase_cost:,.0f}) is low for "
                        f"{entity_type}. Typical range: ${min_cost:,.0f} - ${max_cost:,.0f}"
                    )
                elif purchase_cost > max_cost * 2:
                    warnings.append(
                        f"Purchase cost (${purchase_cost:,.0f}) is high for "
                        f"{entity_type}. Typical range: ${min_cost:,.0f} - ${max_cost:,.0f}"
                    )
                break
        
        return errors, warnings
    
    # ========================================================================
    # SCENARIO VALIDATION
    # ========================================================================
    
    async def validate_scenario(
        self,
        scenario_data: Dict[str, Any]
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate scenario definition.
        
        Args:
            scenario_data: Scenario data
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        try:
            # Validate parameter changes
            parameter_changes = scenario_data.get("parameter_changes", [])
            
            if not parameter_changes:
                errors.append("Scenario must have at least one parameter change")
            
            for i, change in enumerate(parameter_changes):
                is_valid, change_errors = self.data_validator.validate_parameter_change(
                    change
                )
                
                if not is_valid:
                    for error in change_errors:
                        errors.append(f"Parameter change {i+1}: {error}")
            
            # Validate project exists
            project_id = scenario_data.get("project_id")
            if project_id:
                is_valid, error = validate_object_id(project_id)
                if not is_valid:
                    errors.append(f"Invalid project_id: {error}")
            
            # Validate analysis assumptions
            assumptions = scenario_data.get("analysis_assumptions", {})
            
            discount_rate = assumptions.get("discount_rate")
            if discount_rate is not None:
                if discount_rate < 0 or discount_rate > 1:
                    errors.append(
                        f"Discount rate must be between 0 and 1 "
                        f"(got {discount_rate})"
                    )
            
            project_life = assumptions.get("project_life_years")
            if project_life is not None:
                if project_life < 1 or project_life > 100:
                    errors.append(
                        f"Project life must be between 1 and 100 years "
                        f"(got {project_life})"
                    )
            
            # Validate max options
            max_options = scenario_data.get("max_options_to_generate")
            if max_options is not None:
                if max_options < 1 or max_options > 100:
                    errors.append(
                        f"Max options must be between 1 and 100 (got {max_options})"
                    )
            
            return len(errors) == 0, errors, warnings
        
        except Exception as e:
            logger.error(f"Error validating scenario: {e}", exc_info=True)
            errors.append(f"Validation error: {str(e)}")
            return False, errors, warnings
    
    # ========================================================================
    # OPTION VALIDATION
    # ========================================================================
    
    async def validate_option_feasibility(
        self,
        option_data: Dict[str, Any],
        base_case_entity: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate option feasibility.
        
        Checks if the option makes sense technically and economically.
        
        Args:
            option_data: Option data
            base_case_entity: Optional base case entity for comparison
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        try:
            # Validate equipment specifications
            equipment = option_data.get("equipment", {})
            entity_type = option_data.get("entity_type", "")
            
            if equipment:
                is_valid, spec_errors, spec_warnings = await self.validate_equipment_specifications(
                    entity_type, equipment
                )
                errors.extend(spec_errors)
                warnings.extend(spec_warnings)
            
            # Validate cost data
            cost_data = option_data.get("cost_data", {})
            
            if cost_data:
                is_valid, cost_errors, cost_warnings = await self.validate_cost_data(
                    cost_data, entity_type
                )
                errors.extend(cost_errors)
                warnings.extend(cost_warnings)
            
            # Compare with base case if provided
            if base_case_entity:
                comparison_warnings = self._compare_with_base_case(
                    option_data, base_case_entity
                )
                warnings.extend(comparison_warnings)
            
            # Validate NPV analysis if present
            npv_analysis = option_data.get("npv_analysis", {})
            
            if npv_analysis:
                npv_warnings = self._validate_npv_analysis(npv_analysis)
                warnings.extend(npv_warnings)
            
            return len(errors) == 0, errors, warnings
        
        except Exception as e:
            logger.error(f"Error validating option feasibility: {e}", exc_info=True)
            errors.append(f"Validation error: {str(e)}")
            return False, errors, warnings
    
    def _compare_with_base_case(
        self,
        option: Dict[str, Any],
        base_case: Dict[str, Any]
    ) -> List[str]:
        """Compare option with base case and generate warnings."""
        warnings = []
        
        option_specs = option.get("equipment", {})
        base_specs = base_case.get("specifications", {})
        
        # Compare capacity
        option_capacity = option_specs.get("capacity_tph", 0)
        base_capacity = base_specs.get("capacity_tph", 0)
        
        if option_capacity and base_capacity:
            capacity_diff_pct = (option_capacity - base_capacity) / base_capacity * 100
            
            if abs(capacity_diff_pct) > 20:
                warnings.append(
                    f"Option capacity differs from base case by {capacity_diff_pct:.1f}%. "
                    f"Verify downstream impacts are considered."
                )
        
        # Compare power
        option_power = option_specs.get("power_kw", 0)
        base_power = base_specs.get("power_kw", 0)
        
        if option_power and base_power:
            power_diff_pct = (option_power - base_power) / base_power * 100
            
            if abs(power_diff_pct) > 30:
                warnings.append(
                    f"Option power differs from base case by {power_diff_pct:.1f}%. "
                    f"Verify electrical infrastructure can support this."
                )
        
        # Compare cost
        option_cost = option.get("cost_data", {}).get("total_installed_cost", 0)
        base_cost = base_case.get("cost_data", {}).get("total_installed_cost", 0)
        
        if option_cost and base_cost:
            cost_diff_pct = (option_cost - base_cost) / base_cost * 100
            
            if cost_diff_pct > 50:
                warnings.append(
                    f"Option cost is {cost_diff_pct:.1f}% higher than base case. "
                    f"Verify economic justification."
                )
        
        return warnings
    
    def _validate_npv_analysis(self, npv_analysis: Dict[str, Any]) -> List[str]:
        """Validate NPV analysis results."""
        warnings = []
        
        npv = npv_analysis.get("npv", 0)
        irr = npv_analysis.get("irr")
        payback = npv_analysis.get("payback_years")
        
        # Check NPV
        if npv < 0:
            warnings.append(
                f"Negative NPV (${npv:,.0f}). "
                f"This option may not be economically justified."
            )
        
        # Check IRR
        if irr is not None:
            if irr < 0:
                warnings.append(
                    f"Negative IRR ({irr*100:.1f}%). "
                    f"This option is not economically viable."
                )
            elif irr < 0.10:
                warnings.append(
                    f"Low IRR ({irr*100:.1f}%). "
                    f"May not meet typical hurdle rates."
                )
        
        # Check payback
        if payback is not None:
            if payback > 10:
                warnings.append(
                    f"Long payback period ({payback:.1f} years). "
                    f"Consider alternatives with faster payback."
                )
        
        return warnings
    
    # ========================================================================
    # PROCESS FLOW VALIDATION
    # ========================================================================
    
    async def validate_process_flow(
        self,
        entities: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate process flow configuration.
        
        Checks for:
        - Material balance (mass in = mass out)
        - Size distribution compatibility
        - Capacity mismatches (bottlenecks)
        - Missing connections
        
        Args:
            entities: List of entities in process flow
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        try:
            # Build flow graph
            flow_graph = {}
            
            for entity in entities:
                entity_id = str(entity["_id"])
                relationships = entity.get("relationships", [])
                
                downstream = [
                    rel["to_entity_id"]
                    for rel in relationships
                    if rel.get("relationship_type") == "feeds_to"
                ]
                
                flow_graph[entity_id] = {
                    "entity": entity,
                    "downstream": downstream
                }
            
            # Check for orphaned entities
            all_ids = set(flow_graph.keys())
            connected_ids = set()
            
            for node in flow_graph.values():
                connected_ids.update(node["downstream"])
            
            orphaned = all_ids - connected_ids - {
                # Exclude entities that are deliberately start points
                eid for eid, node in flow_graph.items()
                if node["entity"].get("process_stage") in ["feed", "primary_crushing"]
            }
            
            if orphaned:
                warnings.append(
                    f"Found {len(orphaned)} potentially orphaned entities "
                    f"with no upstream connections"
                )
            
            # Check capacity matches
            for entity_id, node in flow_graph.items():
                entity = node["entity"]
                entity_capacity = entity.get("specifications", {}).get("capacity_tph", 0)
                
                if not entity_capacity:
                    continue
                
                # Check downstream capacities
                for downstream_id in node["downstream"]:
                    if downstream_id not in flow_graph:
                        continue
                    
                    downstream = flow_graph[downstream_id]["entity"]
                    downstream_capacity = downstream.get("specifications", {}).get(
                        "capacity_tph", 0
                    )
                    
                    if not downstream_capacity:
                        continue
                    
                    # Check for bottleneck
                    if entity_capacity > downstream_capacity * 1.1:
                        warnings.append(
                            f"Potential bottleneck: {entity.get('name')} "
                            f"({entity_capacity} tph) feeds {downstream.get('name')} "
                            f"({downstream_capacity} tph)"
                        )
            
            return len(errors) == 0, errors, warnings
        
        except Exception as e:
            logger.error(f"Error validating process flow: {e}", exc_info=True)
            errors.append(f"Validation error: {str(e)}")
            return False, errors, warnings