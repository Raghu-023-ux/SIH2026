from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "SIH26001 - Disaster Intelligence Engine (NER Landslide)"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database: defaults to SQLite for immediate local operation; can be overridden by PostgreSQL URL
    DATABASE_URL: str = "sqlite+aiosqlite:///./sih_disaster.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # --- Landslide Risk Model Weights (Configurable) ---
    # Note: These weights represent a prototype analytical risk model
    WEIGHT_RAINFALL_INTENSITY: float = 0.20
    WEIGHT_RAINFALL_ANOMALY: float = 0.20
    WEIGHT_RAINFALL_PERSISTENCE: float = 0.15
    WEIGHT_SOIL_MOISTURE: float = 0.20
    WEIGHT_SOIL_MOISTURE_TREND: float = 0.10
    WEIGHT_SLOPE_ELEVATION: float = 0.10
    WEIGHT_HISTORICAL_SUSCEPTIBILITY: float = 0.05

    # --- Risk Level Score Thresholds (0-100) ---
    THRESHOLD_MODERATE: float = 25.0
    THRESHOLD_HIGH: float = 50.0
    THRESHOLD_CRITICAL: float = 75.0

    # --- Anomaly Detection Parameters ---
    ANOMALY_Z_THRESHOLD: float = 2.0
    MIN_OBSERVATIONS_FOR_BASELINE: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
