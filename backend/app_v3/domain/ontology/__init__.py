"""Ontology module for document parsing and entity extraction."""

from .schemas import (
    OntologySchema,
    EntityOntology,
    MSIOOntology,
    NodeType,
    EdgeType,
    PropertyDefinition,
    Discipline,
    Category,
    Subcategory,
)
from .loader import (
    load_ontology,
    get_ontology,
    reload_ontology,
    load_ontology_from_file,
    is_valid_node_type,
    is_valid_edge_type,
    is_valid_node_property,
    is_valid_edge_property,
    get_node_description,
    get_edge_description,
    get_msio_hierarchy,
    get_all_disciplines,
    get_categories_for_discipline,
    get_subcategories_for_category,
    get_entities_for_subcategory,
)
from .validator import (
    validate_ontology_structure,
    validate_msio_hierarchy,
    validate_node_type,
    validate_edge_type,
    validate_property,
)

__all__ = [
    # Schemas
    "OntologySchema",
    "EntityOntology",
    "MSIOOntology",
    "NodeType",
    "EdgeType",
    "PropertyDefinition",
    "Discipline",
    "Category",
    "Subcategory",
    # Loader functions
    "load_ontology",
    "get_ontology",
    "reload_ontology",
    "load_ontology_from_file",
    "is_valid_node_type",
    "is_valid_edge_type",
    "is_valid_node_property",
    "is_valid_edge_property",
    "get_node_description",
    "get_edge_description",
    "get_msio_hierarchy",
    "get_all_disciplines",
    "get_categories_for_discipline",
    "get_subcategories_for_category",
    "get_entities_for_subcategory",
    # Validator functions
    "validate_ontology_structure",
    "validate_msio_hierarchy",
    "validate_node_type",
    "validate_edge_type",
    "validate_property",
]
