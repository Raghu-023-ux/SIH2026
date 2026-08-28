from abc import ABC, abstractmethod
from backend.app.models.location import Location
from backend.app.engine.base import HistoricalRiskContext


class HistoricalRiskSource(ABC):
    """Abstract interface for historical landslide frequency & susceptibility data."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def get_historical_context(self, location: Location) -> HistoricalRiskContext:
        pass
