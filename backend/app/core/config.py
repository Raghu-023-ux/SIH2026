from typing import List, Union, Dict, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "SIH26001 - Disaster Intelligence Engine (NER Landslide)"
    VERSION: str = "0.3.0"
    ENGINE_VERSION: str = "prototype-v0.3"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database: defaults to SQLite for local runs; overridden by PostgreSQL URL in production/docker
    DATABASE_URL: str = "sqlite+aiosqlite:///./sih_disaster.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Ingestion & Data Mode: "LIVE" (Open-Meteo with fallback) or "SIMULATION" (deterministic scenarios)
    DATA_MODE: str = "LIVE"

    # External Provider Configuration (Open-Meteo - Free Public API)
    OPEN_METEO_API_URL: str = "https://api.open-meteo.com/v1/forecast"
    WEATHER_REQUEST_TIMEOUT_SECONDS: float = 7.0
    WEATHER_MAX_RETRIES: int = 2
    WEATHER_BACKOFF_FACTOR: float = 0.5
    WEATHER_CACHE_TTL_SECONDS: int = 600  # 10 minutes cache

    # Data Freshness Thresholds (Minutes)
    DATA_FRESHNESS_WEATHER_MINUTES: int = 60
    DATA_FRESHNESS_SOIL_MOISTURE_MINUTES: int = 180

    # --- Agentic AI Layer Configuration ---
    LLM_PROVIDER: str = "mock"  # "mock", "openai", "gemini"
    LLM_MODEL: str = "gemini-1.5-flash"
    LLM_API_KEY: Optional[str] = None
    AI_MODE: str = "MOCK"  # "MOCK" or "LIVE"
    AGENT_MAX_STEPS: int = 6
    AGENT_TIMEOUT_SECONDS: float = 20.0

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

    # --- Landslide Risk Factor Weights (Centralized & Normalized 0-1) ---
    RISK_WEIGHTS: Dict[str, float] = {
        "rainfall_intensity": 0.20,
        "rainfall_anomaly": 0.15,
        "rainfall_persistence": 0.15,
        "soil_moisture": 0.15,
        "soil_moisture_trend": 0.10,
        "terrain": 0.15,
        "historical": 0.10,
    }

    # Backward compatibility individual weight getters
    @property
    def WEIGHT_RAINFALL_INTENSITY(self) -> float:
        return self.RISK_WEIGHTS["rainfall_intensity"]

    @property
    def WEIGHT_RAINFALL_ANOMALY(self) -> float:
        return self.RISK_WEIGHTS["rainfall_anomaly"]

    @property
    def WEIGHT_RAINFALL_PERSISTENCE(self) -> float:
        return self.RISK_WEIGHTS["rainfall_persistence"]

    @property
    def WEIGHT_SOIL_MOISTURE(self) -> float:
        return self.RISK_WEIGHTS["soil_moisture"]

    @property
    def WEIGHT_SOIL_MOISTURE_TREND(self) -> float:
        return self.RISK_WEIGHTS["soil_moisture_trend"]

    @property
    def WEIGHT_SLOPE_ELEVATION(self) -> float:
        return self.RISK_WEIGHTS["terrain"]

    @property
    def WEIGHT_HISTORICAL_SUSCEPTIBILITY(self) -> float:
        return self.RISK_WEIGHTS["historical"]

    # --- Risk Level Score Thresholds (0-100) ---
    THRESHOLD_WATCH: float = 25.0
    THRESHOLD_ELEVATED: float = 40.0
    THRESHOLD_HIGH: float = 50.0
    THRESHOLD_CRITICAL: float = 75.0
    THRESHOLD_MODERATE: float = 25.0

    # --- Event State Hysteresis & Debounce ---
    HYSTERESIS_DOWNGRADE_BUFFER: float = 4.0   # Must drop 4 points below threshold to de-escalate
    DEBOUNCE_CONFIRMATION_STEPS: int = 1      # Consecutive evaluations required

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
