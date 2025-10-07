"""
Configuration management for Alpha-Val Pro.

This module handles all configuration from environment variables and provides
typed settings throughout the application.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via .env file or environment variables.
    """

    # Application
    APP_NAME: str = "Alpha-Val Pro Costing API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "alpha_val_pro"

    # API
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    # Cost Escalation Defaults
    DEFAULT_ESCALATION_INDEX: str = "CEPCI"
    DEFAULT_COST_BASE_YEAR: int = 2015
    DEFAULT_TARGET_YEAR: int = 2025

    # Lang Factors Defaults
    DEFAULT_LANG_FACTOR_CATEGORY: str = "Primary Crushing"
    DEFAULT_EQUIPMENT_MULTIPLIER: float = 3.5

    # Analysis Configuration
    ENABLE_DOWNSTREAM_ANALYSIS: bool = True
    ENABLE_OPEX_ESTIMATION: bool = True
    ENABLE_NPV_CALCULATION: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # or "text"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
