import time
from typing import Union, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db
from backend.app.models.location import Location
from backend.app.schemas.engine import (
    EngineRunRequest,
    EngineAssessmentResponse,
    MultiLocationEngineResponse
)
from backend.app.engine.pipeline import disaster_engine
from backend.app.engine.status import engine_status_tracker
from backend.app.core.redis import redis_service
from backend.app.core.logging import logger
from backend.app.services.location_service import LocationService

router = APIRouter()


@router.get("/status", response_model=Dict[str, Any])
async def get_engine_status():
    """
    Returns real-time engine operational health, last run timestamp,
    active event metrics, and background execution status.
    """
    return engine_status_tracker.get_status_payload()


@router.post("/run", response_model=Union[MultiLocationEngineResponse, EngineAssessmentResponse])
async def run_engine(
    request: EngineRunRequest = EngineRunRequest(),
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers an on-demand execution run of the Disaster Intelligence Engine.
    Executes full pipeline:
    1. Ingestion / Observation retrieval (Open-Meteo live)
    2. Anomaly Detection (Statistical rolling z-scores)
    3. Temporal Trend Analysis (Slopes & Persistence)
    4. Landslide Risk Modeling (Explainable weighted factors)
    5. Event Management (Deduplication, state updates, resolution)
    6. Returns structured risk assessment and factor breakdowns.
    """
    logger.info(f"Triggering on-demand Disaster Intelligence Engine run (location_id={request.location_id}, force_fresh={request.force_fresh_fetch})")
    start_t = time.perf_counter()
    engine_status_tracker.mark_running()

    # Ensure locations exist if database is fresh
    await LocationService.seed_initial_locations(db)

    try:
        if request.location_id:
            loc_res = await db.execute(select(Location).where(Location.id == request.location_id))
            location = loc_res.scalars().first()
            if not location:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Location with ID '{request.location_id}' not found."
                )

            assessment_out, event, _ = await disaster_engine.evaluate_location(
                session=db,
                location=location,
                force_fresh=request.force_fresh_fetch
            )
            await db.commit()
            duration_ms = (time.perf_counter() - start_t) * 1000.0
            engine_status_tracker.record_success(
                locations_count=1,
                active_events=1 if event and event.status != "RESOLVED" else 0,
                highest_score=assessment_out.risk_score,
                highest_level=assessment_out.risk_level.value,
                duration_ms=duration_ms
            )
            return disaster_engine.format_assessment_response(location, assessment_out, event)

        # Multi-location execution with distributed lock protection
        lock_name = "engine:execution_lock"
        await redis_service.acquire_lock(lock_name, ttl_seconds=60)
        try:
            result = await disaster_engine.run_pipeline(
                session=db,
                target_location_id=None,
                force_fresh=request.force_fresh_fetch
            )
            await db.commit()
            duration_ms = (time.perf_counter() - start_t) * 1000.0
            engine_status_tracker.record_success(
                locations_count=result.locations_evaluated,
                active_events=result.active_events_count,
                highest_score=result.highest_risk_score,
                highest_level=result.highest_risk_level,
                duration_ms=duration_ms
            )
            return result
        finally:
            await redis_service.release_lock(lock_name)
    except Exception as err:
        duration_ms = (time.perf_counter() - start_t) * 1000.0
        engine_status_tracker.record_error(str(err), duration_ms=duration_ms)
        raise err

