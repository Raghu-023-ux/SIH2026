from abc import ABC, abstractmethod
from backend.app.models.location import Location
from backend.app.engine.base import TerrainProfile


class TerrainDataSource(ABC):
    """Abstract interface for DEM and topographical data providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def get_terrain_profile(self, location: Location) -> TerrainProfile:
        pass
