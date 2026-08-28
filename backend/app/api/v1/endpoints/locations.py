from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db
from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.models.risk import RiskAssessment
from backend.app.models.event import DisasterEvent
from backend.app.models.history import RiskAssessmentHistory
from backend.app.schemas.location import LocationResponse
from backend.app.schemas.weather import WeatherObservationResponse
from backend.app.schemas.risk import RiskAssessmentResponse
from backend.app.schemas.event import DisasterEventResponse
from backend.app.schemas.engine import EngineAssessmentResponse
from backend.app.schemas.dashboard import LocationMapItem, LocationInvestigationResponse, EventTimelineMilestone
from backend.app.services.location_service import LocationService
from backend.app.engine.pipeline import disaster_engine
from backend.app.engine.data_validator import data_validator

router = APIRouter()


@router.get("", response_model=List[LocationResponse])
async def list_locations(db: AsyncSession = Depends(get_db)):
    """
    List all monitored locations in the North Eastern Region.
    """
    locations = await LocationService.get_all_locations(db)
    return locations


@router.get("/map", response_model=List[LocationMapItem])
async def get_locations_for_map(db: AsyncSession = Depends(get_db)):
    """
    Returns all monitored stations enriched with current risk score,
    latest weather readings, and active disaster events for GIS map rendering.
    """
    locations = await LocationService.get_all_locations(db)
    map_items: List[LocationMapItem] = []

    for loc in locations:
        risk_stmt = (
            select(RiskAssessment)
            .where(RiskAssessment.location_id == loc.id)
            .order_by(RiskAssessment.timestamp.desc())
            .limit(1)
        )
        risk_res = await db.execute(risk_stmt)
        latest_risk = risk_res.scalars().first()

        if not latest_risk:
            assessment_out, _, _ = await disaster_engine.evaluate_location(db, loc)
            await db.commit()
            risk_res = await db.execute(risk_stmt)
            latest_risk = risk_res.scalars().first()

        event_stmt = (
            select(DisasterEvent)
            .where(and_(DisasterEvent.location_id == loc.id, DisasterEvent.status != "RESOLVED"))
            .order_by(DisasterEvent.detected_at.desc())
            .limit(1)
        )
        event_res = await db.execute(event_stmt)
        active_event = event_res.scalars().first()

        weather_stmt = (
            select(WeatherObservation)
            .where(WeatherObservation.location_id == loc.id)
            .order_by(WeatherObservation.timestamp.desc())
            .limit(1)
        )
        weather_res = await db.execute(weather_stmt)
        latest_weather = weather_res.scalars().first()

        item = LocationMapItem(
            id=loc.id,
            name=loc.name,
            district=loc.district,
            state=loc.state,
            latitude=loc.latitude,
            longitude=loc.longitude,
            elevation=loc.elevation,
            slope_angle=loc.slope_angle,
            susceptibility_score=loc.susceptibility_score,
            risk_level=latest_risk.risk_level if latest_risk else "LOW",
            risk_score=latest_risk.risk_score if latest_risk else 10.0,
            confidence_score=latest_risk.confidence_score if latest_risk else 0.85,
            active_event=active_event is not None,
            event_id=active_event.id if active_event else None,
            event_status=active_event.status if active_event else None,
            event_severity=active_event.severity if active_event else None,
            rainfall_24h=latest_weather.rainfall_24h if latest_weather else 0.0,
            rainfall_1h=latest_weather.rainfall_1h if latest_weather else 0.0,
            soil_moisture=latest_weather.soil_moisture if latest_weather else 30.0,
            trend_direction="INCREASING" if (latest_weather and (latest_weather.rainfall_1h or 0) > 10) else "STABLE",
            last_updated=latest_risk.timestamp if latest_risk else datetime.now(timezone.utc)
        )
        map_items.append(item)

    return map_items


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(location_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get detailed station metadata.
    """
    location = await LocationService.get_location_by_id(db, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with ID '{location_id}' not found."
        )
    return location


@router.get("/{location_id}/assessment", response_model=EngineAssessmentResponse)
async def get_location_latest_assessment(location_id: str, db: AsyncSession = Depends(get_db)):
    """
    Evaluates or retrieves the latest structured risk assessment for a specific location.
    """
    location = await LocationService.get_location_by_id(db, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with ID '{location_id}' not found."
        )

    assessment_out, event, _ = await disaster_engine.evaluate_location(db, location)
    await db.commit()
    return disaster_engine.format_assessment_response(location, assessment_out, event)


@router.get("/{location_id}/assessment/history", response_model=List[RiskAssessmentResponse])
async def get_location_assessment_history(
    location_id: str,
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves chronological assessment audit history for a specific station.
    """
    stmt = (
        select(RiskAssessment)
        .where(RiskAssessment.location_id == location_id)
        .order_by(RiskAssessment.timestamp.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/{location_id}/environment", response_model=List[WeatherObservationResponse])
async def get_location_environmental_series(
    location_id: str,
    limit: int = Query(48, ge=1, le=168),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves validated meteorological and pore water sensor series for a station.
    """
    stmt = (
        select(WeatherObservation)
        .where(WeatherObservation.location_id == location_id)
        .order_by(WeatherObservation.timestamp.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/{location_id}/investigate", response_model=LocationInvestigationResponse)
async def investigate_location(location_id: str, db: AsyncSession = Depends(get_db)):
    """
    360-degree investigation payload for a specific monitoring station.
    """
    location = await LocationService.get_location_by_id(db, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with ID '{location_id}' not found."
        )

    # 1. Latest Risk Assessment
    risk_stmt = (
        select(RiskAssessment)
        .where(RiskAssessment.location_id == location_id)
        .order_by(RiskAssessment.timestamp.desc())
        .limit(1)
    )
    risk_res = await db.execute(risk_stmt)
    latest_risk = risk_res.scalars().first()

    if not latest_risk:
        await disaster_engine.evaluate_location(db, location)
        await db.commit()
        risk_res = await db.execute(risk_stmt)
        latest_risk = risk_res.scalars().first()

    # 2. Active Event
    event_stmt = (
        select(DisasterEvent)
        .where(and_(DisasterEvent.location_id == location_id, DisasterEvent.status != "RESOLVED"))
        .order_by(DisasterEvent.detected_at.desc())
        .limit(1)
    )
    event_res = await db.execute(event_stmt)
    active_event = event_res.scalars().first()

    # 3. Weather History (past 48 points)
    weather_stmt = (
        select(WeatherObservation)
        .where(WeatherObservation.location_id == location_id)
        .order_by(WeatherObservation.timestamp.asc())
        .limit(48)
    )
    weather_res = await db.execute(weather_stmt)
    weather_history = list(weather_res.scalars().all())

    # 4. Risk History (past 30 assessments)
    hist_stmt = (
        select(RiskAssessment)
        .where(RiskAssessment.location_id == location_id)
        .order_by(RiskAssessment.timestamp.asc())
        .limit(30)
    )
    hist_res = await db.execute(hist_stmt)
    risk_history = list(hist_res.scalars().all())

    # 5. Build Chronological Milestones
    milestones: List[EventTimelineMilestone] = []
    if weather_history:
        first_time = weather_history[0].timestamp
        milestones.append(
            EventTimelineMilestone(
                timestamp=first_time,
                time_label=first_time.strftime("%H:%M"),
                title="Continuous Telemetry Ingestion Online",
                description=f"Sensors active at {location.name} ({location.elevation:.0f}m elev, {location.slope_angle:.0f}° slope).",
                category="info"
            )
        )

    if latest_risk and latest_risk.risk_score >= 25.0:
        milestones.append(
            EventTimelineMilestone(
                timestamp=latest_risk.timestamp,
                time_label=latest_risk.timestamp.strftime("%H:%M"),
                title="Hazard Anomaly & Saturation Flagged",
                description=latest_risk.reason,
                category="anomaly",
                severity=latest_risk.risk_level
            )
        )

    if active_event:
        milestones.append(
            EventTimelineMilestone(
                timestamp=active_event.detected_at,
                time_label=active_event.detected_at.strftime("%H:%M"),
                title=f"Disaster Event Incident Created [{active_event.status}]",
                description=active_event.summary,
                category="event",
                severity=active_event.severity
            )
        )

    return LocationInvestigationResponse(
        location=LocationResponse.model_validate(location),
        latest_assessment=RiskAssessmentResponse.model_validate(latest_risk) if latest_risk else None,
        active_event=DisasterEventResponse.model_validate(active_event) if active_event else None,
        weather_history=[WeatherObservationResponse.model_validate(w) for w in weather_history],
        risk_history=[RiskAssessmentResponse.model_validate(r) for r in risk_history],
        event_timeline=milestones
    )
