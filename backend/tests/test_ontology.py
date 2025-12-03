"""Tests for ontology module."""

import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any, List

from app_v3.domain.ontology import (
    # Schemas
    OntologySchema,
    EntityOntology,
    MSIOOntology,
    # Loader functions
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
    # Validator functions
    validate_ontology_structure,
    validate_msio_hierarchy,
    validate_node_type,
    validate_edge_type,
    validate_property,
)
from app_v3.domain.ontology.ontology import get_default_ontology, ENTITY_ONTOLOGY, AV_MSIO_ONTOLOGY


class TestOntologySchemas:
    """Test ontology schema models."""
    
    def test_entity_ontology_schema(self):
        """Test EntityOntology schema creation."""
        entity_onto = EntityOntology(
            schema_version="0.1.0",
            node_types=["Equipment", "Material"],
            edge_types=["HAS_EQUIPMENT", "USES_EQUIPMENT"],
            node_properties=["name", "capacity"],
            edge_properties=["confidence", "source_doc"],
        )
        assert entity_onto.schema_version == "0.1.0"
        assert len(entity_onto.node_types) == 2
        assert "Equipment" in entity_onto.node_types
        assert len(entity_onto.edge_types) == 2
    
    def test_msio_ontology_schema(self):
        """Test MSIOOntology schema creation."""
        msio_onto = MSIOOntology(
            ontology_name="TEST-ONTOLOGY",
            version="0.1",
            description="Test ontology",
            disciplines=[],
        )
        assert msio_onto.ontology_name == "TEST-ONTOLOGY"
        assert msio_onto.version == "0.1"
        assert len(msio_onto.disciplines) == 0
    
    def test_ontology_schema_creation(self):
        """Test OntologySchema creation."""
        entity_onto = EntityOntology(
            schema_version="0.1.0",
            node_types=["Equipment"],
            edge_types=["HAS_EQUIPMENT"],
            node_properties=["name"],
            edge_properties=["confidence"],
        )
        
        schema = OntologySchema(entity_ontology=entity_onto)
        assert schema.entity_ontology is not None
        assert schema.msio_ontology is None
    
    def test_ontology_schema_get_node_type(self):
        """Test get_node_type method."""
        entity_onto = EntityOntology(
            schema_version="0.1.0",
            node_types=["Equipment", "Material"],
            edge_types=[],
            node_properties=[],
            edge_properties=[],
        )
        schema = OntologySchema(entity_ontology=entity_onto)
        
        assert schema.get_node_type("Equipment") == "Equipment"
        assert schema.get_node_type("Invalid") is None
    
    def test_ontology_schema_get_edge_type(self):
        """Test get_edge_type method."""
        entity_onto = EntityOntology(
            schema_version="0.1.0",
            node_types=[],
            edge_types=["HAS_EQUIPMENT", "USES_EQUIPMENT"],
            node_properties=[],
            edge_properties=[],
        )
        schema = OntologySchema(entity_ontology=entity_onto)
        
        assert schema.get_edge_type("HAS_EQUIPMENT") == "HAS_EQUIPMENT"
        assert schema.get_edge_type("Invalid") is None
    
    def test_ontology_schema_is_valid_property(self):
        """Test is_valid_property method."""
        entity_onto = EntityOntology(
            schema_version="0.1.0",
            node_types=[],
            edge_types=[],
            node_properties=["name", "capacity"],
            edge_properties=["confidence"],
        )
        schema = OntologySchema(entity_ontology=entity_onto)
        
        assert schema.is_valid_property("name", is_edge=False) is True
        assert schema.is_valid_property("confidence", is_edge=True) is True
        assert schema.is_valid_property("invalid", is_edge=False) is False


class TestOntologyLoader:
    """Test ontology loading functions."""
    
    def test_get_default_ontology(self):
        """Test getting default ontology."""
        default = get_default_ontology()
        assert "entity_ontology" in default
        assert "msio_ontology" in default
        assert isinstance(default["entity_ontology"], dict)
        assert isinstance(default["msio_ontology"], dict)
    
    def test_load_ontology_default(self):
        """Test loading default ontology."""
        ontology = load_ontology()
        assert isinstance(ontology, OntologySchema)
        assert ontology.entity_ontology is not None
        assert ontology.msio_ontology is not None
        assert len(ontology.entity_ontology.node_types) > 0
        assert len(ontology.entity_ontology.edge_types) > 0
    
    def test_get_ontology_singleton(self):
        """Test get_ontology returns singleton."""
        ontology1 = get_ontology()
        ontology2 = get_ontology()
        assert ontology1 is ontology2
    
    def test_reload_ontology(self):
        """Test reloading ontology."""
        ontology1 = get_ontology()
        ontology2 = reload_ontology()
        # After reload, should be new instance
        assert ontology2 is not None
    
    def test_load_ontology_from_file_nonexistent(self):
        """Test loading from nonexistent file falls back to default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_file = Path(tmpdir) / "nonexistent.py"
            result = load_ontology_from_file(str(nonexistent_file))
            # Should fall back to default
            assert "entity_ontology" in result
            assert "msio_ontology" in result
    
    def test_load_ontology_from_custom_file(self):
        """Test loading from custom ontology file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a custom ontology file
            custom_file = Path(tmpdir) / "custom_ontology.py"
            custom_file.write_text('''
ENTITY_ONTOLOGY = {
    "schema_version": "0.2.0",
    "node_types": ["CustomNode"],
    "edge_types": ["CUSTOM_EDGE"],
    "node_properties": ["custom_prop"],
    "edge_properties": [],
}
''')
            result = load_ontology_from_file(str(custom_file))
            assert "entity_ontology" in result
            # Should merge with default
            assert isinstance(result["entity_ontology"], dict)
    
    def test_load_ontology_with_ontology_dict(self):
        """Test loading ontology with ONTOLOGY dict in custom file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_file = Path(tmpdir) / "custom_ontology.py"
            custom_file.write_text('''
ONTOLOGY = {
    "entity_ontology": {
        "schema_version": "0.2.0",
        "node_types": ["CustomNode"],
        "edge_types": ["CUSTOM_EDGE"],
        "node_properties": ["custom_prop"],
        "edge_properties": [],
    },
    "msio_ontology": None
}
''')
            result = load_ontology_from_file(str(custom_file))
            assert "entity_ontology" in result
    
    def test_load_ontology_invalid_structure_raises(self):
        """Test that invalid ontology structure raises ValueError."""
        invalid_config = {
            "entity_ontology": {
                # Missing required fields
                "node_types": ["Equipment"],
            }
        }
        with pytest.raises(ValueError):
            load_ontology(ontology_config=invalid_config)


class TestOntologyValidation:
    """Test ontology validation functions."""
    
    def test_validate_ontology_structure_valid(self):
        """Test validating valid ontology structure."""
        valid_config = {
            "entity_ontology": {
                "schema_version": "0.1.0",
                "node_types": ["Equipment"],
                "edge_types": ["HAS_EQUIPMENT"],
                "node_properties": ["name"],
                "edge_properties": ["confidence"],
            }
        }
        is_valid, error = validate_ontology_structure(valid_config)
        assert is_valid is True
        assert error is None
    
    def test_validate_ontology_structure_missing_entity(self):
        """Test validating structure with missing entity_ontology."""
        invalid_config = {}
        is_valid, error = validate_ontology_structure(invalid_config)
        assert is_valid is False
        assert "entity_ontology" in error.lower()
    
    def test_validate_ontology_structure_missing_field(self):
        """Test validating structure with missing required field."""
        invalid_config = {
            "entity_ontology": {
                "node_types": ["Equipment"],
                # Missing edge_types, node_properties, edge_properties
            }
        }
        is_valid, error = validate_ontology_structure(invalid_config)
        assert is_valid is False
        assert error is not None
    
    def test_validate_msio_hierarchy_valid(self):
        """Test validating valid MSIO hierarchy."""
        valid_msio = {
            "ontology_name": "TEST",
            "version": "0.1",
            "description": "Test",
            "disciplines": [
                {
                    "name": "Mechanical",
                    "categories": [
                        {
                            "name": "Pumps",
                            "subcategories": [
                                {
                                    "name": "Centrifugal",
                                    "entities": ["Pump1"]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        is_valid, error, warnings = validate_msio_hierarchy(valid_msio)
        assert is_valid is True
        assert error is None
    
    def test_validate_msio_hierarchy_missing_disciplines(self):
        """Test validating MSIO with missing disciplines."""
        invalid_msio = {
            "ontology_name": "TEST",
            "version": "0.1",
            "description": "Test",
        }
        is_valid, error, warnings = validate_msio_hierarchy(invalid_msio)
        assert is_valid is False
        assert error is not None
    
    def test_validate_node_type(self):
        """Test validate_node_type function."""
        ontology = get_ontology()
        
        # Test valid node type
        assert validate_node_type("Equipment", ontology) is True
        
        # Test invalid node type
        assert validate_node_type("InvalidNodeType", ontology) is False
    
    def test_validate_edge_type(self):
        """Test validate_edge_type function."""
        ontology = get_ontology()
        
        # Test valid edge type
        assert validate_edge_type("HAS_EQUIPMENT", ontology) is True
        
        # Test invalid edge type
        assert validate_edge_type("INVALID_EDGE", ontology) is False
    
    def test_validate_property(self):
        """Test validate_property function."""
        ontology = get_ontology()
        
        # Test valid node property
        assert validate_property("name", ontology, is_edge=False) is True
        
        # Test valid edge property
        assert validate_property("confidence", ontology, is_edge=True) is True
        
        # Test invalid property
        assert validate_property("invalid_prop", ontology, is_edge=False) is False


class TestOntologyHelpers:
    """Test ontology helper functions."""
    
    def test_is_valid_node_type(self):
        """Test is_valid_node_type helper."""
        assert is_valid_node_type("Equipment") is True
        assert is_valid_node_type("Material") is True
        assert is_valid_node_type("InvalidNode") is False
    
    def test_is_valid_edge_type(self):
        """Test is_valid_edge_type helper."""
        assert is_valid_edge_type("HAS_EQUIPMENT") is True
        assert is_valid_edge_type("USES_EQUIPMENT") is True
        assert is_valid_edge_type("INVALID_EDGE") is False
    
    def test_is_valid_node_property(self):
        """Test is_valid_node_property helper."""
        assert is_valid_node_property("name") is True
        assert is_valid_node_property("capacity") is True
        assert is_valid_node_property("invalid_prop") is False
    
    def test_is_valid_edge_property(self):
        """Test is_valid_edge_property helper."""
        assert is_valid_edge_property("confidence") is True
        assert is_valid_edge_property("source_doc") is True
        assert is_valid_edge_property("invalid_prop") is False
    
    def test_get_node_description(self):
        """Test get_node_description helper."""
        desc = get_node_description("Equipment")
        assert desc is not None
        assert isinstance(desc, str)
        assert len(desc) > 0
        
        # Test nonexistent node type
        desc = get_node_description("NonExistentNode")
        assert desc is None
    
    def test_get_edge_description(self):
        """Test get_edge_description helper."""
        desc = get_edge_description("HAS_EQUIPMENT")
        assert desc is not None
        assert isinstance(desc, str)
        
        # Test nonexistent edge type
        desc = get_edge_description("NON_EXISTENT")
        assert desc is None


class TestMSIOHierarchy:
    """Test MSIO hierarchy functions."""
    
    def test_get_all_disciplines(self):
        """Test getting all disciplines."""
        disciplines = get_all_disciplines()
        assert isinstance(disciplines, list)
        assert len(disciplines) > 0
        assert "Mechanical Equipment" in disciplines
    
    def test_get_categories_for_discipline(self):
        """Test getting categories for a discipline."""
        categories = get_categories_for_discipline("Mechanical Equipment")
        assert isinstance(categories, list)
        assert len(categories) > 0
        assert "Pumps" in categories
        
        # Test nonexistent discipline
        categories = get_categories_for_discipline("NonExistent")
        assert categories == []
    
    def test_get_subcategories_for_category(self):
        """Test getting subcategories for a category."""
        subcategories = get_subcategories_for_category("Mechanical Equipment", "Pumps")
        assert isinstance(subcategories, list)
        assert len(subcategories) > 0
        assert "Centrifugal" in subcategories
        
        # Test nonexistent category
        subcategories = get_subcategories_for_category("Mechanical Equipment", "NonExistent")
        assert subcategories == []
        
        # Test nonexistent discipline
        subcategories = get_subcategories_for_category("NonExistent", "Pumps")
        assert subcategories == []
    
    def test_get_entities_for_subcategory(self):
        """Test getting entities for a subcategory."""
        entities = get_entities_for_subcategory(
            "Mechanical Equipment", "Pumps", "Centrifugal"
        )
        assert isinstance(entities, list)
        assert "Base pump unit" in entities
        
        # Test nonexistent subcategory
        entities = get_entities_for_subcategory(
            "Mechanical Equipment", "Pumps", "NonExistent"
        )
        assert entities == []
    
    def test_get_msio_hierarchy(self):
        """Test getting MSIO hierarchy path."""
        path = get_msio_hierarchy("Mechanical Equipment")
        assert isinstance(path, list)
        assert len(path) >= 1
        assert "Mechanical Equipment" in path
        
        # Test with category
        path = get_msio_hierarchy("Mechanical Equipment", "Pumps")
        assert isinstance(path, list)
        assert len(path) >= 2
        assert "Mechanical Equipment" in path
        assert "Pumps" in path
        
        # Test with subcategory
        path = get_msio_hierarchy("Mechanical Equipment", "Pumps", "Centrifugal")
        assert isinstance(path, list)
        assert len(path) >= 3
        assert "Centrifugal" in path
        
        # Test nonexistent discipline
        path = get_msio_hierarchy("NonExistent")
        assert path is None


class TestDefaultOntology:
    """Test default ontology content."""
    
    def test_default_entity_ontology_has_content(self):
        """Test that default entity ontology has expected content."""
        default = get_default_ontology()
        entity_onto = default["entity_ontology"]
        
        assert "node_types" in entity_onto
        assert "edge_types" in entity_onto
        assert "node_properties" in entity_onto
        assert "edge_properties" in entity_onto
        
        assert len(entity_onto["node_types"]) > 0
        assert len(entity_onto["edge_types"]) > 0
        assert len(entity_onto["node_properties"]) > 0
        assert len(entity_onto["edge_properties"]) > 0
    
    def test_default_msio_ontology_has_content(self):
        """Test that default MSIO ontology has expected content."""
        default = get_default_ontology()
        msio_onto = default["msio_ontology"]
        
        assert "ontology_name" in msio_onto
        assert "version" in msio_onto
        assert "description" in msio_onto
        assert "disciplines" in msio_onto
        
        assert len(msio_onto["disciplines"]) > 0
    
    def test_default_ontology_node_types(self):
        """Test that default ontology has expected node types."""
        ontology = get_ontology()
        node_types = ontology.entity_ontology.node_types
        
        expected_types = ["Equipment", "Material", "Process", "Project"]
        for node_type in expected_types:
            assert node_type in node_types
    
    def test_default_ontology_edge_types(self):
        """Test that default ontology has expected edge types."""
        ontology = get_ontology()
        edge_types = ontology.entity_ontology.edge_types
        
        expected_types = ["HAS_EQUIPMENT", "USES_EQUIPMENT", "PART_OF"]
        for edge_type in expected_types:
            assert edge_type in edge_types
    
    def test_default_ontology_properties(self):
        """Test that default ontology has expected properties."""
        ontology = get_ontology()
        node_props = ontology.entity_ontology.node_properties
        edge_props = ontology.entity_ontology.edge_properties
        
        assert "name" in node_props
        assert "capacity" in node_props or "capacity_value" in node_props
        
        assert "confidence" in edge_props
        assert "source_doc" in edge_props


class TestOntologyIntegration:
    """Integration tests for ontology module."""
    
    def test_full_workflow(self):
        """Test complete workflow: load, validate, query."""
        # Load ontology
        ontology = load_ontology()
        assert isinstance(ontology, OntologySchema)
        
        # Validate structure
        # Convert Pydantic models to dict (Pydantic v2 uses model_dump)
        entity_dict = ontology.entity_ontology.model_dump()
        msio_dict = ontology.msio_ontology.model_dump() if ontology.msio_ontology else None
        config = {
            "entity_ontology": entity_dict,
            "msio_ontology": msio_dict,
        }
        is_valid, error = validate_ontology_structure(config)
        assert is_valid is True
        
        # Test queries
        assert is_valid_node_type("Equipment")
        assert is_valid_edge_type("HAS_EQUIPMENT")
        assert is_valid_node_property("name")
        
        # Test MSIO hierarchy
        disciplines = get_all_disciplines()
        assert len(disciplines) > 0
        
        if len(disciplines) > 0:
            categories = get_categories_for_discipline(disciplines[0])
            assert isinstance(categories, list)
    
    def test_ontology_schema_methods(self):
        """Test OntologySchema utility methods."""
        ontology = get_ontology()
        
        # Test get_node_type
        assert ontology.get_node_type("Equipment") == "Equipment"
        assert ontology.get_node_type("Invalid") is None
        
        # Test get_edge_type
        assert ontology.get_edge_type("HAS_EQUIPMENT") == "HAS_EQUIPMENT"
        assert ontology.get_edge_type("Invalid") is None
        
        # Test is_valid_property
        assert ontology.is_valid_property("name", is_edge=False) is True
        assert ontology.is_valid_property("invalid", is_edge=False) is False
        
        # Test get_msio_path
        if ontology.msio_ontology:
            path = ontology.get_msio_path("Mechanical Equipment")
            assert isinstance(path, list)
            assert "Mechanical Equipment" in path
