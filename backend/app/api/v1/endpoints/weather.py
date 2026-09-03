from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db
from backend.app.models.weather import WeatherObservation
from backend.app.models.location import Location
from backend.app.schemas.weather import WeatherObservationResponse
from backend.app.services.ingestion import mock_data_source

router = APIRouter()


@router.get("/{location_id}", response_model=List[WeatherObservationResponse])
async def get_weather_observations(
    location_id: str,
    limit: int = Query(24, ge=1, le=168, description="Number of recent observations to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent meteorological and environmental observations for a location.
    If no observations exist, baseline data is automatically ingested.
    """
    # Verify location exists
    loc_res = await db.execute(select(Location).where(Location.id == location_id))
    location = loc_res.scalars().first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with ID '{location_id}' not found."
        )

    stmt = (
        select(WeatherObservation)
        .where(WeatherObservation.location_id == location_id)
        .order_by(WeatherObservation.timestamp.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    observations = list(result.scalars().all())

    if not observations:
        # Generate baseline observations
        fresh = await mock_data_source.fetch(location_id=location_id, limit=limit)
        for obs in fresh:
            db.add(obs)
        await db.commit()
        # Fetch newly inserted
        stmt = (
            select(WeatherObservation)
            .where(WeatherObservation.location_id == location_id)
            .order_by(WeatherObservation.timestamp.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        observations = list(result.scalars().all())

    return observations
