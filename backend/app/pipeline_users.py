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

# Create API router
router_auth = APIRouter()

# Security
security = HTTPBearer()

# Configuration for JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = 60 * 24  # 1 day
REFRESH_TOKEN_EXPIRY_DAYS = 30  # 30 days

# Pydantic models
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    org_name: str = "alphaval"
    org_id: str = "org_12345"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserProfile(BaseModel):
    user_id: str
    name: str
    email: str
    org_name: str
    org_id: str
    active: bool
    created_at: datetime.datetime

# Helper functions
def get_password_hash(password: str) -> str:
    """Hash a password using werkzeug's PBKDF2 SHA256"""
    return generate_password_hash(password, method="pbkdf2:sha256")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return check_password_hash(hashed_password, plain_password)

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=JWT_EXPIRY_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(token: str, expected_type: str = "access") -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}"
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token, "access")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user from database
    user = db().users.find_one(
        {"user_id": user_id},
        {"password_hash": 0}  # Exclude password hash
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    return user

# Auth Routes
@router_auth.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """
    Register a new user and return JWT tokens
    """
    try:
        # Check if user already exists by email
        existing_user = db().users.find_one({"email": user_data.email})
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email {user_data.email} already exists"
            )
        
        # Generate unique user ID
        user_id = str(uuid.uuid4())
        
        # Hash password
        password_hash = get_password_hash(user_data.password)
        
        # Create user document
        user_document = {
            "user_id": user_id,
            "name": user_data.name,
            "email": user_data.email,
            "password_hash": password_hash,
            "org_name": user_data.org_name,
            "org_id": user_data.org_id,
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow(),
            "active": True,
        }
        
        # Insert user into database
        result = db().users.insert_one(user_document)
        
        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        # Create tokens
        token_data = {
            "sub": user_id,
            "email": user_data.email,
            "name": user_data.name
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": user_id})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=JWT_EXPIRY_MINUTES * 60  # Convert to seconds
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router_auth.post("/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """
    Authenticate user and return JWT tokens
    """
    try:
        # Find user by email
        user = db().users.find_one({"email": user_data.email})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(user_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.get("active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Update last login time
        db().users.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"last_login": datetime.datetime.utcnow()}}
        )
        
        # Create tokens
        token_data = {
            "sub": user["user_id"],
            "email": user["email"],
            "name": user["name"]
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": user["user_id"]})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=JWT_EXPIRY_MINUTES * 60  # Convert to seconds
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router_auth.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    """
    try:
        # Verify refresh token
        payload = verify_token(refresh_data.refresh_token, "refresh")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user from database
        user = db().users.find_one(
            {"user_id": user_id},
            {"password_hash": 0}
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.get("active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Create new tokens
        token_data = {
            "sub": user["user_id"],
            "email": user["email"],
            "name": user["name"]
        }
        
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token({"sub": user["user_id"]})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=JWT_EXPIRY_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router_auth.get("/auth/me", response_model=UserProfile)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user's profile
    """
    # Convert ObjectId to string for JSON serialization
    current_user["_id"] = str(current_user["_id"])
    
    return UserProfile(
        user_id=current_user["user_id"],
        name=current_user["name"],
        email=current_user["email"],
        org_name=current_user["org_name"],
        org_id=current_user["org_id"],
        active=current_user["active"],
        created_at=current_user["created_at"]
    )

@router_auth.post("/auth/logout")
async def logout():
    """
    Logout user (client-side token deletion)
    For JWT, logout is handled client-side by deleting the token.
    In production, you might want to implement token blacklisting.
    """
    return {"message": "Successfully logged out"}

# Protected route example
@router_auth.get("/auth/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    """
    Example of a protected route that requires authentication
    """
    return {
        "message": "This is a protected route",
        "user": {
            "user_id": current_user["user_id"],
            "name": current_user["name"],
            "email": current_user["email"]
        }
    }
