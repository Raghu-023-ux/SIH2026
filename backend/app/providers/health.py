from datetime import datetime, timezone
from typing import Dict, List, Optional
from backend.app.providers.base import ProviderHealth, ProviderStatus
from backend.app.core.logging import logger


class ProviderHealthRegistry:
    """
    Tracks runtime operational health, latency, failure rates,
    and availability for all data providers.
    """

    def __init__(self):
        self._providers: Dict[str, ProviderHealth] = {
            "open-meteo": ProviderHealth(
                name="open-meteo",
                status=ProviderStatus.HEALTHY,
                source_type="LIVE_API",
                last_success=datetime.now(timezone.utc)
            ),
            "mock-weather": ProviderHealth(
                name="mock-weather",
                status=ProviderStatus.SIMULATED,
                source_type="SIMULATION",
                last_success=datetime.now(timezone.utc)
            ),
            "terrain-demo": ProviderHealth(
                name="terrain-demo",
                status=ProviderStatus.HEALTHY,
                source_type="DEMO_GIS",
                last_success=datetime.now(timezone.utc)
            ),
            "historical-demo": ProviderHealth(
                name="historical-demo",
                status=ProviderStatus.HEALTHY,
                source_type="DEMO_HISTORICAL",
                last_success=datetime.now(timezone.utc)
            ),
            "cache-subsystem": ProviderHealth(
                name="cache-subsystem",
                status=ProviderStatus.HEALTHY,
                source_type="IN_MEMORY_REDIS",
                last_success=datetime.now(timezone.utc)
            ),
        }

    def record_success(self, provider_name: str, latency_ms: float):
        if provider_name not in self._providers:
            self._providers[provider_name] = ProviderHealth(
                name=provider_name,
                status=ProviderStatus.HEALTHY,
                source_type="LIVE_API"
            )

        p = self._providers[provider_name]
        p.last_success = datetime.now(timezone.utc)
        p.consecutive_failures = 0
        p.total_requests += 1
        p.successful_requests += 1
        p.last_latency_ms = latency_ms
        p.status = ProviderStatus.HEALTHY
        p.error_message = None

    def record_failure(self, provider_name: str, error_message: str):
        if provider_name not in self._providers:
            self._providers[provider_name] = ProviderHealth(
                name=provider_name,
                status=ProviderStatus.DEGRADED,
                source_type="LIVE_API"
            )

        p = self._providers[provider_name]
        p.last_failure = datetime.now(timezone.utc)
        p.consecutive_failures += 1
        p.total_requests += 1
        p.failed_requests += 1
        p.error_message = error_message

        if p.consecutive_failures >= 3:
            p.status = ProviderStatus.OFFLINE
        else:
            p.status = ProviderStatus.DEGRADED

        logger.warning(f"Provider '{provider_name}' recorded failure: {error_message} (Consecutive: {p.consecutive_failures})")

    def get_provider_health(self, provider_name: str) -> Optional[ProviderHealth]:
        return self._providers.get(provider_name)

    def get_all_health(self) -> List[ProviderHealth]:
        return list(self._providers.values())


provider_health_registry = ProviderHealthRegistry()
