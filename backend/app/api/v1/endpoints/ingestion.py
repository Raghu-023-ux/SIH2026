from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db
from backend.app.models.location import Location
from backend.app.services.location_service import LocationService
from backend.app.services.environmental_data_service import environmental_data_service
from backend.app.engine.pipeline import disaster_engine
from backend.app.providers.health import provider_health_registry
from backend.app.schemas.ingestion import (
    IngestionResponse,
    BatchIngestionResponse,
    IngestionStatusResponse,
    DataModeToggleRequest,
    DataModeResponse,
)
from backend.app.schemas.engine import EngineAssessmentResponse
from backend.app.core.config import settings
from backend.app.core.logging import logger

router = APIRouter()


@router.post("/mode", response_model=DataModeResponse)
async def toggle_data_mode(request: DataModeToggleRequest):
    """
    Toggles global ingestion data mode between 'LIVE' (Open-Meteo) and 'SIMULATION'.
    """
    mode_upper = request.mode.upper()
    if mode_upper not in ("LIVE", "SIMULATION"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mode must be either 'LIVE' or 'SIMULATION'."
        )

    settings.DATA_MODE = mode_upper
    logger.info(f"Operational Data Mode switched to: {settings.DATA_MODE}")

    return DataModeResponse(
        current_mode=settings.DATA_MODE,
        message=f"System data mode successfully switched to {settings.DATA_MODE}.",
        timestamp=datetime.now(timezone.utc)
    )


@router.get("/status", response_model=IngestionStatusResponse)
async def get_ingestion_status(db: AsyncSession = Depends(get_db)):
    """
    Returns real-time status of data ingestion pipelines, active providers, and operational mode.
    """
    locations = await LocationService.get_all_locations(db)
    providers_health = [p.to_dict() for p in provider_health_registry.get_all_health()]

    return IngestionStatusResponse(
        data_mode=settings.DATA_MODE,
        engine_version=settings.ENGINE_VERSION,
        last_ingestion=datetime.now(timezone.utc),
        total_locations=len(locations),
        providers=providers_health,
        cache_status="ACTIVE (TTL: 600s)"
    )


@router.post("/{location_id}", response_model=IngestionResponse)
async def ingest_location_data(
    location_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers immediate on-demand ingestion for a specific monitoring station,
    normalizes and validates incoming telemetry, executes the analytical engine,
    and returns the resulting hazard assessment.
    """
    location = await LocationService.get_location_by_id(db, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with ID '{location_id}' not found."
        )

    try:
        assessment_out, event, action = await disaster_engine.evaluate_location(
            session=db,
            location=location,
            force_fresh=True
        )
        await db.commit()

        formatted_assessment = disaster_engine.format_assessment_response(location, assessment_out, event)
        weather_source = assessment_out.data_quality.quality_notes or "OPEN_METEO"

        return IngestionResponse(
            location_id=location.id,
            location_name=location.name,
            status="SUCCESS",
            data_mode=settings.DATA_MODE,
            source=settings.DATA_MODE,
            freshness=assessment_out.data_quality.status.value,
            assessment=formatted_assessment,
            timestamp=datetime.now(timezone.utc),
            message=f"Ingestion succeeded. Risk evaluated at {assessment_out.risk_score:.1f}/100 ({assessment_out.risk_level.value}). Event lifecycle: {action.upper()}."
        )
    except Exception as err:
        logger.error(f"Ingestion error for location {location_id}: {err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data ingestion failed for station '{location.name}': {str(err)}"
        )


@router.post("/batch", response_model=BatchIngestionResponse)
async def ingest_all_locations_batch(db: AsyncSession = Depends(get_db)):
    """
    Batch ingests environmental data and runs pipeline assessments across all monitored stations.
    """
    locations = await LocationService.get_all_locations(db)
    if not locations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No locations registered in database."
        )

    assessments: List[EngineAssessmentResponse] = []
    success_count = 0
    fail_count = 0
    highest_score = 0.0
    highest_level = "LOW"
    active_events = 0

    for loc in locations:
        try:
            assessment_out, event, _ = await disaster_engine.evaluate_location(
                session=db,
                location=loc,
                force_fresh=True
            )
            formatted = disaster_engine.format_assessment_response(loc, assessment_out, event)
            assessments.append(formatted)
            success_count += 1

            if assessment_out.risk_score > highest_score:
                highest_score = assessment_out.risk_score
                highest_level = assessment_out.risk_level.value

            if event and event.status != "RESOLVED":
                active_events += 1

        except Exception as err:
            logger.warning(f"Batch ingestion failed for {loc.name}: {err}")
            fail_count += 1

    await db.commit()

    return BatchIngestionResponse(
        executed_at=datetime.now(timezone.utc),
        data_mode=settings.DATA_MODE,
        locations_processed=len(locations),
        successful_count=success_count,
        failed_count=fail_count,
        active_events_count=active_events,
        highest_risk_score=round(highest_score, 1),
        highest_risk_level=highest_level,
        assessments=assessments
    )
