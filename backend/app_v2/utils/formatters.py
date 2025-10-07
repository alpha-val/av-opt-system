"""
Response formatting utilities.

Provides functions to format data for API responses and display.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# BASIC FORMATTERS
# ============================================================================

def format_currency(
    amount: Union[int, float, Decimal],
    currency: str = "USD",
    include_symbol: bool = True,
    decimal_places: int = 0
) -> str:
    """
    Format currency amount.
    
    Args:
        amount: Amount to format
        currency: Currency code
        include_symbol: Whether to include currency symbol
        decimal_places: Number of decimal places
        
    Returns:
        Formatted currency string
        
    Examples:
        format_currency(1234567.89) -> "$1,234,568"
        format_currency(1234567.89, decimal_places=2) -> "$1,234,567.89"
        format_currency(1234567.89, include_symbol=False) -> "1,234,568"
    """
    try:
        # Convert to float
        num = float(amount)
        
        # Format with commas and specified decimals
        formatted = f"{num:,.{decimal_places}f}"
        
        if include_symbol:
            # Currency symbols
            symbols = {
                "USD": "$",
                "CAD": "C$",
                "EUR": "€",
                "GBP": "£",
                "AUD": "A$",
                "NZD": "NZ$",
                "ZAR": "R",
                "BRL": "R$",
                "CLP": "CLP$",
                "PEN": "S/",
                "MXN": "MX$"
            }
            
            symbol = symbols.get(currency, currency + " ")
            return f"{symbol}{formatted}"
        
        return formatted
    
    except (ValueError, TypeError) as e:
        logger.warning(f"Error formatting currency: {e}")
        return str(amount)


def format_number(
    value: Union[int, float, Decimal],
    decimal_places: int = 2,
    include_commas: bool = True
) -> str:
    """
    Format number with optional commas and decimals.
    
    Args:
        value: Number to format
        decimal_places: Number of decimal places
        include_commas: Whether to include thousand separators
        
    Returns:
        Formatted number string
        
    Examples:
        format_number(1234.5678) -> "1,234.57"
        format_number(1234.5678, decimal_places=0) -> "1,235"
    """
    try:
        num = float(value)
        
        if include_commas:
            return f"{num:,.{decimal_places}f}"
        else:
            return f"{num:.{decimal_places}f}"
    
    except (ValueError, TypeError) as e:
        logger.warning(f"Error formatting number: {e}")
        return str(value)


def format_percentage(
    value: Union[int, float, Decimal],
    decimal_places: int = 1,
    multiply_by_100: bool = False
) -> str:
    """
    Format percentage.
    
    Args:
        value: Value to format
        decimal_places: Number of decimal places
        multiply_by_100: Whether to multiply by 100 (if value is 0-1 decimal)
        
    Returns:
        Formatted percentage string
        
    Examples:
        format_percentage(0.15, multiply_by_100=True) -> "15.0%"
        format_percentage(15.0) -> "15.0%"
    """
    try:
        num = float(value)
        
        if multiply_by_100:
            num = num * 100
        
        return f"{num:.{decimal_places}f}%"
    
    except (ValueError, TypeError) as e:
        logger.warning(f"Error formatting percentage: {e}")
        return str(value)


def format_date(
    dt: Union[datetime, date, str],
    format_string: str = "%Y-%m-%d"
) -> str:
    """
    Format date/datetime.
    
    Args:
        dt: Date/datetime to format
        format_string: Format string
        
    Returns:
        Formatted date string
        
    Examples:
        format_date(datetime.now()) -> "2025-10-04"
        format_date(datetime.now(), "%B %d, %Y") -> "October 04, 2025"
    """
    try:
        if isinstance(dt, str):
            # Try to parse string
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        
        if isinstance(dt, datetime):
            return dt.strftime(format_string)
        elif isinstance(dt, date):
            return dt.strftime(format_string)
        else:
            return str(dt)
    
    except Exception as e:
        logger.warning(f"Error formatting date: {e}")
        return str(dt)


# ============================================================================
# COMPLEX FORMATTERS
# ============================================================================

def format_cost_breakdown(
    cost_data: Dict[str, Any],
    include_details: bool = True
) -> Dict[str, Any]:
    """
    Format cost breakdown for display.
    
    Args:
        cost_data: Raw cost data
        include_details: Whether to include detailed breakdown
        
    Returns:
        Formatted cost breakdown
    """
    formatted = {
        "purchase_cost": format_currency(
            cost_data.get("purchase_cost_escalated", 0)
        ),
        "installed_cost": format_currency(
            cost_data.get("installed_equipment_cost", 0)
        ),
        "currency": cost_data.get("currency", "USD"),
        "cost_year": cost_data.get("cost_year", "N/A")
    }
    
    if include_details:
        # Format breakdown items
        items = cost_data.get("installed_cost_items", [])
        formatted["breakdown"] = []
        
        for item in items:
            formatted["breakdown"].append({
                "category": item.get("category", "Unknown"),
                "amount": format_currency(item.get("amount", 0)),
                "percentage": format_percentage(
                    item.get("amount", 0) / cost_data.get("installed_equipment_cost", 1) * 100
                ) if cost_data.get("installed_equipment_cost", 0) > 0 else "0%"
            })
        
        # Add totals
        formatted["total_direct"] = format_currency(
            cost_data.get("total_direct_cost", 0)
        )
        formatted["total_indirect"] = format_currency(
            cost_data.get("total_indirect_cost", 0)
        )
    
    return formatted


def format_option_summary(
    option: Dict[str, Any],
    include_costs: bool = True,
    include_equipment: bool = True
) -> Dict[str, Any]:
    """
    Format option for summary display.
    
    Args:
        option: Raw option data
        include_costs: Whether to include cost summary
        include_equipment: Whether to include equipment details
        
    Returns:
        Formatted option summary
    """
    summary = {
        "id": str(option["_id"]),
        "name": option.get("name", "Unknown"),
        "rank": option.get("rank"),
        "selected": option.get("selected", False)
    }
    
    if include_equipment:
        equipment = option.get("equipment", {})
        summary["equipment"] = {
            "manufacturer": equipment.get("manufacturer", "Unknown"),
            "model": equipment.get("model", "Unknown"),
            "capacity": format_number(equipment.get("capacity_tph", 0), decimal_places=0),
            "power": format_number(equipment.get("power_kw", 0), decimal_places=0)
        }
    
    if include_costs:
        summary["costs"] = {
            "purchase": format_currency(option.get("cost_data", {}).get("purchase_cost_escalated", 0)),
            "installed": format_currency(option.get("total_capex", 0)),
            "total_with_downstream": format_currency(option.get("total_capex_with_downstream", 0)),
            "annual_opex": format_currency(option.get("opex", {}).get("total_opex_per_year", 0))
        }
        
        # NPV if available
        npv_data = option.get("npv_analysis", {})
        if npv_data:
            summary["npv"] = {
                "value": format_currency(npv_data.get("npv", 0)),
                "payback_years": format_number(npv_data.get("payback_years", 0), decimal_places=1)
            }
    
    return summary


def format_downstream_impact(
    impact_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Format downstream impact for display.
    
    Args:
        impact_data: Raw impact data
        
    Returns:
        Formatted impact summary
    """
    return {
        "entities_analyzed": impact_data.get("total_entities_analyzed", 0),
        "entities_affected": impact_data.get("entities_affected", 0),
        "total_capex_impact": format_currency(
            impact_data.get("total_capex_delta", 0)
        ),
        "total_opex_impact": format_currency(
            impact_data.get("total_opex_delta_annual", 0)
        ),
        "affected_entities": [
            {
                "name": entity.get("entity_name", "Unknown"),
                "type": entity.get("entity_type", "Unknown"),
                "impact": entity.get("impact_type", "Unknown"),
                "capex_delta": format_currency(entity.get("capex_delta", 0))
            }
            for entity in impact_data.get("affected_entities", [])
        ],
        "confidence": impact_data.get("overall_confidence", "medium"),
        "warnings": impact_data.get("warnings", [])
    }


# ============================================================================
# RESPONSE FORMATTER CLASS
# ============================================================================

class ResponseFormatter:
    """
    Comprehensive response formatter for API responses.
    """
    
    @staticmethod
    def format_success_response(
        data: Any,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format successful API response.
        
        Args:
            data: Response data
            message: Optional success message
            metadata: Optional metadata
            
        Returns:
            Formatted response
        """
        response = {
            "success": True,
            "data": data
        }
        
        if message:
            response["message"] = message
        
        if metadata:
            response["metadata"] = metadata
        
        return response
    
    @staticmethod
    def format_error_response(
        error: str,
        details: Optional[List[str]] = None,
        error_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format error API response.
        
        Args:
            error: Error message
            details: Optional error details
            error_code: Optional error code
            
        Returns:
            Formatted error response
        """
        response = {
            "success": False,
            "error": error
        }
        
        if details:
            response["details"] = details
        
        if error_code:
            response["error_code"] = error_code
        
        return response
    
    @staticmethod
    def format_list_response(
        items: List[Any],
        total: int,
        skip: int = 0,
        limit: int = 20,
        formatter_func: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Format paginated list response.
        
        Args:
            items: List of items
            total: Total count
            skip: Number skipped
            limit: Limit applied
            formatter_func: Optional function to format each item
            
        Returns:
            Formatted list response
        """
        if formatter_func:
            items = [formatter_func(item) for item in items]
        
        return {
            "items": items,
            "pagination": {
                "total": total,
                "skip": skip,
                "limit": limit,
                "returned": len(items),
                "has_more": (skip + len(items)) < total
            }
        }
    
    @staticmethod
    def format_comparison_response(
        items: List[Dict[str, Any]],
        comparison_keys: List[str],
        item_formatter: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Format comparison response for side-by-side display.
        
        Args:
            items: Items to compare
            comparison_keys: Keys to extract for comparison
            item_formatter: Optional function to format items
            
        Returns:
            Formatted comparison
        """
        if item_formatter:
            items = [item_formatter(item) for item in items]
        
        # Build comparison matrix
        comparison = {
            "items_count": len(items),
            "comparison": []
        }
        
        # Extract comparison values for each key
        for key in comparison_keys:
            row = {
                "key": key,
                "values": []
            }
            
            for item in items:
                # Navigate nested keys (e.g., "cost_data.purchase_cost")
                value = item
                for part in key.split("."):
                    value = value.get(part, None) if isinstance(value, dict) else None
                
                row["values"].append(value)
            
            comparison["comparison"].append(row)
        
        comparison["items"] = items
        
        return comparison
    
    @staticmethod
    def format_validation_response(
        is_valid: bool,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Format validation response.
        
        Args:
            is_valid: Whether validation passed
            errors: List of errors
            warnings: List of warnings
            
        Returns:
            Formatted validation response
        """
        response = {
            "valid": is_valid
        }
        
        if errors:
            response["errors"] = errors
            response["error_count"] = len(errors)
        
        if warnings:
            response["warnings"] = warnings
            response["warning_count"] = len(warnings)
        
        return response


# ============================================================================
# SPECIALIZED FORMATTERS
# ============================================================================

def format_scenario_summary(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format scenario for summary display.
    
    Args:
        scenario: Raw scenario data
        
    Returns:
        Formatted scenario summary
    """
    return {
        "id": str(scenario["_id"]),
        "name": scenario.get("name", "Unknown"),
        "description": scenario.get("description", ""),
        "status": scenario.get("status", "unknown"),
        "option_count": scenario.get("option_count", 0),
        "parameter_changes": [
            {
                "parameter": change.get("parameter_name", "Unknown"),
                "from": change.get("original_value"),
                "to": change.get("new_value"),
                "unit": change.get("unit", "")
            }
            for change in scenario.get("parameter_changes", [])
        ],
        "created": format_date(scenario.get("created_at")),
        "updated": format_date(scenario.get("updated_at"))
    }


def format_entity_summary(entity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format entity for summary display.
    
    Args:
        entity: Raw entity data
        
    Returns:
        Formatted entity summary
    """
    specs = entity.get("specifications", {})
    cost = entity.get("cost_data", {})
    
    return {
        "id": str(entity["_id"]),
        "name": entity.get("name", "Unknown"),
        "type": entity.get("entity_type", "Unknown"),
        "tag": entity.get("tag_number", "N/A"),
        "capacity": f"{format_number(specs.get('capacity', 0), 0)} {specs.get('capacity_unit', 'tph')}",
        "power": f"{format_number(specs.get('power_kw', 0), 0)} kW",
        "cost": format_currency(cost.get("total_installed_cost", 0)),
        "status": entity.get("status", "unknown")
    }