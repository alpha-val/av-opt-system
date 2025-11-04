"""Pydantic schemas for ontology components."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator


class PropertyDefinition(BaseModel):
    """Definition of a property with type and constraints."""
    name: str
    description: Optional[str] = None
    property_type: Optional[str] = None  # e.g., "string", "float", "bool"
    required: bool = False
    default_value: Optional[Any] = None


class NodeType(BaseModel):
    """Node type definition with metadata."""
    name: str
    description: Optional[str] = None
    properties: List[str] = Field(default_factory=list)
    allowed_properties: List[str] = Field(default_factory=list)
    examples: Optional[Dict[str, Any]] = None


class EdgeType(BaseModel):
    """Edge type definition with metadata."""
    name: str
    description: Optional[str] = None
    properties: List[str] = Field(default_factory=list)
    allowed_properties: List[str] = Field(default_factory=list)
    examples: Optional[Dict[str, Any]] = None


class Entity(BaseModel):
    """Entity within a subcategory (MSIO hierarchy)."""
    name: str
    description: Optional[str] = None


class Subcategory(BaseModel):
    """Subcategory within a category (MSIO hierarchy)."""
    name: str
    description: Optional[str] = None
    entity: Optional[str] = None  # Single entity for this subcategory entry


class Category(BaseModel):
    """Category within a discipline (MSIO hierarchy)."""
    name: str
    description: Optional[str] = None
    subcategories: List[Subcategory] = Field(default_factory=list)


class Discipline(BaseModel):
    """Discipline in MSIO hierarchy."""
    name: str
    description: Optional[str] = None
    categories: List[Category] = Field(default_factory=list)


class EntityOntology(BaseModel):
    """Core entity ontology with node and edge types."""
    schema_version: str = "0.1.0"
    node_types: List[str] = Field(default_factory=list)
    edge_types: List[str] = Field(default_factory=list)
    node_properties: List[str] = Field(default_factory=list)
    edge_properties: List[str] = Field(default_factory=list)
    node_descriptions: Dict[str, str] = Field(default_factory=dict)
    edge_descriptions: Dict[str, str] = Field(default_factory=dict)
    node_prop_examples: Dict[str, Any] = Field(default_factory=dict)
    edge_prop_examples: Dict[str, Any] = Field(default_factory=dict)


class MSIOOntology(BaseModel):
    """MSIO hierarchical ontology."""
    ontology_name: str
    version: str
    description: str
    disciplines: List[Discipline] = Field(default_factory=list)


class OntologySchema(BaseModel):
    """Complete ontology schema combining entity and MSIO ontologies."""
    entity_ontology: EntityOntology
    msio_ontology: Optional[MSIOOntology] = None
    
    @validator('entity_ontology', pre=True)
    def validate_entity_ontology(cls, v):
        if isinstance(v, dict):
            return EntityOntology(**v)
        return v
    
    @validator('msio_ontology', pre=True)
    def validate_msio_ontology(cls, v):
        if v is None:
            return None
        if isinstance(v, dict):
            return MSIOOntology(**v)
        return v
    
    def get_node_type(self, node_type: str) -> Optional[str]:
        """Check if node type is valid."""
        return node_type if node_type in self.entity_ontology.node_types else None
    
    def get_edge_type(self, edge_type: str) -> Optional[str]:
        """Check if edge type is valid."""
        return edge_type if edge_type in self.entity_ontology.edge_types else None
    
    def is_valid_property(self, property_name: str, is_edge: bool = False) -> bool:
        """Check if property is valid for nodes or edges."""
        if is_edge:
            return property_name in self.entity_ontology.edge_properties
        return property_name in self.entity_ontology.node_properties
    
    def get_msio_path(
        self,
        discipline: str,
        category: Optional[str] = None,
        subcategory: Optional[str] = None
    ) -> Optional[List[str]]:
        """Get MSIO hierarchy path for a given discipline/category/subcategory."""
        if not self.msio_ontology:
            return None
        
        path = [discipline]
        
        discipline_obj = next(
            (d for d in self.msio_ontology.disciplines if d.name == discipline),
            None
        )
        if not discipline_obj:
            return None
        
        if category:
            path.append(category)
            category_obj = next(
                (c for c in discipline_obj.categories if c.name == category),
                None
            )
            if not category_obj:
                return path
            
            if subcategory:
                path.append(subcategory)
                subcategory_obj = next(
                    (s for s in category_obj.subcategories if s.name == subcategory),
                    None
                )
                if not subcategory_obj:
                    return path
        
        return path
