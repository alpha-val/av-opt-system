"""Ontology loading and access utilities."""

from typing import Dict, Any, Optional, List
import os
from pathlib import Path

from .schemas import OntologySchema
from .ontology import get_default_ontology, ENTITY_ONTOLOGY, AV_MSIO_ONTOLOGY
from .validator import (
    validate_ontology_structure,
    validate_msio_hierarchy,
    validate_node_type,
    validate_edge_type,
    validate_property,
)

# Global ontology instance cache
_ontology_instance: Optional[OntologySchema] = None
_ontology_source: Optional[str] = None


def load_ontology_from_file(file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load ontology from a Python file.
    
    Attempts to load from:
    1. Custom file_path if provided
    2. domain/ontology/ontology.py (user-defined)
    3. Falls back to default ontology
    
    Args:
        file_path: Optional path to ontology file. If None, looks for
                   ontology.py in the same directory as this module.
    
    Returns:
        Dictionary containing ontology definition
    """
    # Try to load from user-defined ontology.py
    if file_path is None:
        # Look for ontology.py in the same directory
        current_dir = Path(__file__).parent
        file_path = current_dir / "ontology.py"
    
    # If custom file_path provided, use it
    ontology_file = Path(file_path)
    
    if ontology_file.exists() and ontology_file.suffix == ".py":
        try:
            # Import the ontology module
            import importlib.util
            spec = importlib.util.spec_from_file_location("user_ontology", ontology_file)
            if spec and spec.loader:
                user_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(user_module)
                
                # Check for ONTOLOGY or ENTITY_ONTOLOGY in module
                if hasattr(user_module, "ONTOLOGY"):
                    user_ontology = user_module.ONTOLOGY
                    if isinstance(user_ontology, dict):
                        return _merge_ontology(user_ontology)
                
                # Also check for separate definitions
                user_entity = getattr(user_module, "ENTITY_ONTOLOGY", None)
                user_msio = getattr(user_module, "AV_MSIO_ONTOLOGY", None)
                
                if user_entity or user_msio:
                    merged = get_default_ontology().copy()
                    if user_entity:
                        merged["entity_ontology"] = user_entity
                    if user_msio:
                        merged["msio_ontology"] = user_msio
                    return merged
        
        except Exception as e:
            # If loading fails, fall back to default
            print(f"Warning: Failed to load ontology from {file_path}: {e}")
            print("Falling back to default ontology.")
    
    # Fall back to default
    return get_default_ontology()


def _merge_ontology(user_ontology: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge user ontology with default ontology.
    
    User ontology values override defaults.
    
    Args:
        user_ontology: User-provided ontology dictionary
    
    Returns:
        Merged ontology dictionary
    """
    default = get_default_ontology()
    merged = default.copy()
    
    # Deep merge entity_ontology
    if "entity_ontology" in user_ontology:
        user_entity = user_ontology["entity_ontology"]
        default_entity = merged["entity_ontology"]
        
        # Merge lists (extend, not replace)
        for key in ["node_types", "edge_types", "node_properties", "edge_properties"]:
            if key in user_entity:
                if isinstance(user_entity[key], list):
                    # Combine and deduplicate
                    combined = list(set(default_entity.get(key, []) + user_entity[key]))
                    merged["entity_ontology"][key] = combined
        
        # Merge dictionaries (user overrides default)
        for key in ["node_descriptions", "edge_descriptions", "node_prop_examples", "edge_prop_examples"]:
            if key in user_entity:
                if isinstance(user_entity[key], dict):
                    merged["entity_ontology"][key] = {
                        **default_entity.get(key, {}),
                        **user_entity[key]
                    }
    
    # Replace MSIO ontology if provided (no merge for hierarchical structure)
    if "msio_ontology" in user_ontology:
        merged["msio_ontology"] = user_ontology["msio_ontology"]
    
    return merged


def load_ontology(ontology_config: Optional[Dict[str, Any]] = None, file_path: Optional[str] = None) -> OntologySchema:
    """
    Load an ontology from configuration dictionary or file.
    
    Args:
        ontology_config: Optional custom ontology configuration dictionary.
                        If None, attempts to load from file.
        file_path: Optional path to ontology file. If None, looks for
                   ontology.py in the domain/ontology directory.
    
    Returns:
        OntologySchema instance
    
    Raises:
        ValueError: If ontology structure is invalid
    """
    global _ontology_instance, _ontology_source
    
    if ontology_config is None:
        ontology_config = load_ontology_from_file(file_path)
        source = "file" if file_path else "default"
    else:
        source = "config"
    
    # Validate structure
    is_valid, error = validate_ontology_structure(ontology_config)
    if not is_valid:
        raise ValueError(f"Invalid ontology structure: {error}")
    
    # Validate MSIO hierarchy if present
    if "msio_ontology" in ontology_config:
        is_valid, error, warnings = validate_msio_hierarchy(ontology_config["msio_ontology"])
        if not is_valid:
            raise ValueError(f"Invalid MSIO ontology: {error}")
        if warnings:
            print(f"MSIO ontology warnings: {warnings}")
    
    # Create schema instance
    _ontology_instance = OntologySchema(**ontology_config)
    _ontology_source = source
    
    return _ontology_instance


def get_ontology() -> OntologySchema:
    """
    Get the current ontology instance.
    Loads default ontology if not already loaded.
    
    Returns:
        OntologySchema instance
    """
    global _ontology_instance
    
    if _ontology_instance is None:
        _ontology_instance = load_ontology()
    
    return _ontology_instance


def reload_ontology(file_path: Optional[str] = None) -> OntologySchema:
    """
    Reload ontology from file or default.
    
    Useful for development when ontology changes.
    
    Args:
        file_path: Optional path to ontology file
    
    Returns:
        OntologySchema instance
    """
    global _ontology_instance, _ontology_source
    
    _ontology_instance = None
    _ontology_source = None
    
    return load_ontology(file_path=file_path)


def is_valid_node_type(node_type: str) -> bool:
    """Check if a node type is valid in the ontology."""
    ontology = get_ontology()
    return validate_node_type(node_type, ontology)


def is_valid_edge_type(edge_type: str) -> bool:
    """Check if an edge type is valid in the ontology."""
    ontology = get_ontology()
    return validate_edge_type(edge_type, ontology)


def is_valid_node_property(property_name: str) -> bool:
    """Check if a property name is valid for nodes."""
    ontology = get_ontology()
    return validate_property(property_name, ontology, is_edge=False)


def is_valid_edge_property(property_name: str) -> bool:
    """Check if a property name is valid for edges."""
    ontology = get_ontology()
    return validate_property(property_name, ontology, is_edge=True)


def get_node_description(node_type: str) -> Optional[str]:
    """Get description for a node type."""
    ontology = get_ontology()
    return ontology.entity_ontology.node_descriptions.get(node_type)


def get_edge_description(edge_type: str) -> Optional[str]:
    """Get description for an edge type."""
    ontology = get_ontology()
    return ontology.entity_ontology.edge_descriptions.get(edge_type)


def get_msio_hierarchy(
    discipline: str,
    category: Optional[str] = None,
    subcategory: Optional[str] = None
) -> Optional[List[str]]:
    """
    Get MSIO hierarchy path.
    
    Args:
        discipline: Discipline name
        category: Optional category name
        subcategory: Optional subcategory name
    
    Returns:
        List representing the hierarchy path, or None if not found
    """
    ontology = get_ontology()
    return ontology.get_msio_path(discipline, category, subcategory)


def get_all_disciplines() -> List[str]:
    """Get list of all discipline names from MSIO ontology."""
    ontology = get_ontology()
    if not ontology.msio_ontology:
        return []
    
    return [d.name for d in ontology.msio_ontology.disciplines]


def get_categories_for_discipline(discipline: str) -> List[str]:
    """Get list of category names for a given discipline."""
    ontology = get_ontology()
    if not ontology.msio_ontology:
        return []
    
    discipline_obj = next(
        (d for d in ontology.msio_ontology.disciplines if d.name == discipline),
        None
    )
    
    if not discipline_obj:
        return []
    
    return [c.name for c in discipline_obj.categories]


def get_subcategories_for_category(discipline: str, category: str) -> List[str]:
    """Get list of subcategory names for a given discipline and category."""
    ontology = get_ontology()
    if not ontology.msio_ontology:
        return []
    
    discipline_obj = next(
        (d for d in ontology.msio_ontology.disciplines if d.name == discipline),
        None
    )
    
    if not discipline_obj:
        return []
    
    category_obj = next(
        (c for c in discipline_obj.categories if c.name == category),
        None
    )
    
    if not category_obj:
        return []
    
    return [s.name for s in category_obj.subcategories]


def get_entities_for_subcategory(
    discipline: str,
    category: str,
    subcategory: str
) -> List[str]:
    """Get list of entity names for a given discipline, category, and subcategory."""
    ontology = get_ontology()
    if not ontology.msio_ontology:
        return []
    
    discipline_obj = next(
        (d for d in ontology.msio_ontology.disciplines if d.name == discipline),
        None
    )
    
    if not discipline_obj:
        return []
    
    category_obj = next(
        (c for c in discipline_obj.categories if c.name == category),
        None
    )
    
    if not category_obj:
        return []
    
    # Collect all subcategories with matching name (new structure allows multiple entries)
    matching_subcategories = [
        s for s in category_obj.subcategories if s.name == subcategory
    ]
    
    if not matching_subcategories:
        return []
    
    # Extract entity values from all matching subcategories, filtering out None values
    entities = [
        s.entity for s in matching_subcategories 
        if s.entity is not None
    ]
    
    return entities
