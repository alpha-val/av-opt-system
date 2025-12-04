"""
Parameter extraction service for scenario resizing.

This module extracts user-editable parameters from decision_levers and maps them
to affected components for the cost estimation workflow.
"""
from typing import List, Dict, Any, Optional, Set
import logging

logger = logging.getLogger(__name__)

# Categories that are typically user-editable (primary parameters)
PRIMARY_CATEGORIES = {
    "capacity",
    "geometry",
    "material",
    "containment",
    "stormwater",
    "civil",
    "instrumentation",
    "electrical",
}

# Categories that are typically derived or less user-friendly
DERIVED_CATEGORIES = {
    "cost_model",
    "schedule",
}

# Mapping from parameter names/patterns to affected component roles
PARAMETER_TO_COMPONENT_MAP = {
    "tank.*capacity": ["Water storage tank", "Storage tank"],
    "tank.*volume": ["Water storage tank", "Storage tank"],
    "tank.*nominal": ["Water storage tank", "Storage tank"],
    "containment.*factor": ["Secondary containment system", "Secondary containment basin", "Containment basin"],
    "containment.*capacity": ["Secondary containment system", "Secondary containment basin", "Containment basin"],
    "stormwater.*capture": ["Stormwater detention system", "Stormwater detention/infiltration system"],
    "stormwater.*depth": ["Stormwater detention system", "Stormwater detention/infiltration system"],
    "platform.*elevation": ["Support platform", "Access platform and stairs", "Platform & structural steel"],
    "foundation.*pedestal": ["Pedestal foundation pad", "Foundations & pedestals"],
    "instrumentation.*scope": ["Instrumentation package", "PLC panel with HMI"],
    "electrical.*service": ["Local control panel and transformer"],
    "transformer.*size": ["Local control panel and transformer"],
    "heat.*trace": ["Heat tracing system"],
    "sump.*pump": ["Sump pump (optional)"],
    "number.*tank": ["Water storage tank", "Storage tank"],  # Affects all tank-related components
}


def extract_editable_parameters(
    decision_levers: List[Dict[str, Any]],
    components_for_tabular_lookup: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Extract user-editable parameters from decision_levers and map them to affected components.
    
    Args:
        decision_levers: List of decision lever objects from scenario analysis
        components_for_tabular_lookup: List of component objects that will be costed
        
    Returns:
        List of parameter objects with metadata for form rendering
    """
    editable_params = []
    component_roles = {comp.get("role") for comp in components_for_tabular_lookup}
    
    for lever in decision_levers:
        category = lever.get("category", "").lower()
        name = lever.get("name", "")
        
        # Skip derived categories (cost_model, schedule) unless explicitly needed
        if category in DERIVED_CATEGORIES:
            # Only include contingency as it's commonly adjusted
            if "contingency" in name.lower():
                pass  # Include it
            else:
                continue
        
        # Determine if this lever affects components we care about
        affected_components = _find_affected_components(name, component_roles)
        
        # Skip if no relevant components affected (unless it's a primary category)
        if not affected_components and category not in PRIMARY_CATEGORIES:
            continue
        
        # Build parameter object
        param = {
            "parameter_id": _generate_parameter_id(name),
            "name": name,
            "display_name": name,
            "category": category,
            "description": lever.get("description", ""),
            "baseline_value": lever.get("baseline_value"),
            "baseline_unit": lever.get("baseline_unit"),
            "baseline_text": lever.get("baseline_text", ""),
            "type": _determine_parameter_type(lever),
            "is_discrete": lever.get("is_discrete", False),
            "options": lever.get("options", []),
            "plausible_range": lever.get("plausible_range"),
            "change_relevance": lever.get("change_relevance_to_objective", ""),
            "dependencies": lever.get("dependencies", []),
            "affected_components": affected_components,
            "priority": _calculate_priority(category, name, affected_components),
        }
        
        editable_params.append(param)
    
    # Sort by priority (highest first) and then by category
    editable_params.sort(key=lambda p: (-p["priority"], p["category"], p["name"]))
    
    return editable_params


def _generate_parameter_id(name: str) -> str:
    """Generate a URL-friendly parameter ID from name."""
    import re
    # Convert to lowercase, replace spaces/special chars with underscores
    param_id = re.sub(r'[^a-z0-9]+', '_', name.lower())
    # Remove leading/trailing underscores
    param_id = param_id.strip('_')
    return param_id


def _determine_parameter_type(lever: Dict[str, Any]) -> str:
    """Determine the UI input type for a parameter."""
    is_discrete = lever.get("is_discrete", False)
    options = lever.get("options", [])
    baseline_value = lever.get("baseline_value")
    
    if is_discrete and options:
        if len(options) <= 3:
            return "radio"  # Small set of options
        else:
            return "select"  # Larger dropdown
    elif isinstance(baseline_value, bool):
        return "checkbox"
    elif isinstance(baseline_value, (int, float)):
        return "number"
    elif isinstance(baseline_value, str):
        return "text"
    else:
        return "text"


def _find_affected_components(parameter_name: str, component_roles: Set[str]) -> List[str]:
    """Find which components are affected by a parameter change."""
    affected = []
    param_lower = parameter_name.lower()
    
    # Check direct matches
    for pattern, component_patterns in PARAMETER_TO_COMPONENT_MAP.items():
        import re
        if re.search(pattern.replace(".*", ".*"), param_lower, re.IGNORECASE):
            for comp_role in component_roles:
                for pattern_comp in component_patterns:
                    if pattern_comp.lower() in comp_role.lower():
                        if comp_role not in affected:
                            affected.append(comp_role)
    
    # Also check if parameter name contains component keywords
    component_keywords = {
        "tank": ["tank", "storage"],
        "containment": ["containment"],
        "stormwater": ["stormwater"],
        "platform": ["platform", "access"],
        "foundation": ["foundation", "pedestal"],
        "instrumentation": ["instrumentation", "plc", "hmi"],
        "electrical": ["electrical", "transformer", "panel"],
        "heat": ["heat", "trace"],
        "pump": ["pump", "sump"],
    }
    
    for keyword, comp_patterns in component_keywords.items():
        if keyword in param_lower:
            for comp_role in component_roles:
                for pattern_comp in comp_patterns:
                    if pattern_comp.lower() in comp_role.lower():
                        if comp_role not in affected:
                            affected.append(comp_role)
    
    return affected


def _calculate_priority(category: str, name: str, affected_components: List[str]) -> int:
    """
    Calculate priority for parameter display (higher = more important).
    
    Priority factors:
    - Capacity/geometry parameters: 10
    - Material/containment: 8
    - Civil/stormwater: 6
    - Instrumentation/electrical: 4
    - Others: 2
    - If affects multiple components: +2
    """
    priority_map = {
        "capacity": 10,
        "geometry": 10,
        "material": 8,
        "containment": 8,
        "stormwater": 6,
        "civil": 6,
        "instrumentation": 4,
        "electrical": 4,
    }
    
    base_priority = priority_map.get(category, 2)
    
    # Boost if affects multiple components
    if len(affected_components) > 1:
        base_priority += 2
    
    # Boost if it's a primary capacity parameter
    if "capacity" in name.lower() or "volume" in name.lower():
        base_priority += 2
    
    return base_priority


def group_parameters_by_category(parameters: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group parameters by category for organized form display."""
    grouped = {}
    for param in parameters:
        category = param.get("category", "other")
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(param)
    return grouped


def get_parameter_summary(parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get a summary of parameters for quick overview."""
    return {
        "total_parameters": len(parameters),
        "by_category": {
            cat: len(params)
            for cat, params in group_parameters_by_category(parameters).items()
        },
        "primary_parameters": [
            p["parameter_id"]
            for p in parameters
            if p.get("priority", 0) >= 8
        ],
    }

