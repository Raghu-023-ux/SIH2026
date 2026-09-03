from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.engine.base import TerrainProfile, HistoricalRiskContext


class FreshnessStatus(str, Enum):
    FRESH = "FRESH"
    AGING = "AGING"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class ProviderStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    SIMULATED = "SIMULATED"


@dataclass
class ProviderHealth:
    name: str
    status: ProviderStatus
    source_type: str  # "LIVE_API", "DEMO_GIS", "DEMO_HISTORICAL", "SIMULATION"
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_latency_ms: Optional[float] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "source_type": self.source_type,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "consecutive_failures": self.consecutive_failures,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "last_latency_ms": round(self.last_latency_ms, 1) if self.last_latency_ms else None,
            "error_message": self.error_message,
        }


class WeatherDataSource(ABC):
    """Abstract interface for weather and meteorological data providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the weather provider (e.g. 'OPEN_METEO', 'MOCK')."""
        pass

    @property
    @abstractmethod
    def provider_version(self) -> str:
        """Version of the provider adapter."""
        pass

    @abstractmethod
    async def get_observations(
        self,
        location: Location,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 24
    ) -> List[WeatherObservation]:
        """Fetch chronological weather observations for a given location."""
        pass


class TerrainDataSource(ABC):
    """Abstract interface for geomorphological, slope, and elevation data providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def get_terrain_profile(self, location: Location) -> TerrainProfile:
        pass


class HistoricalRiskSource(ABC):
    """Abstract interface for historical landslide frequency & susceptibility data."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def get_historical_context(self, location: Location) -> HistoricalRiskContext:
        pass
