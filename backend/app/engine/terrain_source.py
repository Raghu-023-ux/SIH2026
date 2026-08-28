from abc import ABC, abstractmethod
from typing import Optional, Dict
from backend.app.models.location import Location
from backend.app.engine.base import TerrainProfile
from backend.app.core.logging import logger


class TerrainDataSource(ABC):
    """Abstract interface for retrieving topographical, slope, and elevation data."""

    @abstractmethod
    async def get_terrain_profile(self, location: Location) -> TerrainProfile:
        """Fetch terrain and geomorphological metrics for a given station/location."""
        pass


class MockTerrainDataSource(TerrainDataSource):
    """
    Deterministic terrain provider for North Eastern Region monitoring stations.
    NOTE: Prototype topography data source for MVP demonstration.
    """

    def __init__(self):
        # Known baseline terrain characteristics for Himalayan/NER corridors
        self._aspect_profiles: Dict[str, str] = {
            "NER-SIK-GANGTOK-01": "SOUTH_EAST",
            "NER-MEG-SHILLONG-01": "SOUTH_WEST",
            "NER-MIZ-AIZAWL-01": "WEST",
            "NER-NAG-KOHIMA-01": "EAST",
            "NER-ARU-ITANAGAR-01": "SOUTH",
            "NER-ASM-HAFLONG-01": "SOUTH_EAST",
        }

    async def get_terrain_profile(self, location: Location) -> TerrainProfile:
        slope = location.slope_angle if location.slope_angle is not None else 30.0
        elev = location.elevation if location.elevation is not None else 1200.0
        aspect = self._aspect_profiles.get(location.id, "SOUTH_EAST")

        # Slope score: steepness > 35° represents severe Himalayan escarpments
        slope_factor = min(1.0, slope / 45.0)
        elev_factor = min(1.0, elev / 2500.0)

        # Composite terrain susceptibility (0.0 to 1.0)
        terrain_susc = round((slope_factor * 0.7) + (elev_factor * 0.3), 3)

        return TerrainProfile(
            location_id=location.id,
            elevation=elev,
            slope_angle=slope,
            aspect=aspect,
            terrain_susceptibility=terrain_susc,
            geology_type="Himalayan Phyllite & Weathered Schist"
        )


terrain_data_source = MockTerrainDataSource()
