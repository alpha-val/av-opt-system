"""
Entity normalization and deduplication.

Generates canonical keys, UUIDs, and merges duplicate entities.
"""

from typing import List, Dict, Any, Optional
import uuid
import logging

logger = logging.getLogger(__name__)

# Fixed namespace for deterministic UUID5 generation
NAMESPACE = uuid.UUID("11111111-2222-3333-4444-555555555555")


class EntityNormalizer:
    """Normalize and deduplicate entities."""
    
    def __init__(self, namespace: Optional[uuid.UUID] = None):
        """
        Initialize normalizer.
        
        Args:
            namespace: UUID namespace for deterministic ID generation
                      (default: fixed namespace)
        """
        self.namespace = namespace or NAMESPACE
    
    def canonical_key(self, entity: Dict[str, Any]) -> str:
        """
        Generate canonical key for entity deduplication.
        
        Format: type|name|original_id
        
        Args:
            entity: Entity dictionary
            
        Returns:
            Canonical key string
        """
        name = (entity.get("properties", {}).get("name") or "").strip().lower()
        orig = (
            (entity.get("properties", {}).get("original_id") or entity.get("id") or "")
            .strip()
            .lower()
        )
        typ = (entity.get("type") or "").strip().lower()
        
        return f"{typ}|{name}|{orig}"
    
    def generate_uuid(self, entity: Dict[str, Any]) -> str:
        """
        Generate deterministic UUID5 for entity based on canonical key.
        
        Args:
            entity: Entity dictionary
            
        Returns:
            UUID string
        """
        key = self.canonical_key(entity)
        return str(uuid.uuid5(self.namespace, key))
    
    def normalize_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize entity: generate UUID and canonical key.
        
        Args:
            entity: Entity dictionary
            
        Returns:
            Normalized entity with id and canonical_key
        """
        # Preserve original ID if present
        original_id = entity.get("id", "")
        
        # Generate canonical key
        canonical_key = self.canonical_key(entity)
        
        # Generate UUID5 from canonical key
        new_id = self.generate_uuid(entity)
        
        # Update entity
        if original_id and original_id != new_id:
            entity.setdefault("properties", {})["original_id"] = original_id
        entity["id"] = new_id
        entity.setdefault("properties", {})["canonical_key"] = canonical_key
        
        return entity
    
    def normalize_batch(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize a batch of entities (generate IDs and canonical keys).
        
        Args:
            entities: List of entity dictionaries
            
        Returns:
            List of normalized entities
        """
        normalized = []
        for entity in entities:
            try:
                normalized_entity = self.normalize_entity(entity.copy())
                normalized.append(normalized_entity)
            except Exception as e:
                logger.error(f"Failed to normalize entity: {e}")
                continue
        
        logger.info(f"Normalized {len(normalized)}/{len(entities)} entities")
        
        return normalized
    
    def deduplicate(
        self,
        entities: List[Dict[str, Any]],
        merge_properties: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate entities by canonical key.
        
        Args:
            entities: List of entity dictionaries
            merge_properties: If True, merge properties from duplicates
            
        Returns:
            List of unique entities
        """
        # First normalize all entities to get canonical keys
        normalized = self.normalize_batch(entities)
        
        # Group by canonical key
        by_key = {}
        for entity in normalized:
            key = entity["properties"].get("canonical_key")
            if not key:
                # Should not happen after normalization, but handle gracefully
                logger.warning(f"Entity {entity.get('id')} missing canonical_key")
                continue
            
            if key in by_key:
                # Merge properties if requested
                if merge_properties:
                    existing_props = by_key[key].get("properties", {})
                    new_props = entity.get("properties", {})
                    # Merge properties (new values override existing)
                    existing_props.update(new_props)
                    by_key[key]["properties"] = existing_props
                    logger.debug(f"Merged duplicate entity with key: {key}")
            else:
                by_key[key] = entity
        
        unique_entities = list(by_key.values())
        
        logger.info(
            f"Deduplicated {len(entities)} entities to {len(unique_entities)} unique entities"
        )
        
        return unique_entities
    
    def normalize_and_deduplicate(
        self,
        entities: List[Dict[str, Any]],
        merge_properties: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Normalize and deduplicate entities in one step.
        
        Args:
            entities: List of entity dictionaries
            merge_properties: If True, merge properties from duplicates
            
        Returns:
            List of normalized, unique entities
        """
        return self.deduplicate(entities, merge_properties=merge_properties)

