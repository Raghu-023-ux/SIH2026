"""
Cache facade and compatibility layer.
Re-exports the unified RedisService instance and Granular Cache Key builders.
"""

from typing import Optional, Any
from backend.app.core.redis import redis_service, RedisService, InMemoryTTLCache, rate_limiter

# Global singleton alias
cache: RedisService = redis_service


class CacheKeys:
    """Standardized Redis cache key generators across all external providers."""

    @staticmethod
    def weather_live(location_id: str) -> str:
        return f"weather:live:{location_id}"

    @staticmethod
    def weather_coords(lat: float, lon: float) -> str:
        return f"weather:coords:{lat:.4f}:{lon:.4f}"

    @staticmethod
    def weather_forecast(location_id: str) -> str:
        return f"weather:forecast:{location_id}"

    @staticmethod
    def bhoonidhi_scenes(collection: str, location_id: str, limit: int) -> str:
        return f"bhoonidhi:scenes:{collection}:{location_id}:{limit}"

    @staticmethod
    def terrain_static(location_id: str) -> str:
        return f"terrain:static:{location_id}"

    @staticmethod
    def historical_incident(incident_id: str) -> str:
        return f"historical:incident:{incident_id}"

    @staticmethod
    def ai_explanation(location_id: str, assessment_id: str, agent_type: str) -> str:
        return f"ai:explanation:{location_id}:{assessment_id}:{agent_type}"


__all__ = [
    "cache",
    "redis_service",
    "RedisService",
    "InMemoryTTLCache",
    "rate_limiter",
    "CacheKeys",
]
