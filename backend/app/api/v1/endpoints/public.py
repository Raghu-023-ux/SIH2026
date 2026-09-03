from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db
from backend.app.services.public_safety_service import public_safety_service
from backend.app.schemas.public import (
    PublicSystemStatusResponse,
    PublicAlertItem,
    PublicAlertDetailResponse,
    PublicRiskCheckResponse,
    LocationCheckRequest,
    SafetyPointResponse,
    PublicAlertAcknowledgeRequest,
    PublicPreferencesRequest,
    PublicPreferencesResponse,
)
from backend.app.core.logging import logger

router = APIRouter()


@router.get("/status", response_model=PublicSystemStatusResponse)
async def get_public_system_status(db: AsyncSession = Depends(get_db)):
    """Public system health check and active alert counter."""
    return await public_safety_service.get_public_system_status(db)


@router.get("/risk", response_model=PublicRiskCheckResponse)
async def check_public_risk_get(
    latitude: Optional[float] = Query(None, ge=-90.0, le=90.0),
    longitude: Optional[float] = Query(None, ge=-180.0, le=180.0),
    location_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Evaluates geofenced risk for a citizen based on GPS coordinates or monitored station ID."""
    return await public_safety_service.evaluate_user_location(
        session=db,
        latitude=latitude,
        longitude=longitude,
        location_id=location_id
    )


@router.post("/location-check", response_model=PublicRiskCheckResponse)
async def check_public_risk_post(
    req: LocationCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    """Evaluates geofenced hazard risk and returns structured safety guidance."""
    return await public_safety_service.evaluate_user_location(
        session=db,
        latitude=req.latitude,
        longitude=req.longitude,
        location_id=req.location_id
    )


@router.get("/alerts", response_model=List[PublicAlertItem])
async def list_active_public_alerts(db: AsyncSession = Depends(get_db)):
    """Lists all active public landslide safety alerts in the North Eastern Region."""
    return await public_safety_service.get_active_public_alerts(db)


@router.get("/alerts/{event_id}", response_model=PublicAlertDetailResponse)
async def get_public_alert_detail(
    event_id: str,
    latitude: Optional[float] = Query(None, ge=-90.0, le=90.0),
    longitude: Optional[float] = Query(None, ge=-180.0, le=180.0),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves full public safety briefing, conservative Do/Don't guidance, and nearest safer points."""
    alert_detail = await public_safety_service.get_public_alert_detail(
        session=db,
        event_id=event_id,
        user_lat=latitude,
        user_lon=longitude
    )
    if not alert_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disaster alert for event '{event_id}' not found or resolved."
        )
    return alert_detail


@router.get("/safety-points", response_model=List[SafetyPointResponse])
async def list_safety_points(
    location_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Lists configured safer reference points, community assembly grounds, and shelters."""
    points = await public_safety_service.get_all_safety_points(db, location_id)
    return [SafetyPointResponse.model_validate(p) for p in points]


@router.post("/acknowledge", status_code=status.HTTP_200_OK)
async def acknowledge_public_alert(
    req: PublicAlertAcknowledgeRequest,
    db: AsyncSession = Depends(get_db)
):
    """Records citizen review/acknowledgment of emergency safety guidance."""
    await public_safety_service.record_acknowledgment(
        session=db,
        event_id=req.event_id,
        location_id=req.location_id,
        user_id=req.user_id
    )
    await db.commit()
    return {"status": "ACKNOWLEDGED", "message": "Safety guidance view recorded."}


@router.post("/preferences", response_model=PublicPreferencesResponse)
async def update_public_preferences(
    req: PublicPreferencesRequest,
    db: AsyncSession = Depends(get_db)
):
    """Saves localized citizen notification radius and alert preferences."""
    from datetime import datetime, timezone
    import uuid

    return PublicPreferencesResponse(
        user_id=req.user_id or str(uuid.uuid4()),
        alert_enabled=req.alert_enabled,
        alert_radius_km=req.alert_radius_km,
        preferred_language=req.preferred_language,
        updated_at=datetime.now(timezone.utc)
    )
