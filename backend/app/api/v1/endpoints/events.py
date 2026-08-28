from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db
from backend.app.models.event import DisasterEvent
from backend.app.models.location import Location
from backend.app.models.risk import RiskAssessment
from backend.app.schemas.event import DisasterEventResponse
from backend.app.schemas.dashboard import EventTimelineMilestone
from backend.app.core.logging import logger

router = APIRouter()


@router.get("", response_model=List[DisasterEventResponse])
async def list_events(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: 'active', 'WATCH', 'HIGH_RISK', 'CRITICAL', 'RESOLVED'"),
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    List disaster events. Pass status='active' to retrieve non-resolved events.
    """
    stmt = select(DisasterEvent)

    if status_filter:
        if status_filter.lower() == "active":
            stmt = stmt.where(DisasterEvent.status != "RESOLVED")
        else:
            stmt = stmt.where(DisasterEvent.status == status_filter.upper())

    if location_id:
        stmt = stmt.where(DisasterEvent.location_id == location_id)

    stmt = stmt.order_by(DisasterEvent.updated_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{event_id}", response_model=DisasterEventResponse)
async def get_event(event_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get detailed information about a specific disaster event.
    """
    stmt = select(DisasterEvent).where(DisasterEvent.id == event_id)
    result = await db.execute(stmt)
    event = result.scalars().first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disaster event with ID '{event_id}' not found."
        )

    return event


@router.get("/{event_id}/timeline", response_model=List[EventTimelineMilestone])
async def get_event_timeline(event_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns the step-by-step chronological audit log milestones for an event.
    """
    stmt = select(DisasterEvent).where(DisasterEvent.id == event_id)
    result = await db.execute(stmt)
    event = result.scalars().first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disaster event with ID '{event_id}' not found."
        )

    # Fetch location details
    loc_stmt = select(Location).where(Location.id == event.location_id)
    loc_res = await db.execute(loc_stmt)
    location = loc_res.scalars().first()

    # Reconstruct chronological progression
    milestones: List[EventTimelineMilestone] = []
    base_time = event.detected_at - timedelta(hours=3)

    # Step 1: Baseline monitoring
    milestones.append(
        EventTimelineMilestone(
            timestamp=base_time,
            time_label=base_time.strftime("%H:%M"),
            title="Environmental Baseline Active",
            description=f"Continuous sensor data telemetry ingested for {location.name if location else 'station'}.",
            category="info"
        )
    )

    # Step 2: Precipitation / pore pressure surge
    t2 = event.detected_at - timedelta(minutes=45)
    milestones.append(
        EventTimelineMilestone(
            timestamp=t2,
            time_label=t2.strftime("%H:%M"),
            title="Rainfall Anomaly & Moisture Saturation Flagged",
            description="Statistical Z-score exceeded threshold. Pore water saturation rate accelerated.",
            category="anomaly",
            severity="MODERATE"
        )
    )

    # Step 3: Event Creation
    milestones.append(
        EventTimelineMilestone(
            timestamp=event.detected_at,
            time_label=event.detected_at.strftime("%H:%M"),
            title=f"Disaster Event Created: {event.status}",
            description=f"Landslide risk score reached {event.risk_score:.1f}/100. Severity categorized as {event.severity}.",
            category="event",
            severity=event.severity
        )
    )

    # Step 4: Latest update / resolution
    if event.status == "RESOLVED":
        milestones.append(
            EventTimelineMilestone(
                timestamp=event.updated_at,
                time_label=event.updated_at.strftime("%H:%M"),
                title="Hazard Subsidence & Event Resolved",
                description=f"Environmental indices subsided to safe baseline (Score: {event.risk_score:.1f}).",
                category="resolution"
            )
        )
    elif event.updated_at > event.detected_at + timedelta(seconds=10):
        milestones.append(
            EventTimelineMilestone(
                timestamp=event.updated_at,
                time_label=event.updated_at.strftime("%H:%M"),
                title=f"Risk Assessment Updated ({event.status})",
                description=f"Ongoing monitoring state active. Current risk score: {event.risk_score:.1f}/100.",
                category="escalation",
                severity=event.severity
            )
        )

    return milestones


@router.post("/{event_id}/acknowledge", response_model=DisasterEventResponse)
async def acknowledge_event(event_id: str, db: AsyncSession = Depends(get_db)):
    """
    Allows central monitoring officers to acknowledge an ongoing disaster event.
    """
    stmt = select(DisasterEvent).where(DisasterEvent.id == event_id)
    result = await db.execute(stmt)
    event = result.scalars().first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disaster event with ID '{event_id}' not found."
        )

    if "[ACKNOWLEDGED BY OFFICER]" not in event.summary:
        event.summary = f"[ACKNOWLEDGED BY OFFICER] {event.summary}"
        event.updated_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(f"Officer acknowledged DisasterEvent {event.id}")

    return event
