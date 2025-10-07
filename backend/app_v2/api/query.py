"""
Natural language query API endpoints.

Handles conversational queries about projects, scenarios, and options.
Uses LLM to interpret questions and generate answers with data provenance.
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
import logging

from app_v2.core.database import get_database
from app_v2.schemas.query import QueryRequest, QueryResponse, QueryHistoryResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=QueryResponse)
async def query(
    query_request: QueryRequest = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Process a natural language query.

    Examples:
    - "What's the cost difference between options in scenario X?"
    - "Which crusher model has the lowest installed cost?"
    - "Show me all crushers with capacity > 1000 tph"
    - "What are the downstream impacts of changing to a 54-75 crusher?"

    The system:
    1. Parses the query using LLM
    2. Determines required data
    3. Queries the database
    4. Formats a natural language response
    5. Returns data with provenance

    Args:
        query_request: Query request with question and context
        db: Database connection

    Returns:
        Query response with answer and data

    Raises:
        HTTPException: If query fails
    """
    try:
        logger.info(f"Processing query", extra={"query": query_request.query[:100]})

        # TODO: Implement query processing with LLM
        # This is a placeholder - actual implementation would use
        # services/query_processor.py

        # For now, return a simple response
        return QueryResponse(
            query=query_request.query,
            answer="Query processing not yet implemented. This endpoint will use LLM to interpret and answer questions about your mining projects.",
            confidence=0.0,
            data_sources=[],
            suggested_followups=[],
        )

    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to process query: {str(e)}"
        )


@router.get("/history", response_model=QueryHistoryResponse)
async def get_query_history(
    project_id: Optional[str] = None,
    limit: int = 20,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get query history.

    Args:
        project_id: Optional filter by project
        limit: Maximum queries to return
        db: Database connection

    Returns:
        Query history
    """
    try:
        # TODO: Implement query history retrieval
        # Would query a queries collection

        return QueryHistoryResponse(queries=[], total=0)

    except Exception as e:
        logger.error(f"Error getting query history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get query history: {str(e)}"
        )
