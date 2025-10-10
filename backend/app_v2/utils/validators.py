"""
Validation utilities.

Provides reusable validation functions for common data types and patterns.
"""

from typing import Any, Dict, List, Optional, Tuple
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# BASIC VALIDATORS
# ============================================================================

def validate_object_id(value: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate MongoDB ObjectId.
    
    Args:
        value: Value to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if value is None:
        return False, "ObjectId cannot be None"
    
    try:
        if isinstance(value, ObjectId):
            return True, None
        
        # Try to convert string to ObjectId
        ObjectId(str(value))
        return True, None
    
    except (InvalidId, ValueError, TypeError) as e:
        return False, f"Invalid ObjectId format: {str(e)}"


def validate_positive_number(
    value: Any,
    allow_zero: bool = False,
    field_name: str = "value"
) -> Tuple[bool, Optional[str]]:
    """
    Validate that a value is a positive number.
    
    Args:
        value: Value to validate
        allow_zero: Whether to allow zero
        field_name: Name of field for error messages
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        num = float(value)
        
        if allow_zero:
            if num < 0:
                return False, f"{field_name} must be >= 0"
        else:
            if num <= 0:
                return False, f"{field_name} must be > 0"
        
        return True, None
    
    except (ValueError, TypeError):
        return False, f"{field_name} must be a number"


def validate_year(value: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate year value.
    
    Args:
        value: Year to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        year = int(value)
        current_year = datetime.now().year
        
        if year < 1900:
            return False, "Year must be >= 1900"
        
        if year > current_year + 50:
            return False, f"Year must be <= {current_year + 50}"
        
        return True, None
    
    except (ValueError, TypeError):
        return False, "Year must be an integer"


def validate_currency_code(code: str) -> Tuple[bool, Optional[str]]:
    """
    Validate currency code (ISO 4217).
    
    Args:
        code: Currency code (e.g., "USD", "CAD")
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Common currency codes
    valid_codes = {
        "USD", "CAD", "EUR", "GBP", "AUD", "NZD", "ZAR", "BRL",
        "CLP", "PEN", "MXN", "CNY", "JPY", "INR", "RUB"
    }
    
    if not isinstance(code, str):
        return False, "Currency code must be a string"
    
    code_upper = code.upper()
    
    if len(code_upper) != 3:
        return False, "Currency code must be 3 characters"
    
    if code_upper not in valid_codes:
        return False, f"Currency code '{code}' not recognized"
    
    return True, None


def validate_unit(unit: str, allowed_units: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate unit of measurement.
    
    Args:
        unit: Unit string
        allowed_units: Optional list of allowed units
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(unit, str):
        return False, "Unit must be a string"
    
    if not unit.strip():
        return False, "Unit cannot be empty"
    
    if allowed_units:
        if unit not in allowed_units:
            return False, f"Unit must be one of: {', '.join(allowed_units)}"
    
    return True, None


# ============================================================================
# COMPLEX VALIDATORS
# ============================================================================

class DataValidator:
    """
    Comprehensive data validator with domain-specific rules.
    """
    
    # Equipment capacity units
    CAPACITY_UNITS = ["tph", "tpd", "mtpa", "m3/h", "gpm", "l/s"]
    
    # Size units
    SIZE_UNITS = ["inches", "in", "mm", "cm", "m", "ft", "microns", "um"]
    
    # Power units
    POWER_UNITS = ["kW", "MW", "hp"]
    
    @staticmethod
    def validate_equipment_specifications(
        specs: Dict[str, Any],
        entity_type: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate equipment specifications.
        
        Args:
            specs: Specifications dictionary
            entity_type: Type of entity
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check capacity if present
        if "capacity" in specs:
            is_valid, error = validate_positive_number(
                specs["capacity"],
                field_name="capacity"
            )
            if not is_valid:
                errors.append(error)
            
            # Check unit
            if "capacity_unit" in specs:
                is_valid, error = validate_unit(
                    specs["capacity_unit"],
                    DataValidator.CAPACITY_UNITS
                )
                if not is_valid:
                    errors.append(error)
        
        # Check power if present
        if "power_kw" in specs:
            is_valid, error = validate_positive_number(
                specs["power_kw"],
                field_name="power_kw"
            )
            if not is_valid:
                errors.append(error)
        
        # Check physical dimensions
        for dim in ["length_m", "width_m", "height_m", "weight_kg"]:
            if dim in specs:
                is_valid, error = validate_positive_number(
                    specs[dim],
                    field_name=dim
                )
                if not is_valid:
                    errors.append(error)
        
        # Entity-specific validations
        if entity_type == "crusher" or "crusher" in entity_type.lower():
            errors.extend(DataValidator._validate_crusher_specs(specs))
        
        elif entity_type == "mill" or "mill" in entity_type.lower():
            errors.extend(DataValidator._validate_mill_specs(specs))
        
        elif entity_type == "conveyor" or "conveyor" in entity_type.lower():
            errors.extend(DataValidator._validate_conveyor_specs(specs))
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_crusher_specs(specs: Dict[str, Any]) -> List[str]:
        """Validate crusher-specific specifications."""
        errors = []
        
        # Feed opening should be larger than CSS
        if "feed_opening_in" in specs and "closed_side_setting_in" in specs:
            feed = float(specs["feed_opening_in"])
            css = float(specs["closed_side_setting_in"])
            
            if css >= feed:
                errors.append(
                    "Closed side setting must be less than feed opening"
                )
        
        # Check reduction ratio
        if "reduction_ratio" in specs:
            ratio = float(specs["reduction_ratio"])
            if ratio < 1 or ratio > 20:
                errors.append(
                    "Reduction ratio should be between 1 and 20"
                )
        
        return errors
    
    @staticmethod
    def _validate_mill_specs(specs: Dict[str, Any]) -> List[str]:
        """Validate mill-specific specifications."""
        errors = []
        
        # Length should be reasonable relative to diameter
        if "diameter_m" in specs and "length_m" in specs:
            diameter = float(specs["diameter_m"])
            length = float(specs["length_m"])
            
            ratio = length / diameter if diameter > 0 else 0
            
            if ratio < 0.5 or ratio > 5.0:
                errors.append(
                    f"Mill L/D ratio ({ratio:.2f}) is outside typical range (0.5-5.0)"
                )
        
        # Check speed percentage
        if "critical_speed_pct" in specs:
            speed_pct = float(specs["critical_speed_pct"])
            if speed_pct < 50 or speed_pct > 90:
                errors.append(
                    "Critical speed percentage should be between 50% and 90%"
                )
        
        # Check mill filling
        if "mill_filling_pct" in specs:
            filling = float(specs["mill_filling_pct"])
            if filling < 10 or filling > 50:
                errors.append(
                    "Mill filling should be between 10% and 50%"
                )
        
        return errors
    
    @staticmethod
    def _validate_conveyor_specs(specs: Dict[str, Any]) -> List[str]:
        """Validate conveyor-specific specifications."""
        errors = []
        
        # Belt speed should be reasonable
        if "belt_speed_mps" in specs:
            speed = float(specs["belt_speed_mps"])
            if speed < 0.5 or speed > 10.0:
                errors.append(
                    "Belt speed should be between 0.5 and 10.0 m/s"
                )
        
        # Max lump size should be reasonable relative to belt width
        if "belt_width_mm" in specs and "max_lump_size_mm" in specs:
            width = float(specs["belt_width_mm"])
            lump = float(specs["max_lump_size_mm"])
            
            if lump > width / 2:
                errors.append(
                    "Maximum lump size should be less than half belt width"
                )
        
        return errors
    
    @staticmethod
    def validate_cost_data(
        cost_data: Dict[str, Any],
        required_fields: Optional[List[str]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate cost data.
        
        Args:
            cost_data: Cost data dictionary
            required_fields: Optional list of required fields
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        if required_fields:
            for field in required_fields:
                if field not in cost_data:
                    errors.append(f"Required field '{field}' missing")
        
        # Validate purchase cost
        if "purchase_cost" in cost_data:
            is_valid, error = validate_positive_number(
                cost_data["purchase_cost"],
                field_name="purchase_cost"
            )
            if not is_valid:
                errors.append(error)
        
        # Validate cost year
        if "purchase_cost_year" in cost_data:
            is_valid, error = validate_year(cost_data["purchase_cost_year"])
            if not is_valid:
                errors.append(error)
        
        # Validate currency
        if "purchase_cost_currency" in cost_data:
            is_valid, error = validate_currency_code(
                cost_data["purchase_cost_currency"]
            )
            if not is_valid:
                errors.append(error)
        
        # Validate installed cost if present
        if "total_installed_cost" in cost_data:
            purchase = cost_data.get("purchase_cost", 0)
            installed = cost_data.get("total_installed_cost", 0)
            
            if installed > 0 and purchase > 0:
                if installed < purchase:
                    errors.append(
                        "Installed cost should be greater than purchase cost"
                    )
                
                # Check if multiplier is reasonable (typically 2-5x)
                multiplier = installed / purchase
                if multiplier < 1.5 or multiplier > 10:
                    errors.append(
                        f"Cost multiplier ({multiplier:.2f}x) is outside typical range (1.5-10x)"
                    )
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_parameter_change(
        change: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate a parameter change.
        
        Args:
            change: Parameter change dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Required fields
        required = ["parameter_name", "original_value", "new_value"]
        for field in required:
            if field not in change:
                errors.append(f"Required field '{field}' missing")
        
        if errors:
            return False, errors
        
        # Values should be different
        if change["original_value"] == change["new_value"]:
            errors.append("New value must be different from original value")
        
        # If numeric, validate both values
        try:
            orig = float(change["original_value"])
            new = float(change["new_value"])
            
            if orig <= 0 or new <= 0:
                errors.append("Numeric values must be positive")
        except (ValueError, TypeError):
            # Not numeric, that's OK
            pass
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_table_row(
        row_data: Dict[str, Any],
        column_definitions: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a table row against column definitions.
        
        Args:
            row_data: Row data dictionary
            column_definitions: List of column definitions
            
        Returns:
            Tuple of (is_valid, list_of_errors, list_of_warnings)
        """
        errors = []
        warnings = []
        
        # Build column lookup
        columns_by_name = {col["name"]: col for col in column_definitions}
        
        # Check required columns
        for col_def in column_definitions:
            col_name = col_def["name"]
            is_required = col_def.get("is_required", False)
            
            if is_required and col_name not in row_data:
                errors.append(f"Required column '{col_name}' missing")
            
            # Validate value if present
            if col_name in row_data:
                value = row_data[col_name]
                data_type = col_def.get("data_type", "string")
                
                # Type validation
                if data_type == "number" or data_type == "integer":
                    try:
                        num = float(value)
                        
                        # Range validation
                        min_val = col_def.get("min_value")
                        max_val = col_def.get("max_value")
                        
                        if min_val is not None and num < min_val:
                            errors.append(
                                f"Value for '{col_name}' ({num}) is below minimum ({min_val})"
                            )
                        
                        if max_val is not None and num > max_val:
                            errors.append(
                                f"Value for '{col_name}' ({num}) is above maximum ({max_val})"
                            )
                    
                    except (ValueError, TypeError):
                        errors.append(
                            f"Value for '{col_name}' must be a number"
                        )
                
                elif data_type == "string":
                    # Check allowed values if specified
                    allowed = col_def.get("allowed_values")
                    if allowed and value not in allowed:
                        errors.append(
                            f"Value '{value}' not allowed for '{col_name}'. "
                            f"Must be one of: {', '.join(allowed)}"
                        )
        
        # Check for unexpected columns
        for col_name in row_data.keys():
            if col_name not in columns_by_name:
                warnings.append(f"Unexpected column '{col_name}' in row data")
        
        return len(errors) == 0, errors, warnings


# ============================================================================
# SPECIALIZED VALIDATORS
# ============================================================================

def validate_npv_inputs(
    capex: float,
    opex: float,
    discount_rate: float,
    project_life: int
) -> Tuple[bool, List[str]]:
    """
    Validate NPV calculation inputs.
    
    Args:
        capex: Capital expenditure
        opex: Operating expenditure
        discount_rate: Discount rate (as decimal, e.g., 0.10 for 10%)
        project_life: Project life in years
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # CAPEX validation
    is_valid, error = validate_positive_number(capex, allow_zero=True, field_name="CAPEX")
    if not is_valid:
        errors.append(error)
    
    # OPEX validation
    is_valid, error = validate_positive_number(opex, allow_zero=True, field_name="OPEX")
    if not is_valid:
        errors.append(error)
    
    # Discount rate validation
    if discount_rate < 0 or discount_rate > 1:
        errors.append("Discount rate must be between 0 and 1")
    
    if discount_rate > 0.5:
        errors.append("Warning: Discount rate above 50% is unusual")
    
    # Project life validation
    if project_life < 1:
        errors.append("Project life must be at least 1 year")
    
    if project_life > 100:
        errors.append("Project life exceeds 100 years (unusual)")
    
    return len(errors) == 0, errors


def validate_escalation_params(
    base_year: int,
    target_year: int,
    escalation_rate: Optional[float] = None,
    index_values: Optional[Dict[int, float]] = None
) -> Tuple[bool, List[str]]:
    """
    Validate cost escalation parameters.
    
    Args:
        base_year: Base year for cost
        target_year: Target year to escalate to
        escalation_rate: Annual escalation rate (if using compound method)
        index_values: Index values by year (if using index method)
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Year validation
    is_valid, error = validate_year(base_year)
    if not is_valid:
        errors.append(f"Base year: {error}")
    
    is_valid, error = validate_year(target_year)
    if not is_valid:
        errors.append(f"Target year: {error}")
    
    if base_year > target_year:
        errors.append("Base year must be before or equal to target year")
    
    # Escalation method validation
    if escalation_rate is not None:
        if escalation_rate < -0.5 or escalation_rate > 1.0:
            errors.append(
                "Escalation rate should be between -50% and 100%"
            )
    
    elif index_values is not None:
        # Check we have both years
        if base_year not in index_values:
            errors.append(f"Index value missing for base year {base_year}")
        
        if target_year not in index_values:
            errors.append(f"Index value missing for target year {target_year}")
        
        # Validate index values are positive
        for year, value in index_values.items():
            if value <= 0:
                errors.append(f"Index value for year {year} must be positive")
    
    else:
        errors.append(
            "Either escalation_rate or index_values must be provided"
        )
    
    return len(errors) == 0, errors