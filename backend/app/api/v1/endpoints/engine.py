from typing import Union
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
from backend.app.core.logging import logger

router = APIRouter()


@router.post("/run", response_model=Union[MultiLocationEngineResponse, EngineAssessmentResponse])
async def run_engine(
    request: EngineRunRequest = EngineRunRequest(),
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers an execution run of the Disaster Intelligence Engine.
    Executes full pipeline:
    1. Ingestion / Observation retrieval
    2. Anomaly Detection (Statistical rolling z-scores)
    3. Temporal Trend Analysis (Slopes & Persistence)
    4. Landslide Risk Modeling (Explainable weighted factors)
    5. Event Management (Deduplication, state updates, resolution)
    6. Returns structured risk assessment and factor breakdowns.
    """
    logger.info(f"Triggering Disaster Intelligence Engine run (location_id={request.location_id}, force_fresh={request.force_fresh_fetch})")

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
        return disaster_engine.format_assessment_response(location, assessment_out, event)

    # Multi-location execution
    result = await disaster_engine.run_pipeline(
        session=db,
        target_location_id=None,
        force_fresh=request.force_fresh_fetch
    )
    await db.commit()
    return result
