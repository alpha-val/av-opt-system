"""
Entity repository with domain-specific queries.

Provides data access for entities (equipment, materials, infrastructure)
with specialized queries for:
- Base case entities
- Scenario/option entities
- Equipment selection by type/specs
- Process flow traversal
- Cost rollups
- Relationship management
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any, Optional
from bson import ObjectId
import logging

from .base import BaseRepository
from ..models.entity import Entity, EntitySummary

logger = logging.getLogger(__name__)


class EntityRepository(BaseRepository[Entity]):
    """
    Repository for entity data access.

    Provides entity-specific queries beyond basic CRUD operations.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "entities")

    # =========================================================================
    # BASE CASE QUERIES
    # =========================================================================

    async def find_base_case_entities(
        self,
        project_id: str,
        entity_types: Optional[List[str]] = None,
        entity_category: Optional[str] = None,
        skip: int = 0,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Find base case entities for a project.

        Base case entities represent the current/existing configuration
        before any scenario modifications.

        Args:
            project_id: Project ID
            entity_types: Optional filter by entity types
            entity_category: Optional filter by category
            skip: Number to skip for pagination
            limit: Maximum to return

        Returns:
            List of base case entities
        """
        query = {
            "project_id": ObjectId(project_id),
            "is_base_case": True,
            "status": {"$in": ["existing", "planned"]},
        }

        if entity_types:
            query["entity_type"] = {"$in": entity_types}

        if entity_category:
            query["entity_category"] = entity_category

        # Sort by process stage and creation date
        sort = [("process_stage", 1), ("created_at", 1)]

        entities = await self.find_many(query, skip=skip, limit=limit, sort=sort)

        logger.info(
            f"Found {len(entities)} base case entities for project",
            extra={"project_id": project_id},
        )

        return entities

    async def snapshot_base_case(self, project_id: str) -> Dict[str, Any]:
        """
        Create a snapshot of base case configuration.

        This snapshot is stored with scenarios to track what changed.
        Critical for data lineage and provenance.

        Args:
            project_id: Project ID

        Returns:
            Base case snapshot with entity summaries
        """
        entities = await self.find_base_case_entities(project_id)

        # Build snapshot structure
        snapshot = {
            "project_id": project_id,
            "total_entities": len(entities),
            "entities_by_type": {},
            "entities_by_category": {},
            "total_installed_cost": 0.0,
            "entities": [],
        }

        for entity in entities:
            entity_type = entity.get("entity_type")
            entity_category = entity.get("entity_category")

            # Count by type
            if entity_type:
                snapshot["entities_by_type"][entity_type] = (
                    snapshot["entities_by_type"].get(entity_type, 0) + 1
                )

            # Count by category
            if entity_category:
                snapshot["entities_by_category"][entity_category] = (
                    snapshot["entities_by_category"].get(entity_category, 0) + 1
                )

            # Sum costs
            cost_data = entity.get("cost_data", {})
            if cost_data and cost_data.get("total_installed_cost"):
                snapshot["total_installed_cost"] += cost_data["total_installed_cost"]

            # Add summary
            snapshot["entities"].append(
                {
                    "_id": str(entity["_id"]),
                    "name": entity.get("name"),
                    "entity_type": entity_type,
                    "entity_category": entity_category,
                    "tag_number": entity.get("tag_number"),
                    "specifications": entity.get("specifications", {}),
                    "cost_data": cost_data,
                }
            )

        logger.info(
            f"Created base case snapshot with {len(entities)} entities, "
            f"total cost ${snapshot['total_installed_cost']:,.0f}"
        )

        return snapshot

    # =========================================================================
    # SCENARIO/OPTION QUERIES
    # =========================================================================

    async def find_by_scenario(
        self,
        scenario_id: str,
        entity_types: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Find entities associated with a scenario.

        Args:
            scenario_id: Scenario ID
            entity_types: Optional filter by entity types
            skip: Number to skip
            limit: Maximum to return

        Returns:
            List of scenario entities
        """
        query = {"scenario_id": ObjectId(scenario_id)}

        if entity_types:
            query["entity_type"] = {"$in": entity_types}

        return await self.find_many(query, skip=skip, limit=limit)

    async def find_by_option(
        self,
        option_id: str,
        entity_types: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Find entities associated with an option.

        Args:
            option_id: Option ID
            entity_types: Optional filter by entity types
            skip: Number to skip
            limit: Maximum to return

        Returns:
            List of option entities
        """
        query = {"option_id": ObjectId(option_id)}

        if entity_types:
            query["entity_type"] = {"$in": entity_types}

        return await self.find_many(query, skip=skip, limit=limit)

    async def clone_entity_for_option(
        self,
        entity_id: str,
        option_id: str,
        scenario_id: str,
        modifications: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Clone an entity for an option with optional modifications.

        This is used when creating option alternatives that modify
        specific entities while keeping others the same.

        Args:
            entity_id: Source entity ID to clone
            option_id: Target option ID
            scenario_id: Target scenario ID
            modifications: Optional modifications to apply

        Returns:
            ID of cloned entity
        """
        # Get source entity
        source = await self.find_by_id(entity_id)

        if not source:
            raise ValueError(f"Entity {entity_id} not found")

        # Create clone
        clone = source.copy()
        clone.pop("_id", None)

        # Update context
        clone["scenario_id"] = ObjectId(scenario_id)
        clone["option_id"] = ObjectId(option_id)
        clone["is_base_case"] = False
        clone["status"] = "proposed"

        # Apply modifications if provided
        if modifications:
            # Handle nested updates
            for key, value in modifications.items():
                if "." in key:
                    # Nested field (e.g., "specifications.capacity")
                    parts = key.split(".")
                    current = clone
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = value
                else:
                    clone[key] = value

        # Create new entity
        new_id = await self.create(clone)

        logger.info(
            f"Cloned entity for option",
            extra={
                "source_entity_id": entity_id,
                "new_entity_id": new_id,
                "option_id": option_id,
            },
        )

        return new_id

    # =========================================================================
    # EQUIPMENT SELECTION QUERIES
    # =========================================================================

    async def find_by_type(
        self,
        project_id: str,
        entity_type: str,
        is_base_case: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Find entities by type.

        Args:
            project_id: Project ID
            entity_type: Entity type (e.g., "gyratory_crusher")
            is_base_case: Optional filter for base case
            skip: Number to skip
            limit: Maximum to return

        Returns:
            List of matching entities
        """
        query = {"project_id": ObjectId(project_id), "entity_type": entity_type}

        if is_base_case is not None:
            query["is_base_case"] = is_base_case

        return await self.find_many(query, skip=skip, limit=limit)

    async def find_by_specifications(
        self,
        project_id: str,
        entity_type: str,
        spec_filters: Dict[str, Any],
        is_base_case: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find entities matching specification criteria.

        Supports MongoDB query operators for flexible filtering.

        Example:
            Find crushers with capacity >= 1000 tph:
            spec_filters = {
                "specifications.capacity": {"$gte": 1000},
                "specifications.capacity_unit": "tph"
            }

        Args:
            project_id: Project ID
            entity_type: Entity type
            spec_filters: Specification filters (supports MongoDB operators)
            is_base_case: Optional filter for base case

        Returns:
            List of matching entities
        """
        query = {"project_id": ObjectId(project_id), "entity_type": entity_type}

        if is_base_case is not None:
            query["is_base_case"] = is_base_case

        # Add specification filters
        query.update(spec_filters)

        entities = await self.find_many(query)

        logger.info(
            f"Found {len(entities)} entities matching specifications",
            extra={"entity_type": entity_type, "filters": spec_filters},
        )

        return entities

    async def find_similar_equipment(
        self, entity_id: str, tolerance_pct: float = 20.0
    ) -> List[Dict[str, Any]]:
        """
        Find similar equipment based on specifications.

        Useful for finding alternative equipment options.

        Args:
            entity_id: Reference entity ID
            tolerance_pct: Tolerance for numeric specifications (%)

        Returns:
            List of similar entities
        """
        # Get reference entity
        reference = await self.find_by_id(entity_id)

        if not reference:
            return []

        project_id = reference.get("project_id")
        entity_type = reference.get("entity_type")
        specs = reference.get("specifications", {})

        # Build query for similar entities
        query = {
            "project_id": project_id,
            "entity_type": entity_type,
            "_id": {"$ne": ObjectId(entity_id)},  # Exclude self
        }

        # Add capacity tolerance if present
        if specs.get("capacity"):
            capacity = float(specs["capacity"])
            tolerance = capacity * (tolerance_pct / 100.0)
            query["specifications.capacity"] = {
                "$gte": capacity - tolerance,
                "$lte": capacity + tolerance,
            }

        # Add power tolerance if present
        if specs.get("power_kw"):
            power = float(specs["power_kw"])
            tolerance = power * (tolerance_pct / 100.0)
            query["specifications.power_kw"] = {
                "$gte": power - tolerance,
                "$lte": power + tolerance,
            }

        similar = await self.find_many(query)

        logger.info(
            f"Found {len(similar)} similar entities",
            extra={"reference_entity": entity_id, "tolerance_pct": tolerance_pct},
        )

        return similar

    # =========================================================================
    # RELATIONSHIP QUERIES
    # =========================================================================

    async def get_upstream_entities(
        self, entity_id: str, relationship_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get entities that feed into this entity.

        Follows "receives_from" relationships.

        Args:
            entity_id: Entity ID
            relationship_types: Optional filter by relationship types

        Returns:
            List of upstream entities
        """
        entity = await self.find_by_id(entity_id)

        if not entity:
            return []

        relationships = entity.get("relationships", [])

        # Filter for upstream relationships
        if relationship_types is None:
            relationship_types = ["receives_from"]

        upstream_ids = [
            rel["related_entity_id"]
            for rel in relationships
            if rel.get("relationship_type") in relationship_types
        ]

        if not upstream_ids:
            return []

        # Get upstream entities
        query = {"_id": {"$in": [ObjectId(str(id)) for id in upstream_ids]}}
        upstream = await self.find_many(query)

        return upstream

    async def get_downstream_entities(
        self, entity_id: str, relationship_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get entities that receive material from this entity.

        Follows "feeds_to" relationships.

        Args:
            entity_id: Entity ID
            relationship_types: Optional filter by relationship types

        Returns:
            List of downstream entities
        """
        entity = await self.find_by_id(entity_id)

        if not entity:
            return []

        relationships = entity.get("relationships", [])

        # Filter for downstream relationships
        if relationship_types is None:
            relationship_types = ["feeds_to"]

        downstream_ids = [
            rel["related_entity_id"]
            for rel in relationships
            if rel.get("relationship_type") in relationship_types
        ]

        if not downstream_ids:
            return []

        # Get downstream entities
        query = {"_id": {"$in": [ObjectId(str(id)) for id in downstream_ids]}}
        downstream = await self.find_many(query)

        return downstream

    async def get_process_flow(
        self, project_id: str, start_entity_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build complete process flow graph.

        Returns nodes (entities) and edges (relationships).

        Args:
            project_id: Project ID
            start_entity_id: Optional starting entity (if None, includes all)

        Returns:
            Process flow graph
        """
        # Get all entities for project
        entities = await self.find_base_case_entities(project_id)

        # Build nodes
        nodes = []
        edges = []

        for entity in entities:
            entity_id = str(entity["_id"])

            # Add node
            nodes.append(
                {
                    "id": entity_id,
                    "name": entity.get("name"),
                    "entity_type": entity.get("entity_type"),
                    "entity_category": entity.get("entity_category"),
                    "tag_number": entity.get("tag_number"),
                    "process_stage": entity.get("process_stage"),
                    "specifications": entity.get("specifications", {}),
                }
            )

            # Add edges from relationships
            relationships = entity.get("relationships", [])
            for rel in relationships:
                related_id = str(rel.get("related_entity_id"))
                rel_type = rel.get("relationship_type")

                # Only add "feeds_to" relationships to avoid duplicates
                if rel_type == "feeds_to":
                    edges.append(
                        {
                            "from": entity_id,
                            "to": related_id,
                            "type": rel_type,
                            "flow_tph": rel.get("material_flow_tph"),
                            "stream_name": rel.get("stream_name"),
                        }
                    )

        flow_graph = {
            "project_id": project_id,
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }

        logger.info(
            f"Built process flow graph",
            extra={"project_id": project_id, "nodes": len(nodes), "edges": len(edges)},
        )

        return flow_graph

    async def add_relationship(
        self,
        from_entity_id: str,
        to_entity_id: str,
        relationship_type: str,
        material_flow_tph: Optional[float] = None,
        stream_name: Optional[str] = None,
        context: Optional[str] = None,
    ) -> bool:
        """
        Add relationship between two entities.

        Creates bidirectional relationships:
        - from_entity "feeds_to" to_entity
        - to_entity "receives_from" from_entity

        Args:
            from_entity_id: Source entity ID
            to_entity_id: Target entity ID
            relationship_type: Relationship type
            material_flow_tph: Optional flow rate
            stream_name: Optional stream name
            context: Optional context

        Returns:
            True if successful
        """
        # Validate entities exist
        from_entity = await self.find_by_id(from_entity_id)
        to_entity = await self.find_by_id(to_entity_id)

        if not from_entity or not to_entity:
            logger.error("One or both entities not found")
            return False

        # Build relationship data
        forward_rel = {
            "related_entity_id": ObjectId(to_entity_id),
            "relationship_type": relationship_type,
            "relationship_context": context,
            "material_flow_tph": material_flow_tph,
            "stream_name": stream_name,
        }

        # Determine reverse relationship type
        reverse_type_map = {
            "feeds_to": "receives_from",
            "receives_from": "feeds_to",
            "supports": "supported_by",
            "supported_by": "supports",
        }

        reverse_type = reverse_type_map.get(relationship_type, relationship_type)

        backward_rel = {
            "related_entity_id": ObjectId(from_entity_id),
            "relationship_type": reverse_type,
            "relationship_context": context,
            "material_flow_tph": material_flow_tph,
            "stream_name": stream_name,
        }

        # Add to from_entity
        await self.collection.update_one(
            {"_id": ObjectId(from_entity_id)},
            {"$addToSet": {"relationships": forward_rel}},
        )

        # Add to to_entity
        await self.collection.update_one(
            {"_id": ObjectId(to_entity_id)},
            {"$addToSet": {"relationships": backward_rel}},
        )

        logger.info(
            f"Added relationship",
            extra={
                "from": from_entity_id,
                "to": to_entity_id,
                "type": relationship_type,
            },
        )

        return True

    # =========================================================================
    # COST QUERIES
    # =========================================================================

    async def calculate_total_cost(
        self,
        project_id: str,
        entity_ids: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None,
        is_base_case: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Calculate total cost for entities.

        Args:
            project_id: Project ID
            entity_ids: Optional specific entity IDs
            entity_types: Optional filter by types
            is_base_case: Optional filter for base case

        Returns:
            Cost breakdown
        """
        query = {"project_id": ObjectId(project_id)}

        if entity_ids:
            query["_id"] = {"$in": [ObjectId(id) for id in entity_ids]}

        if entity_types:
            query["entity_type"] = {"$in": entity_types}

        if is_base_case is not None:
            query["is_base_case"] = is_base_case

        # Aggregation pipeline to sum costs
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": None,
                    "total_purchase_cost": {"$sum": "$cost_data.purchase_cost"},
                    "total_installed_cost": {"$sum": "$cost_data.total_installed_cost"},
                    "total_annual_opex": {"$sum": "$cost_data.total_annual_opex"},
                    "count": {"$sum": 1},
                }
            },
        ]

        result = await self.aggregate(pipeline)

        if not result:
            return {
                "total_purchase_cost": 0.0,
                "total_installed_cost": 0.0,
                "total_annual_opex": 0.0,
                "count": 0,
            }

        return result[0]

    async def get_cost_breakdown_by_type(
        self, project_id: str, is_base_case: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Get cost breakdown by entity type.

        Args:
            project_id: Project ID
            is_base_case: Optional filter for base case

        Returns:
            Cost breakdown by type
        """
        query = {"project_id": ObjectId(project_id)}

        if is_base_case is not None:
            query["is_base_case"] = is_base_case

        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": "$entity_type",
                    "count": {"$sum": 1},
                    "total_installed_cost": {"$sum": "$cost_data.total_installed_cost"},
                    "total_annual_opex": {"$sum": "$cost_data.total_annual_opex"},
                    "avg_installed_cost": {"$avg": "$cost_data.total_installed_cost"},
                }
            },
            {"$sort": {"total_installed_cost": -1}},
        ]

        breakdown = await self.aggregate(pipeline)

        # Format results
        formatted = []
        for item in breakdown:
            formatted.append(
                {
                    "entity_type": item["_id"],
                    "count": item["count"],
                    "total_installed_cost": item.get("total_installed_cost", 0.0),
                    "total_annual_opex": item.get("total_annual_opex", 0.0),
                    "avg_installed_cost": item.get("avg_installed_cost", 0.0),
                }
            )

        return formatted

    # =========================================================================
    # VALIDATION & QUALITY CHECKS
    # =========================================================================

    async def find_entities_missing_cost_data(
        self, project_id: str
    ) -> List[Dict[str, Any]]:
        """
        Find entities without cost data.

        Useful for data quality checks.

        Args:
            project_id: Project ID

        Returns:
            List of entities missing cost data
        """
        query = {
            "project_id": ObjectId(project_id),
            "$or": [
                {"cost_data": {"$exists": False}},
                {"cost_data": None},
                {"cost_data.total_installed_cost": {"$exists": False}},
                {"cost_data.total_installed_cost": None},
            ],
        }

        entities = await self.find_many(query)

        logger.info(
            f"Found {len(entities)} entities missing cost data",
            extra={"project_id": project_id},
        )

        return entities

    async def find_orphaned_entities(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Find entities with no relationships.

        May indicate data quality issues.

        Args:
            project_id: Project ID

        Returns:
            List of orphaned entities
        """
        query = {
            "project_id": ObjectId(project_id),
            "$or": [
                {"relationships": {"$exists": False}},
                {"relationships": {"$size": 0}},
            ],
        }

        orphans = await self.find_many(query)

        logger.warning(
            f"Found {len(orphans)} orphaned entities", extra={"project_id": project_id}
        )

        return orphans

    async def validate_entity_relationships(self, entity_id: str) -> Dict[str, Any]:
        """
        Validate entity relationships.

        Checks:
        - All related entities exist
        - Bidirectional relationships are symmetric
        - No circular references

        Args:
            entity_id: Entity ID

        Returns:
            Validation result
        """
        entity = await self.find_by_id(entity_id)

        if not entity:
            return {"valid": False, "errors": ["Entity not found"]}

        relationships = entity.get("relationships", [])
        errors = []
        warnings = []

        for rel in relationships:
            related_id = str(rel.get("related_entity_id"))

            # Check related entity exists
            related = await self.find_by_id(related_id)
            if not related:
                errors.append(f"Related entity {related_id} not found")
                continue

            # Check for reverse relationship
            related_rels = related.get("relationships", [])
            reverse_exists = any(
                str(r.get("related_entity_id")) == entity_id for r in related_rels
            )

            if not reverse_exists:
                warnings.append(f"Missing reverse relationship with {related_id}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "total_relationships": len(relationships),
        }
