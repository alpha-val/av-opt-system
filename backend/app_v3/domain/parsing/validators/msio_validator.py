"""
MSIO ontology validation for extracted entities.

Validates that entities match the MSIO ontology hierarchy:
discipline → category → subcategory → entity
"""

from typing import Dict, Any, List, Tuple, Optional
from app_v3.domain.ontology import (
    get_ontology,
    get_entities_for_subcategory,
    validate_node_type,
)
import logging

logger = logging.getLogger(__name__)


class MSIOValidator:
    """Validate entities against MSIO ontology."""
    
    def __init__(self):
        """Initialize validator with ontology."""
        self.ontology = get_ontology()
    
    def validate_entity(
        self,
        entity: Dict[str, Any],
        strict: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Validate entity against MSIO ontology.
        
        Args:
            entity: Entity dictionary with properties containing MSIO fields
            strict: If True, invalid entities are rejected. If False, warnings are logged.
            
        Returns:
            Tuple of (is_valid, warnings)
            - is_valid: True if entity matches MSIO ontology
            - warnings: List of warning messages
        """
        warnings = []
        properties = entity.get("properties", {})
        
        # Extract MSIO fields
        discipline = properties.get("discipline")
        category = properties.get("category")
        subcategory = properties.get("subcategory")
        entity_name = properties.get("entity")  # Note: singular "entity" field
        
        # Check all required fields are present
        missing_fields = []
        if not discipline:
            missing_fields.append("discipline")
        if not category:
            missing_fields.append("category")
        if not subcategory:
            missing_fields.append("subcategory")
        if not entity_name:
            missing_fields.append("entity")
        
        if missing_fields:
            warning = f"Entity {entity.get('id', 'unknown')} missing MSIO fields: {', '.join(missing_fields)}"
            warnings.append(warning)
            if strict:
                logger.warning(warning)
                return False, warnings
            else:
                logger.debug(warning)
                return False, warnings  # Still invalid, but non-blocking
        
        # Validate MSIO hierarchy path
        try:
            # Get valid entities for this subcategory
            valid_entities = get_entities_for_subcategory(
                discipline, category, subcategory
            )
            
            if not valid_entities:
                warning = (
                    f"Entity {entity.get('id', 'unknown')}: "
                    f"No entities found for subcategory '{subcategory}' "
                    f"in category '{category}' of discipline '{discipline}'"
                )
                warnings.append(warning)
                logger.warning(warning)
                return False, warnings
            
            # Check if entity name matches any valid entity (case-insensitive)
            entity_lower = entity_name.lower().strip()
            valid_entities_lower = [e.lower().strip() for e in valid_entities]
            
            if entity_lower not in valid_entities_lower:
                warning = (
                    f"Entity {entity.get('id', 'unknown')}: "
                    f"Entity name '{entity_name}' not found in MSIO ontology. "
                    f"Valid entities for '{discipline}/{category}/{subcategory}': {valid_entities}"
                )
                warnings.append(warning)
                logger.warning(warning)
                return False, warnings
            
            # Entity is valid
            logger.debug(
                f"Entity {entity.get('id', 'unknown')} validated: "
                f"{discipline}/{category}/{subcategory}/{entity_name}"
            )
            return True, warnings
            
        except Exception as e:
            warning = f"Entity {entity.get('id', 'unknown')}: Validation error: {str(e)}"
            warnings.append(warning)
            logger.error(warning)
            return False, warnings
    
    def validate_batch(
        self,
        entities: List[Dict[str, Any]],
        strict: bool = False
    ) -> Dict[str, Any]:
        """
        Validate a batch of entities.
        
        Args:
            entities: List of entity dictionaries
            strict: If True, invalid entities are filtered out
            
        Returns:
            Dictionary with:
            - valid_entities: List of valid entities
            - invalid_entities: List of invalid entities
            - warnings: List of all warning messages
            - stats: Validation statistics
        """
        valid_entities = []
        invalid_entities = []
        all_warnings = []
        
        for entity in entities:
            is_valid, warnings = self.validate_entity(entity, strict=strict)
            all_warnings.extend(warnings)
            
            if is_valid:
                valid_entities.append(entity)
            else:
                invalid_entities.append(entity)
        
        stats = {
            "total": len(entities),
            "valid": len(valid_entities),
            "invalid": len(invalid_entities),
            "validation_rate": len(valid_entities) / len(entities) if entities else 0.0,
        }
        
        logger.info(
            f"Validated {len(entities)} entities: "
            f"{len(valid_entities)} valid, {len(invalid_entities)} invalid"
        )
        
        return {
            "valid_entities": valid_entities,
            "invalid_entities": invalid_entities,
            "warnings": all_warnings,
            "stats": stats,
        }
    
    def validate_node_type(self, node_type: str) -> bool:
        """
        Validate node type against ontology.
        
        Args:
            node_type: Node type string (e.g., "Equipment", "Material")
            
        Returns:
            True if valid node type
        """
        return validate_node_type(node_type, self.ontology)

