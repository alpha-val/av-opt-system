from __future__ import annotations
import datetime
import uuid
import jwt
import os
from fastapi import APIRouter, HTTPException, Depends, Body, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, EmailStr
from werkzeug.security import generate_password_hash, check_password_hash
from .bronze_store import db
from app.vector_db.vector_operations import pc
from app.vector_db.vector_operations import index as pinecone_index
from app.vector_db.vector_operations import index_name
# Create API router
router_admin = APIRouter()

# Security
security = HTTPBearer()

# Configuration for JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = 60 * 24  # 1 day
REFRESH_TOKEN_EXPIRY_DAYS = 30  # 30 days


def verify_token(token: str, expected_type: str = "access") -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token, "access")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    # Get user from database
    user = db().users.find_one(
        {"user_id": user_id}, {"password_hash": 0}  # Exclude password hash
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    if not user.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive"
        )

    return user


# Auth Routes
@router_admin.post("/admin/clear_all_data")
async def clear_all_data(current_user: dict = Depends(get_current_user)):
    """Clear all data belonging to the current user - Admin only"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )

    user_id = current_user["user_id"]
    
    # Clear collections with user_id filter
    collections_cleared = []
    
    # Clear chunks belonging to this user
    chunks_result = db().chunks.delete_many({"properties.user_id": user_id})
    collections_cleared.append(f"chunks: {chunks_result.deleted_count}")
    
    # Clear entities belonging to this user
    entities_result = db().entities.delete_many({"properties.user_id": user_id})
    collections_cleared.append(f"entities: {entities_result.deleted_count}")
    
    # Clear relations belonging to this user
    relations_result = db().relations.delete_many({"properties.user_id": user_id})
    collections_cleared.append(f"relations: {relations_result.deleted_count}")
    
    # Clear rows belonging to this user
    rows_result = db().rows.delete_many({"properties.user_id": user_id})
    collections_cleared.append(f"rows: {rows_result.deleted_count}")
    
    # Clear tables belonging to this user
    tables_result = db().tables.delete_many({"properties.user_id": user_id})
    collections_cleared.append(f"tables: {tables_result.deleted_count}")

    # Clear cost estimates belonging to this user
    scenarios_result = db().scenarios.delete_many({"user_id": user_id})
    collections_cleared.append(f"scenarios: {scenarios_result.deleted_count}")

    # Clear cost estimates belonging to this user
    cost_estimates_result = db().cost_estimates.delete_many({"user_id": user_id})
    collections_cleared.append(f"cost_estimates: {cost_estimates_result.deleted_count}")

    # Clear documents belonging to this user
    documents_result = db().documents.delete_many({"user_id": user_id})
    collections_cleared.append(f"documents: {documents_result.deleted_count}")
    
    # Clear projects belonging to this user
    projects_result = db().projects.delete_many({"user_id": user_id})
    collections_cleared.append(f"projects: {projects_result.deleted_count}")

    # Clear vectors from Pinecone index
    try:
        # Initialize the Pinecone index
        pinecone_index = pc.Index(index_name)

        # Get all namespaces from the Pinecone index
        index_stats = pinecone_index.describe_index_stats()
        namespaces = index_stats["namespaces"].keys()

        # Delete vectors for each namespace
        for namespace in namespaces:
            pinecone_index.delete(filter={"user_id": user_id}, namespace=namespace)
            collections_cleared.append(f"vectors: all vectors deleted from namespace '{namespace}'")

    except Exception as e:
        collections_cleared.append(f"vectors: failed to delete vectors from Pinecone - {e}")

    print(f"[ADMIN] User {user_id} cleared their data: {collections_cleared}")

    return {
        "message": "All data cleared successfully",
        "user_id": user_id,
        "collections_cleared": collections_cleared,
        "cleared_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
