from __future__ import annotations
import os, uuid, datetime
from typing import Dict, Any
import jwt
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId  # For MongoDB ObjectId handling
from ....adapters.mongo.client import db  # Import MongoDB client

auth_router = APIRouter(prefix="/api/v1", tags=["auth"])

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = 60 * 24
REFRESH_TOKEN_EXPIRY_DAYS = 30
security = HTTPBearer()

# Get the MongoDB users collection
_users_collection = db().users


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    org_name: str = "alphaval"
    org_id: str = "org_id_tbd"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    is_admin: bool


class UserProfile(BaseModel):
    user_id: str
    name: str
    email: str
    org_name: str
    org_id: str
    active: bool
    created_at: datetime.datetime
    is_admin: bool


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)

def _create_access(data: dict) -> str:
    to_encode = data.copy()
    to_encode.update(
        {
            "exp": _now() + datetime.timedelta(minutes=JWT_EXPIRY_MINUTES),
            "type": "access",
        }
    )
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _create_refresh(data: dict) -> str:
    to_encode = data.copy()
    to_encode.update(
        {
            "exp": _now() + datetime.timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS),
            "type": "refresh",
        }
    )
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _verify(token: str, expected: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected}",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    payload = _verify(token, "access")
    uid = payload.get("sub")
    user = _users_collection.find_one({"_id": ObjectId(uid)})
    if not uid or not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    if not user.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive"
        )
    return user


@auth_router.post(
    "/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(body: UserRegister):
    if _users_collection.find_one({"email": body.email}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )
    uid = str(uuid.uuid4())
    doc = {
        "_id": ObjectId(uid),  # Use ObjectId for MongoDB
        "name": body.name,
        "email": body.email,
        "password_hash": generate_password_hash(body.password, method="pbkdf2:sha256"),
        "org_name": body.org_name,
        "org_id": body.org_id,
        "created_at": _now(),
        "updated_at": _now(),
        "active": True,
        "is_admin": False,
    }
    _users_collection.insert_one(doc)
    access = _create_access({"sub": uid, "email": body.email, "name": body.name})
    refresh = _create_refresh({"sub": uid})
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=JWT_EXPIRY_MINUTES * 60,
        user_id=uid,
        is_admin=False,
    )


@auth_router.post("/auth/login", response_model=TokenResponse)
async def login(body: UserLogin):
    user = _users_collection.find_one({"email": body.email})
    if not user or not check_password_hash(user["password_hash"], body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    if not user.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive"
        )
    user["last_login"] = _now()
    _users_collection.update_one(
        {"_id": user["_id"]}, {"$set": {"last_login": user["last_login"]}}
    )
    access = _create_access(
        {"sub": str(user["_id"]), "email": user["email"], "name": user["name"]}
    )
    refresh = _create_refresh({"sub": str(user["_id"])})
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=JWT_EXPIRY_MINUTES * 60,
        user_id=str(user["_id"]),
        is_admin=user.get("is_admin", False),
    )


@auth_router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(payload: dict):
    token = payload.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing refresh_token"
        )
    data = _verify(token, "refresh")
    uid = data.get("sub")
    user = _users_collection.find_one({"_id": ObjectId(uid)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    if not user.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive"
        )
    access = _create_access(
        {"sub": str(user["_id"]), "email": user["email"], "name": user["name"]}
    )
    new_refresh = _create_refresh({"sub": str(user["_id"])})
    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
        expires_in=JWT_EXPIRY_MINUTES * 60,
        user_id=str(user["_id"]),
        is_admin=user.get("is_admin", False),
    )


@auth_router.get("/auth/me", response_model=UserProfile)
async def me(current: dict = Depends(get_current_user)):
    return UserProfile(
        user_id=str(current["_id"]),
        name=current["name"],
        email=current["email"],
        org_name=current["org_name"],
        org_id=current["org_id"],
        active=current["active"],
        created_at=current["created_at"],
        is_admin=current.get("is_admin", False),
    )


@auth_router.post("/auth/logout")
async def logout():
    return {"message": "Successfully logged out"}


@auth_router.get("/auth/protected")
async def protected(current: dict = Depends(get_current_user)):
    return {
        "message": "This is a protected route",
        "user": {
            "user_id": str(current["_id"]),
            "name": current["name"],
            "email": current["email"],
        },
    }
