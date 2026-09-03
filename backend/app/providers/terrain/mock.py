from typing import Dict
from backend.app.models.location import Location
from backend.app.engine.base import TerrainProfile
from backend.app.providers.terrain.base import TerrainDataSource
from backend.app.providers.health import provider_health_registry


class MockTerrainProvider(TerrainDataSource):
    """
    Deterministic terrain provider for North Eastern Region monitoring stations.
    NOTE: Prototype topography data adapter for demonstration.
    """

    def __init__(self):
        self._aspect_profiles: Dict[str, str] = {
            "NER-SIK-GANGTOK-01": "SOUTH_EAST",
            "NER-MEG-SHILLONG-01": "SOUTH_WEST",
            "NER-MIZ-AIZAWL-01": "WEST",
            "NER-NAG-KOHIMA-01": "EAST",
            "NER-ARU-ITANAGAR-01": "SOUTH",
            "NER-ASM-HAFLONG-01": "SOUTH_EAST",
        }

    @property
    def provider_name(self) -> str:
        return "MOCK_TERRAIN_GIS"

    async def get_terrain_profile(self, location: Location) -> TerrainProfile:
        slope = location.slope_angle if location.slope_angle is not None else 30.0
        elev = location.elevation if location.elevation is not None else 1200.0
        aspect = self._aspect_profiles.get(location.id, "SOUTH_EAST")

        slope_factor = min(1.0, slope / 45.0)
        elev_factor = min(1.0, elev / 2500.0)
        terrain_susc = round((slope_factor * 0.7) + (elev_factor * 0.3), 3)

        provider_health_registry.record_success("terrain-demo", 0.5)

        return TerrainProfile(
            location_id=location.id,
            elevation=elev,
            slope_angle=slope,
            aspect=aspect,
            terrain_susceptibility=terrain_susc,
            geology_type="Himalayan Phyllite & Weathered Schist"
        )


mock_terrain_provider = MockTerrainProvider()
