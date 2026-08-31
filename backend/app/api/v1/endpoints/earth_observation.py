from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from backend.app.api.deps import get_db
from backend.app.services.location_service import LocationService
from backend.app.services.earth_observation_provider import get_earth_observation_provider
from backend.app.schemas.earth_observation import (
    EarthObservationSearchRequest,
    EarthObservationItemResponse,
    EarthObservationSearchResponse,
    BhoonidhiStatusResponse,
)

router = APIRouter()


@router.get("/status", response_model=BhoonidhiStatusResponse)
def get_bhoonidhi_status():
    """
    Returns live connectivity status, token validity, rate-limit statistics,
    and supported collection archive for ISRO / NRSC Bhoonidhi Open Data Gateway.
    """
    provider = get_earth_observation_provider()
    return provider.get_health_status()


@router.post("/search", response_model=EarthObservationSearchResponse)
async def search_earth_observations(
    req: EarthObservationSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Queries Earth Observation metadata catalog across Sentinel-1 SAR,
    CartoSat-1 CartoDEM 30m, and NISAR radar products based on STAC specifications.
    """
    provider = get_earth_observation_provider()
    return await provider.search(req, db_session=db)


@router.get("/location/{location_id}/acquisitions", response_model=List[EarthObservationItemResponse])
async def get_location_satellite_acquisitions(
    location_id: str,
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves recent Earth Observation satellite scenes covering a specific monitored station.
    """
    location = await LocationService.get_location_by_id(db, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location '{location_id}' not found."
        )

    provider = get_earth_observation_provider()
    return await provider.get_acquisitions_for_location(location_id, location=location, limit=limit, db_session=db)

