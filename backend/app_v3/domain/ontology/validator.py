"""Ontology validation utilities."""

from typing import Dict, Any, List, Optional, Tuple
from .schemas import OntologySchema, EntityOntology, MSIOOntology


def validate_ontology_structure(ontology_dict: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate ontology structure has required fields.
    
    Args:
        ontology_dict: Dictionary containing ontology definition
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check for entity_ontology
    if "entity_ontology" not in ontology_dict:
        return False, "Missing 'entity_ontology' field"
    
    entity_onto = ontology_dict["entity_ontology"]
    
    # Required fields for entity ontology
    required_fields = ["node_types", "edge_types", "node_properties", "edge_properties"]
    for field in required_fields:
        if field not in entity_onto:
            return False, f"Missing required field '{field}' in entity_ontology"
        
        if not isinstance(entity_onto[field], list):
            return False, f"Field '{field}' must be a list"
    
    # Validate MSIO ontology if present
    if "msio_ontology" in ontology_dict:
        msio_onto = ontology_dict["msio_ontology"]
        required_msio_fields = ["ontology_name", "version", "description", "disciplines"]
        for field in required_msio_fields:
            if field not in msio_onto:
                return False, f"Missing required field '{field}' in msio_ontology"
        
        if not isinstance(msio_onto["disciplines"], list):
            return False, "msio_ontology.disciplines must be a list"
    
    return True, None


def validate_msio_hierarchy(msio_ontology: Dict[str, Any]) -> Tuple[bool, Optional[str], List[str]]:
    """
    Validate MSIO hierarchy consistency.
    
    Args:
        msio_ontology: MSIO ontology dictionary
    
    Returns:
        Tuple of (is_valid, error_message, warnings)
    """
    warnings: List[str] = []
    
    if "disciplines" not in msio_ontology:
        return False, "Missing 'disciplines' field", warnings
    
    disciplines = msio_ontology["disciplines"]
    
    if not isinstance(disciplines, list):
        return False, "disciplines must be a list", warnings
    
    # Check for duplicate discipline names
    discipline_names = [d.get("name") for d in disciplines if isinstance(d, dict) and "name" in d]
    if len(discipline_names) != len(set(discipline_names)):
        return False, "Duplicate discipline names found", warnings
    
    # Validate each discipline structure
    for discipline in disciplines:
        if not isinstance(discipline, dict):
            warnings.append(f"Invalid discipline entry (not a dict): {discipline}")
            continue
        
        if "name" not in discipline:
            warnings.append(f"Discipline missing 'name' field: {discipline}")
            continue
        
        if "categories" not in discipline:
            warnings.append(f"Discipline '{discipline['name']}' missing 'categories'")
            continue
        
        categories = discipline["categories"]
        if not isinstance(categories, list):
            warnings.append(f"Discipline '{discipline['name']}' categories must be a list")
            continue
        
        # Check for duplicate category names within discipline
        category_names = [
            c.get("name") for c in categories
            if isinstance(c, dict) and "name" in c
        ]
        if len(category_names) != len(set(category_names)):
            warnings.append(
                f"Duplicate category names in discipline '{discipline['name']}'"
            )
        
        # Validate category structure
        for category in categories:
            if not isinstance(category, dict):
                continue
            
            if "subcategories" not in category:
                continue
            
            subcategories = category["subcategories"]
            if not isinstance(subcategories, list):
                warnings.append(
                    f"Category '{category.get('name')}' subcategories must be a list"
                )
                continue
            
            # Validate subcategory structure (new format: each entry has "entity" not "entities")
            for subcat in subcategories:
                if not isinstance(subcat, dict):
                    continue
                
                # Check for old format (entities array) - this is now invalid
                if "entities" in subcat:
                    warnings.append(
                        f"Subcategory '{subcat.get('name')}' uses old 'entities' format. "
                        "Should use 'entity' (singular) instead."
                    )
                
                # Check that new format has proper structure
                if "name" not in subcat:
                    warnings.append(
                        f"Subcategory in category '{category.get('name')}' missing 'name' field"
                    )
    
    return True, None, warnings


def validate_node_type(node_type: str, ontology: OntologySchema) -> bool:
    """Check if node type is valid in ontology."""
    return node_type in ontology.entity_ontology.node_types


def validate_edge_type(edge_type: str, ontology: OntologySchema) -> bool:
    """Check if edge type is valid in ontology."""
    return edge_type in ontology.entity_ontology.edge_types


def validate_property(
    property_name: str,
    ontology: OntologySchema,
    is_edge: bool = False
) -> bool:
    """Check if property is valid for nodes or edges."""
    if is_edge:
        return property_name in ontology.entity_ontology.edge_properties
    return property_name in ontology.entity_ontology.node_properties
