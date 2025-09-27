from __future__ import annotations
import datetime
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Optional
from .bronze_store import db

# Create API router
router_projects = APIRouter()
