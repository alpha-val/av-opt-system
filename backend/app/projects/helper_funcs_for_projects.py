# Helper functions for project-related operations
from typing import Dict, Any
from app.bronze_store import db
from pymongo.collection import Collection

def get_project_details(project_id: str) -> Dict[str, Any]:
    """
    Get aggregated information about a project from related collections.

    Args:
        project_id: The ID of the project.
        db: The database connection object.

    Returns:
        A dictionary containing project stats.
    """
    # Retrieve stats from helper functions
    num_documents, total_document_size = get_document_stats(project_id, db().documents)
    entity_stats = get_entity_stats(project_id, db().entities)
    num_scenarios = get_scenario_stats(project_id, db().scenarios)

    # Combine all stats into a single dictionary
    return {
        "number_of_documents": num_documents,
        "total_document_size": total_document_size,
        "entities_by_type": entity_stats,
        "number_of_scenarios": num_scenarios,
    }


def get_document_stats(project_id: str, documents_collection: Collection) -> (int, int):
    """
    Get the number of documents and their total size for a project.

    Args:
        project_id: The ID of the project.
        documents_collection: The MongoDB collection for documents.

    Returns:
        A tuple containing the number of documents and the total size of documents.
    """
    pipeline = [
        {"$match": {"project_id": project_id}},
        {"$group": {"_id": None, "total_size": {"$sum": "$file_size"}, "count": {"$sum": 1}}},
    ]
    result = list(documents_collection.aggregate(pipeline))
    if result:
        return result[0]["count"], result[0]["total_size"]
    return 0, 0


def get_entity_stats(project_id: str, entities_collection: Collection) -> Dict[str, int]:
    """
    Get the number of entities grouped by type for a project.

    Args:
        project_id: The ID of the project.
        entities_collection: The MongoDB collection for entities.

    Returns:
        A dictionary with entity types as keys and their counts as values.
    """
    pipeline = [
        {"$match": {"project_id": project_id}},
        {"$group": {"_id": "$type", "count": {"$sum": 1}}},
    ]
    result = list(entities_collection.aggregate(pipeline))
    return {item["_id"]: item["count"] for item in result}


def get_scenario_stats(project_id: str, scenarios_collection: Collection) -> int:
    """
    Get the number of scenarios for a project.

    Args:
        project_id: The ID of the project.
        scenarios_collection: The MongoDB collection for scenarios.

    Returns:
        The number of scenarios for the project.
    """
    return scenarios_collection.count_documents({"project_id": project_id})

