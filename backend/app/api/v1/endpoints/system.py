from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter
from backend.app.providers.health import provider_health_registry
from backend.app.core.config import settings

router = APIRouter()


@router.get("/data-sources")
async def get_data_sources_health() -> Dict[str, Any]:
    """
    Returns runtime operational health, latency metrics, and data provenance
    for all registered environmental, DEM terrain, and historical data providers.
    """
    providers = [p.to_dict() for p in provider_health_registry.get_all_health()]

    return {
        "data_mode": settings.DATA_MODE,
        "engine_version": settings.ENGINE_VERSION,
        "server_time": datetime.now(timezone.utc).isoformat(),
        "providers": providers,
        "caching": {
            "status": "OPERATIONAL",
            "type": "IN_MEMORY_TTL",
            "ttl_seconds": settings.WEATHER_CACHE_TTL_SECONDS
        },
        "freshness_policy": {
            "weather_max_minutes": settings.DATA_FRESHNESS_WEATHER_MINUTES,
            "soil_moisture_max_minutes": settings.DATA_FRESHNESS_SOIL_MOISTURE_MINUTES,
        }
    }
