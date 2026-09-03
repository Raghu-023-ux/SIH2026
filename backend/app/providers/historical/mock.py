from typing import Dict
from backend.app.models.location import Location
from backend.app.engine.base import HistoricalRiskContext
from backend.app.providers.historical.base import HistoricalRiskSource
from backend.app.providers.health import provider_health_registry


class MockHistoricalProvider(HistoricalRiskSource):
    """
    Deterministic historical susceptibility provider.
    NOTE: Prototype baseline dataset. Values are simulated for demonstration.
    """

    def __init__(self):
        self._historical_events: Dict[str, int] = {
            "NER-SIK-GANGTOK-01": 18,
            "NER-MEG-SHILLONG-01": 9,
            "NER-MIZ-AIZAWL-01": 22,
            "NER-NAG-KOHIMA-01": 16,
            "NER-ARU-ITANAGAR-01": 7,
            "NER-ASM-HAFLONG-01": 14,
        }

    @property
    def provider_name(self) -> str:
        return "MOCK_HISTORICAL_BASELINE"

    async def get_historical_context(self, location: Location) -> HistoricalRiskContext:
        events = self._historical_events.get(location.id, 8)
        susc = location.susceptibility_score if location.susceptibility_score is not None else 0.65
        monsoon_vuln = min(1.0, max(0.2, (susc * 0.7) + min(0.3, events / 40.0)))

        provider_health_registry.record_success("historical-demo", 0.5)

        return HistoricalRiskContext(
            location_id=location.id,
            historical_landslide_events=events,
            susceptibility_score=susc,
            data_period_years=10,
            monsoon_vulnerability_index=round(monsoon_vuln, 3)
        )


mock_historical_provider = MockHistoricalProvider()
