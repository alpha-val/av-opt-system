"""
Natural language query schemas.

Defines API contracts for query operations.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class DataSource(BaseModel):
    """
    A data source cited in a query response.
    
    Provides provenance for query answers.
    """
    
    source_type: str = Field(
        ...,
        description="Type of source (e.g., 'entity', 'table', 'scenario', 'option')"
    )
    source_id: str = Field(
        ...,
        description="ID of source"
    )
    source_name: Optional[str] = Field(
        None,
        description="Name/description of source"
    )
    
    # Data extracted
    data_used: Optional[Dict[str, Any]] = Field(
        None,
        description="Specific data from this source"
    )
    
    # Confidence
    relevance_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="How relevant this source is to the query"
    )


class QueryRequest(BaseModel):
    """
    Request schema for natural language query.
    """
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Natural language query"
    )
    
    # Context
    project_id: Optional[str] = Field(
        None,
        description="Project context for query"
    )
    scenario_id: Optional[str] = Field(
        None,
        description="Scenario context for query"
    )
    
    # Query parameters
    max_results: int = Field(
        10,
        ge=1,
        le=100,
        description="Maximum results to return"
    )
    include_provenance: bool = Field(
        True,
        description="Whether to include data source provenance"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "query": "What's the cost difference between the top 3 options in scenario XYZ?",
                "project_id": "507f1f77bcf86cd799439011",
                "scenario_id": "507f1f77bcf86cd799439012",
                "max_results": 10,
                "include_provenance": True
            }
        }


class QueryResponse(BaseModel):
    """
    Response schema for natural language query.
    
    Includes natural language answer plus structured data.
    """
    
    query: str = Field(
        ...,
        description="Original query"
    )
    
    answer: str = Field(
        ...,
        description="Natural language answer"
    )
    
    # Structured data
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Structured data supporting the answer"
    )
    
    # Provenance
    data_sources: List[DataSource] = Field(
        default_factory=list,
        description="Data sources used to answer query"
    )
    
    # Query understanding
    intent: Optional[str] = Field(
        None,
        description="Detected intent (e.g., 'compare_costs', 'find_equipment')"
    )
    entities_mentioned: List[str] = Field(
        default_factory=list,
        description="Entities mentioned in query"
    )
    
    # Confidence
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in answer (0-1)"
    )
    
    # Follow-up suggestions
    suggested_followups: List[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions"
    )
    
    # Metadata
    processing_time_ms: Optional[float] = Field(
        None,
        description="Query processing time in milliseconds"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "query": "What's the cost difference between options?",
                "answer": "The cost difference between the top 3 options ranges from $500K to $1.2M. Option A (Metso 54-75) has the lowest installed cost at $9.6M, while Option C (FLS 60-89) is highest at $10.8M.",
                "data": {
                    "options": [
                        {
                            "name": "Metso Superior MKII 54-75",
                            "installed_cost": 9600000
                        },
                        {
                            "name": "Sandvik CG820i",
                            "installed_cost": 10100000
                        },
                        {
                            "name": "FLS 60-89",
                            "installed_cost": 10800000
                        }
                    ]
                },
                "data_sources": [
                    {
                        "source_type": "option",
                        "source_id": "507f1f77bcf86cd799439013",
                        "source_name": "Metso Superior MKII 54-75",
                        "relevance_score": 1.0
                    }
                ],
                "intent": "compare_costs",
                "confidence": 0.95,
                "suggested_followups": [
                    "Which option has the best NPV?",
                    "What are the downstream impacts of Option A?",
                    "Show me the cost breakdown for Option A"
                ],
                "processing_time_ms": 245.3
            }
        }


class QueryHistoryItem(BaseModel):
    """
    Single item in query history.
    """
    
    query_id: str
    query: str
    answer: str
    confidence: float
    project_id: Optional[str]
    scenario_id: Optional[str]
    timestamp: datetime


class QueryHistoryResponse(BaseModel):
    """
    Response schema for query history.
    """
    
    queries: List[QueryHistoryItem] = Field(
        default_factory=list,
        description="Query history"
    )
    total: int = Field(
        0,
        description="Total queries in history"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "queries": [],
                "total": 0
            }
        }