"""
Centralized configuration for Smart Airport Command Center.
Loads settings from .env file and provides defaults.
"""

import os
from pydantic_settings import BaseSettings
from pathlib import Path

# Determine the backend root directory
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Security
    # SECRET_KEY: JWT signing key. MUST be overridden via environment in
    # production. The default here exists only so the app can start for
    # development/demo without configuration.
    SECRET_KEY: str = "smart-airport-command-center-secret-key-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Alert Thresholds
    # These are the operational thresholds used by the Smart Alert Engine,
    # the Congestion Detection and the Staff Recommendation Engine.
    # They are configurable so airport operators can tune them without code
    # changes. Values represent the synthetic operational dataset scale and
    # are demonstration defaults:
    #   QUEUE_HIGH_THRESHOLD        - queue length (people) above which queue is "very high"
    #   QUEUE_MEDIUM_THRESHOLD      - queue length (people) above which queue is "elevated"
    #   WAITING_HIGH_THRESHOLD      - waiting time (minutes) above which wait is "critical"
    #   WAITING_MEDIUM_THRESHOLD    - waiting time (minutes) above which wait is "elevated"
    #   PASSENGER_CAPACITY_THRESHOLD- passenger flow considered terminal capacity
    #   PASSENGER_WARNING_THRESHOLD - passenger flow considered high (warning)
    QUEUE_HIGH_THRESHOLD: int = 100
    QUEUE_MEDIUM_THRESHOLD: int = 50
    WAITING_HIGH_THRESHOLD: int = 45
    WAITING_MEDIUM_THRESHOLD: int = 25
    PASSENGER_CAPACITY_THRESHOLD: int = 8000
    PASSENGER_WARNING_THRESHOLD: int = 5000

    # Rate Limiting
    # In-memory sliding window: max RATE_LIMIT_REQUESTS per IP per
    # RATE_LIMIT_WINDOW seconds. Documentation-only for development:
    # in-memory state is lost on restart and not shared across processes.
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # Paths
    MODELS_DIR: str = str(BACKEND_DIR / "models")
    DATASETS_DIR: str = str(BACKEND_DIR / "datasets")
    LOGS_DIR: str = str(BACKEND_DIR / "logs")
    
    model_config = {
        "env_file": str(BACKEND_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

# Global settings instance
settings = Settings()

# Warn when the default/development SECRET_KEY is in use so operators notice
# before deploying with an insecure key.
_DEFAULT_SECRET = "smart-airport-command-center-secret-key-2024"
if settings.SECRET_KEY == _DEFAULT_SECRET:
    print("⚠️  WARNING: SECRET_KEY is using the default development value.")
    print("           Set SECRET_KEY in the environment (or backend/.env) before deploying.")

# Ensure logs directory exists
os.makedirs(settings.LOGS_DIR, exist_ok=True)
