from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db
from backend.app.models.risk import RiskAssessment
from backend.app.models.location import Location
from backend.app.schemas.risk import RiskAssessmentResponse
from backend.app.engine.pipeline import disaster_engine

router = APIRouter()


@router.get("/{location_id}", response_model=RiskAssessmentResponse)
async def get_latest_risk_assessment(location_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the latest evaluated landslide risk assessment for a location.
    If none exists, executes a fresh engine evaluation.
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
        select(RiskAssessment)
        .where(RiskAssessment.location_id == location_id)
        .order_by(RiskAssessment.timestamp.desc())
    )
    result = await db.execute(stmt)
    latest = result.scalars().first()

    if not latest:
        # Run engine evaluation for this location
        await disaster_engine.evaluate_location(db, location)
        await db.commit()

        result = await db.execute(stmt)
        latest = result.scalars().first()

    return latest


@router.get("/{location_id}/history", response_model=List[RiskAssessmentResponse])
async def get_risk_history(
    location_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical risk assessments for trend and evolution review.
    """
    stmt = (
        select(RiskAssessment)
        .where(RiskAssessment.location_id == location_id)
        .order_by(RiskAssessment.timestamp.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
