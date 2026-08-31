from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.providers.base import (
    WeatherDataSource,
    TerrainDataSource,
    HistoricalRiskSource,
    FreshnessStatus,
)
from backend.app.providers.weather.open_meteo import open_meteo_provider
from backend.app.providers.weather.mock import mock_weather_provider
from backend.app.providers.terrain.mock import mock_terrain_provider
from backend.app.providers.historical.mock import mock_historical_provider
from backend.app.providers.health import provider_health_registry
from backend.app.engine.base import (
    EnvironmentalState,
    TerrainProfile,
    HistoricalRiskContext,
    DataQualityReport,
    QualityStatus,
)
from backend.app.engine.data_validator import data_validator
from backend.app.core.cache import cache, CacheKeys
from backend.app.core.config import settings
from backend.app.core.logging import logger


@dataclass
class EnvironmentalStatePackage:
    location: Location
    observations: List[WeatherObservation]
    env_states: List[EnvironmentalState]
    latest_env: EnvironmentalState
    terrain: TerrainProfile
    historical: HistoricalRiskContext
    data_quality: DataQualityReport
    freshness_status: FreshnessStatus
    sources: List[str]
    is_live: bool


class EnvironmentalDataService:
    """
    Unified Ingestion & Environmental Collection Service.
    Enforces strict separation between data acquisition and assessment intelligence.
    Orchestrates live provider calls, caching, graceful degradation fallback,
    provenance tagging, quality verification, and terrain/historical context synthesis.
    """

    def __init__(
        self,
        live_weather: WeatherDataSource = open_meteo_provider,
        mock_weather: WeatherDataSource = mock_weather_provider,
        terrain_source: TerrainDataSource = mock_terrain_provider,
        historical_source: HistoricalRiskSource = mock_historical_provider
    ):
        self.live_weather = live_weather
        self.mock_weather = mock_weather
        self.terrain_source = terrain_source
        self.historical_source = historical_source
        self.validator = data_validator

    def evaluate_freshness(self, obs_time: datetime) -> FreshnessStatus:
        """Evaluates observational age against configurable freshness boundaries."""
        if obs_time.tzinfo is None:
            obs_time = obs_time.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age_minutes = (now - obs_time).total_seconds() / 60.0

        if age_minutes <= settings.DATA_FRESHNESS_WEATHER_MINUTES:
            return FreshnessStatus.FRESH
        elif age_minutes <= settings.DATA_FRESHNESS_SOIL_MOISTURE_MINUTES:
            return FreshnessStatus.AGING
        else:
            return FreshnessStatus.STALE

    async def collect_weather_observations(
        self,
        session: AsyncSession,
        location: Location,
        force_fresh: bool = False
    ) -> Tuple[List[WeatherObservation], str, bool]:
        """
        Retrieves weather telemetry with resilient multi-tier fallback:
        Tier 1: In-memory Cache (if not force_fresh)
        Tier 2: Database existing observations (if not force_fresh and DB has records)
        Tier 3: Live Provider (Open-Meteo) if DATA_MODE == 'LIVE'
        Tier 4: Simulation Fallback (Mock Provider)
        Returns: (observations, source_name, is_live)
        """
        cache_key = CacheKeys.weather_live(location.id)
        is_live = settings.DATA_MODE == "LIVE"

        # Tier 1 & Tier 2: Check Cache and DB when not forcing a fresh fetch
        if not force_fresh:
            # 1. Cache
            cached_data = await cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache HIT for weather observations at {location.name}")
                provider_health_registry.record_success("cache-subsystem", 0.2)
                obs_list = [WeatherObservation(**item) for item in cached_data]
                return obs_list, obs_list[-1].source if obs_list else "CACHED", is_live

            # 2. Database existing observations (e.g. from prior runs or scenario injections)
            db_stmt = (
                select(WeatherObservation)
                .where(WeatherObservation.location_id == location.id)
                .order_by(WeatherObservation.timestamp.asc())
            )
            db_res = await session.execute(db_stmt)
            db_obs = list(db_res.scalars().all())

            if db_obs and len(db_obs) >= 6:
                source_name = db_obs[-1].source or "DATABASE"
                return db_obs, source_name, (source_name == "OPEN_METEO")

        # Tier 3: Query Live Provider if in LIVE mode
        if is_live:
            try:
                logger.info(f"Querying live Open-Meteo provider for {location.name} ({location.latitude}, {location.longitude})")
                obs = await self.live_weather.get_observations(location, limit=24)
                if obs:
                    serializable = [
                        {
                            "location_id": o.location_id,
                            "timestamp": o.timestamp,
                            "temperature": o.temperature,
                            "humidity": o.humidity,
                            "pressure": o.pressure,
                            "wind_speed": o.wind_speed,
                            "wind_direction": o.wind_direction,
                            "rainfall_1h": o.rainfall_1h,
                            "rainfall_6h": o.rainfall_6h,
                            "rainfall_24h": o.rainfall_24h,
                            "soil_moisture": o.soil_moisture,
                            "source": o.source,
                            "source_version": o.source_version,
                            "freshness_status": self.evaluate_freshness(o.timestamp).value
                        }
                        for o in obs
                    ]
                    await cache.set(cache_key, serializable, ttl_seconds=settings.WEATHER_CACHE_TTL_SECONDS)
                    return obs, self.live_weather.provider_name, True

            except Exception as err:
                logger.warning(f"Live provider failed for {location.name} ({err}). Engaging graceful fallback...")

        # Tier 4: Fallback to Deterministic Simulation
        logger.info(f"Fallback to simulation weather provider for {location.name}")
        sim_obs = await self.mock_weather.get_observations(location, limit=24)
        return sim_obs, self.mock_weather.provider_name, False

    async def collect_environmental_package(
        self,
        session: AsyncSession,
        location: Location,
        force_fresh: bool = False
    ) -> EnvironmentalStatePackage:
        """
        Collects, validates, and synthesizes full multi-source environmental package for a station.
        """
        # 1. Collect Weather Observations
        observations, weather_source, is_live = await self.collect_weather_observations(
            session=session,
            location=location,
            force_fresh=force_fresh
        )

        # 2. Tag Freshness & Provenance on Observations
        now_utc = datetime.now(timezone.utc)
        for o in observations:
            freshness = self.evaluate_freshness(o.timestamp)
            o.freshness_status = freshness.value
            o.retrieved_at = now_utc

        # 3. Persist new observations to DB if missing
        for obs in observations:
            check_stmt = select(WeatherObservation.id).where(
                and_(
                    WeatherObservation.location_id == location.id,
                    WeatherObservation.timestamp == obs.timestamp
                )
            )
            exists = (await session.execute(check_stmt)).scalars().first()
            if not exists:
                session.add(obs)
        await session.flush()

        # 4. Collect Terrain Profile
        terrain_profile = await self.terrain_source.get_terrain_profile(location)

        # 5. Collect Historical Susceptibility Context
        historical_context = await self.historical_source.get_historical_context(location)

        # 6. Validate & Normalize into intermediate EnvironmentalState
        env_states, quality_report = self.validator.validate_series(observations)
        latest_env = env_states[-1] if env_states else EnvironmentalState(location_id=location.id, timestamp=now_utc)

        # Active Sources List
        sources = [
            weather_source,
            self.terrain_source.provider_name,
            self.historical_source.provider_name,
        ]

        latest_freshness = self.evaluate_freshness(latest_env.timestamp)

        return EnvironmentalStatePackage(
            location=location,
            observations=observations,
            env_states=env_states,
            latest_env=latest_env,
            terrain=terrain_profile,
            historical=historical_context,
            data_quality=quality_report,
            freshness_status=latest_freshness,
            sources=sources,
            is_live=is_live
        )


environmental_data_service = EnvironmentalDataService()
