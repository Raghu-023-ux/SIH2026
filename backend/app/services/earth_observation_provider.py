from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
import time
import httpx
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.cache import cache, CacheKeys
from backend.app.providers.health import provider_health_registry
from backend.app.models.earth_observation import EarthObservation
from backend.app.models.location import Location
from backend.app.schemas.earth_observation import (
    EarthObservationSearchRequest,
    EarthObservationItemResponse,
    EarthObservationSearchResponse,
    BhoonidhiStatusResponse,
)

# Supported satellite collections from ISRO/NRSC Bhoonidhi archive
SUPPORTED_BHOONIDHI_COLLECTIONS = [
    "Sentinel-1A_SAR-IW_GRD",
    "Sentinel-1A_SAR-IW_SLC",
    "CartoSat-1_PAN_CartoDEM_30m",
    "NISAR_SSAR_RSLC",
    "NISAR_SSAR_GSLC",
    "NISAR_SSAR_GCOV",
    "NISAR_SSAR_RUNW",
    "NISAR_SSAR_GUNW",
]


class EarthObservationProvider(ABC):
    """
    Abstract base provider for Earth Observation & Satellite Data.
    Standard interface for catalogue search, scene metadata retrieval,
    and satellite acquisition indexing.
    """

    @abstractmethod
    async def authenticate(self) -> bool:
        pass

    @abstractmethod
    async def search(
        self,
        request: EarthObservationSearchRequest,
        db_session: Optional[AsyncSession] = None
    ) -> EarthObservationSearchResponse:
        pass

    @abstractmethod
    async def get_acquisitions_for_location(
        self,
        location_id: str,
        location: Optional[Location] = None,
        limit: int = 5,
        db_session: Optional[AsyncSession] = None
    ) -> List[EarthObservationItemResponse]:
        pass

    @abstractmethod
    def get_health_status(self) -> BhoonidhiStatusResponse:
        pass


class MockEarthObservationProvider(EarthObservationProvider):
    """
    Deterministic Mock Earth Observation Provider for local development & demonstration.
    Generates realistic Sentinel-1A SAR, CartoSat-1 CartoDEM 30m, and NISAR acquisition metadata
    for the North Eastern Region monitoring network.
    """

    def __init__(self):
        self._auth_valid = True

    async def authenticate(self) -> bool:
        return True

    def get_health_status(self) -> BhoonidhiStatusResponse:
        return BhoonidhiStatusResponse(
            provider_name="Bhoonidhi (ISRO / NRSC Open Data Portal) - Local Simulation",
            status="MOCK_MODE",
            configured=True,
            api_endpoint=settings.BHOONIDHI_API_URL,
            token_valid=True,
            supported_collections=SUPPORTED_BHOONIDHI_COLLECTIONS,
            rate_limits={
                "auth_per_hour_limit": 20,
                "search_per_second_limit": 3,
                "status": "OPERATIONAL_SIMULATED",
            },
            latest_synced_scene="S1A_IW_GRDH_1SDV_20260828T001522_055410_06C4E1_NER",
            note="Local deterministic satellite metadata provider active. Real Earth-Observation binaries not queried.",
        )

    async def search(
        self,
        request: EarthObservationSearchRequest,
        db_session: Optional[AsyncSession] = None
    ) -> EarthObservationSearchResponse:
        now = datetime.now(timezone.utc)
        results: List[EarthObservationItemResponse] = []

        coll = request.collection or "Sentinel-1A_SAR-IW_GRD"
        loc_id = request.location_id or "NER-SIK-GANGTOK-01"

        # Generate realistic satellite passes
        for i in range(min(request.limit, 6)):
            t_acq = now - timedelta(days=i * 2, hours=3 + i)
            p_id = f"S1A_IW_GRDH_1SDV_{t_acq.strftime('%Y%m%d')}_{loc_id}_{i+1:02d}"

            results.append(
                EarthObservationItemResponse(
                    id=f"eo-mock-{loc_id}-{i+1}",
                    location_id=loc_id,
                    collection=coll,
                    product_id=p_id,
                    timestamp=t_acq,
                    acquisition_start=t_acq - timedelta(seconds=25),
                    acquisition_end=t_acq,
                    platform="Sentinel-1A" if "Sentinel" in coll else ("NISAR" if "NISAR" in coll else "CartoSat-1"),
                    instrument="C-SAR" if "Sentinel" in coll else ("L-SAR" if "NISAR" in coll else "PAN"),
                    processing_level="Level-1 GRD" if "GRD" in coll else ("Level-3 DEM" if "CartoDEM" in coll else "Level-2 GCOV"),
                    bbox=[88.50, 27.20, 88.75, 27.45],
                    available_online=True,
                    source="BHOONIDHI_ISRO_MOCK",
                    metadata={
                        "orbit_pass": "DESCENDING" if i % 2 == 0 else "ASCENDING",
                        "polarization": "VV+VH",
                        "resolution_m": 10.0 if "Sentinel" in coll else 30.0,
                        "relative_orbit": 128 + i,
                        "cloud_cover_pct": 0.0,  # SAR penetrates clouds
                        "product_status": "ONLINE",
                        "sensor_mode": "IW (Interferometric Wide Swath)",
                    },
                    created_at=now,
                )
            )

        return EarthObservationSearchResponse(
            total_results=len(results),
            provider="MockEarthObservationProvider",
            provider_status="MOCK_MODE",
            cached=False,
            results=results,
        )

    async def get_acquisitions_for_location(
        self,
        location_id: str,
        location: Optional[Location] = None,
        limit: int = 5,
        db_session: Optional[AsyncSession] = None
    ) -> List[EarthObservationItemResponse]:
        req = EarthObservationSearchRequest(location_id=location_id, limit=limit)
        res = await self.search(req, db_session=db_session)
        return res.results


class BhoonidhiProvider(EarthObservationProvider):
    """
    Live Bhoonidhi (ISRO / NRSC) Open Data Portal API Provider.
    Implements:
    - OAuth2 Bearer Token Authentication (/auth/token) with Redis token reuse and rate limit awareness (20 auth/hr)
    - STAC Catalogue Search (/data/search) with rate-limiting (3 req/sec) and Redis TTL caching
    - Database persistence of discovered satellite metadata in PostgreSQL
    - Explicit unconfigured detection: Never fakes a green status if credentials are missing
    """

    def __init__(self):
        self.api_url = settings.BHOONIDHI_API_URL.rstrip("/")
        self.user_id = settings.BHOONIDHI_USER_ID
        self.password = settings.BHOONIDHI_PASSWORD
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._last_auth_attempt: Optional[datetime] = None
        self._auth_count_hourly: int = 0
        self._last_request_time: float = 0.0
        self.mock_fallback = MockEarthObservationProvider()

    def is_configured(self) -> bool:
        return bool(self.user_id and self.password)

    def get_health_status(self) -> BhoonidhiStatusResponse:
        configured = self.is_configured()
        token_valid = bool(
            self._access_token
            and self._token_expiry
            and self._token_expiry > datetime.now(timezone.utc)
        )

        if not configured:
            status_label = "NOT_CONFIGURED"
            note = "Bhoonidhi credentials (BHOONIDHI_USER_ID, BHOONIDHI_PASSWORD) not provided in environment."
        elif token_valid:
            status_label = "AVAILABLE"
            note = "Authenticated with ISRO / NRSC Bhoonidhi Open Data Gateway."
        else:
            status_label = "AVAILABLE"
            note = "Configured. Token will authenticate on next remote sensing query."

        return BhoonidhiStatusResponse(
            provider_name="Bhoonidhi (ISRO / NRSC Open Data Portal)",
            status=status_label,
            configured=configured,
            api_endpoint=self.api_url,
            token_valid=token_valid,
            supported_collections=SUPPORTED_BHOONIDHI_COLLECTIONS,
            rate_limits={
                "auth_per_hour_limit": 20,
                "search_per_second_limit": 3,
                "current_hour_auths": self._auth_count_hourly,
            },
            latest_synced_scene="S1A_IW_GRDH_1SDV_NER_CATALOGUE",
            note=note,
        )

    async def authenticate(self) -> bool:
        if not self.is_configured():
            logger.warning("Bhoonidhi authenticate called without credentials.")
            return False

        now = datetime.now(timezone.utc)

        # 1. In-memory check
        if (
            self._access_token
            and self._token_expiry
            and self._token_expiry > now + timedelta(minutes=5)
        ):
            return True

        # 2. Redis Token Cache Check
        token_cache_key = CacheKeys.bhoonidhi_auth_token(self.user_id or "default")
        cached_token = await cache.get(token_cache_key)
        if cached_token and isinstance(cached_token, dict):
            token_str = cached_token.get("token")
            exp_str = cached_token.get("expires_at")
            if token_str and exp_str:
                exp_dt = datetime.fromisoformat(exp_str)
                if exp_dt > now + timedelta(minutes=5):
                    self._access_token = token_str
                    self._token_expiry = exp_dt
                    return True

        # 3. Check rate limit: 20 auths per hour
        if self._last_auth_attempt and (now - self._last_auth_attempt).total_seconds() < 3600:
            if self._auth_count_hourly >= 20:
                logger.error("Bhoonidhi authentication rate limit reached (20 auths/hr).")
                return False
        else:
            self._auth_count_hourly = 0

        self._auth_count_hourly += 1
        self._last_auth_attempt = now

        start_t = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(
                    f"{self.api_url}/auth/token",
                    json={"username": self.user_id, "password": self.password},
                )
                latency_ms = (time.perf_counter() - start_t) * 1000.0

                if res.status_code == 200:
                    data = res.json()
                    self._access_token = data.get("access_token")
                    expires_in = data.get("expires_in", 3600)
                    self._token_expiry = now + timedelta(seconds=expires_in)

                    # Persist in Redis with TTL
                    await cache.set(
                        token_cache_key,
                        {
                            "token": self._access_token,
                            "expires_at": self._token_expiry.isoformat(),
                        },
                        ttl_seconds=max(60, expires_in - 300)
                    )
                    provider_health_registry.record_success("bhoonidhi-auth", latency_ms)
                    logger.info("Successfully authenticated with ISRO Bhoonidhi.")
                    return True
                else:
                    logger.error(f"Bhoonidhi authentication failed: HTTP {res.status_code} - {res.text}")
                    provider_health_registry.record_failure("bhoonidhi-auth", f"HTTP {res.status_code}")
                    return False
        except Exception as ex:
            logger.error(f"Bhoonidhi authentication exception: {ex}")
            provider_health_registry.record_failure("bhoonidhi-auth", str(ex))
            return False

    async def search(
        self,
        request: EarthObservationSearchRequest,
        db_session: Optional[AsyncSession] = None
    ) -> EarthObservationSearchResponse:
        if not self.is_configured():
            return EarthObservationSearchResponse(
                total_results=0,
                provider="BhoonidhiProvider",
                provider_status="NOT_CONFIGURED",
                cached=False,
                results=[],
            )

        # 1. Cache key lookup via unified Redis cache
        cache_key = CacheKeys.bhoonidhi_scenes(
            collection=request.collection or "default",
            location_id=request.location_id or "all",
            limit=request.limit or 10
        )
        cached_data = await cache.get(cache_key)
        if cached_data:
            try:
                cached_resp = EarthObservationSearchResponse(**cached_data)
                cached_resp.cached = True
                return cached_resp
            except Exception:
                pass

        # 2. Rate limit protection: 3 requests per second
        curr_time = time.time()
        elapsed = curr_time - self._last_request_time
        if elapsed < 0.35:
            await time.sleep(0.35 - elapsed)
        self._last_request_time = time.time()

        auth_ok = await self.authenticate()
        if not auth_ok:
            return EarthObservationSearchResponse(
                total_results=0,
                provider="BhoonidhiProvider",
                provider_status="AUTH_FAILED",
                cached=False,
                results=[],
            )

        start_t = time.perf_counter()
        now = datetime.now(timezone.utc)
        try:
            headers = {"Authorization": f"Bearer {self._access_token}"}
            payload: Dict[str, Any] = {
                "collections": [request.collection] if request.collection else SUPPORTED_BHOONIDHI_COLLECTIONS[:3],
                "limit": request.limit,
            }
            if request.bbox:
                payload["bbox"] = request.bbox

            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{self.api_url}/data/search",
                    headers=headers,
                    json=payload,
                )
                latency_ms = (time.perf_counter() - start_t) * 1000.0

                if res.status_code == 200:
                    data = res.json()
                    features = data.get("features", [])
                    results = []
                    for f in features:
                        props = f.get("properties", {})
                        item = EarthObservationItemResponse(
                            id=str(f.get("id", f"eo-{time.time()}")),
                            location_id=request.location_id,
                            collection=props.get("collection", request.collection or "Sentinel-1A_SAR-IW_GRD"),
                            product_id=f.get("id", "S1A_GRD"),
                            timestamp=datetime.fromisoformat(props.get("datetime", now.isoformat())),
                            platform=props.get("platform", "Sentinel-1A"),
                            instrument=props.get("instrument", "C-SAR"),
                            processing_level=props.get("processing_level", "Level-1 GRD"),
                            bbox=f.get("bbox"),
                            available_online=props.get("available_online", True),
                            source="BHOONIDHI_ISRO",
                            metadata=props,
                            created_at=now,
                        )
                        results.append(item)

                        # Persist to PostgreSQL if session is provided
                        if db_session:
                            try:
                                eo_record = EarthObservation(
                                    id=item.id,
                                    location_id=item.location_id,
                                    collection=item.collection,
                                    product_id=item.product_id,
                                    timestamp=item.timestamp,
                                    platform=item.platform,
                                    instrument=item.instrument,
                                    processing_level=item.processing_level,
                                    bbox_json=item.bbox,
                                    available_online=item.available_online,
                                    source=item.source,
                                    metadata_json=item.metadata,
                                    created_at=now,
                                )
                                db_session.add(eo_record)
                            except Exception:
                                pass

                    if db_session:
                        try:
                            await db_session.commit()
                        except Exception:
                            pass

                    response = EarthObservationSearchResponse(
                        total_results=len(results),
                        provider="BhoonidhiProvider",
                        provider_status="AVAILABLE",
                        cached=False,
                        results=results,
                    )
                    await cache.set(
                        cache_key,
                        response.model_dump(mode="json"),
                        ttl_seconds=settings.BHOONIDHI_CACHE_TTL_SECONDS
                    )
                    provider_health_registry.record_success("bhoonidhi-stac", latency_ms)
                    return response
                else:
                    logger.error(f"Bhoonidhi search failed: HTTP {res.status_code} - {res.text}")
                    provider_health_registry.record_failure("bhoonidhi-stac", f"HTTP {res.status_code}")
                    return EarthObservationSearchResponse(
                        total_results=0,
                        provider="BhoonidhiProvider",
                        provider_status="API_ERROR",
                        cached=False,
                        results=[],
                    )
        except Exception as ex:
            logger.error(f"Bhoonidhi search exception: {ex}")
            provider_health_registry.record_failure("bhoonidhi-stac", str(ex))
            return EarthObservationSearchResponse(
                total_results=0,
                provider="BhoonidhiProvider",
                provider_status="UNAVAILABLE",
                cached=False,
                results=[],
            )

    async def get_acquisitions_for_location(
        self,
        location_id: str,
        location: Optional[Location] = None,
        limit: int = 5,
        db_session: Optional[AsyncSession] = None
    ) -> List[EarthObservationItemResponse]:
        bbox = None
        if location and location.latitude and location.longitude:
            lat, lon = location.latitude, location.longitude
            bbox = [round(lon - 0.2, 3), round(lat - 0.2, 3), round(lon + 0.2, 3), round(lat + 0.2, 3)]

        req = EarthObservationSearchRequest(
            location_id=location_id,
            bbox=bbox,
            limit=limit
        )
        res = await self.search(req, db_session=db_session)
        return res.results


# Global provider factory instance
_earth_observation_provider: Optional[EarthObservationProvider] = None


def get_earth_observation_provider() -> EarthObservationProvider:
    global _earth_observation_provider
    if _earth_observation_provider is None:
        if (
            settings.BHOONIDHI_PROVIDER_MODE == "LIVE"
            and settings.BHOONIDHI_USER_ID
            and settings.BHOONIDHI_PASSWORD
        ):
            _earth_observation_provider = BhoonidhiProvider()
        else:
            _earth_observation_provider = MockEarthObservationProvider()
    return _earth_observation_provider
