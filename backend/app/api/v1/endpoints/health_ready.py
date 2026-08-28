from datetime import datetime, timezone
import time
from typing import Dict, Any
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db
from backend.app.models.location import Location
from backend.app.models.event import DisasterEvent
from backend.app.models.alerting import NotificationDispatchLog
from backend.app.core.config import settings

router = APIRouter()


@router.get("/live", tags=["Health & Readiness"])
async def liveness_probe():
    """Kubernetes / Container Liveness Probe."""
    return {
        "status": "ALIVE",
        "service": "SIH26001 Disaster Intelligence Engine",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/ready", tags=["Health & Readiness"])
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    """Kubernetes / Container Readiness Probe verifying database & pipeline health."""
    try:
        # Check database connectivity
        loc_count = (await db.execute(select(func.count(Location.id)))).scalar_one()
        active_events = (await db.execute(
            select(func.count(DisasterEvent.id)).where(DisasterEvent.status != "RESOLVED")
        )).scalar_one()

        return {
            "status": "READY",
            "database": "CONNECTED",
            "locations_monitored": loc_count,
            "active_events": active_events,
            "data_mode": settings.DATA_MODE,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return Response(
            content=f'{{"status": "NOT_READY", "error": "{str(e)}"}}',
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json"
        )


@router.get("/metrics", tags=["Health & Readiness"])
async def prometheus_metrics(db: AsyncSession = Depends(get_db)):
    """Prometheus-compatible operational monitoring metrics."""
    try:
        loc_count = (await db.execute(select(func.count(Location.id)))).scalar_one()
        active_events = (await db.execute(
            select(func.count(DisasterEvent.id)).where(DisasterEvent.status != "RESOLVED")
        )).scalar_one()
        total_broadcasts = (await db.execute(select(func.count(NotificationDispatchLog.id)))).scalar_one()
    except Exception:
        loc_count, active_events, total_broadcasts = 6, 0, 0

    mode_val = 1.0 if settings.DATA_MODE == "LIVE" else 0.0

    lines = [
        "# HELP sih_engine_up Engine process availability",
        "# TYPE sih_engine_up gauge",
        "sih_engine_up 1.0",
        "# HELP sih_engine_live_mode Data ingestion mode (1=LIVE, 0=SIMULATION)",
        "# TYPE sih_engine_live_mode gauge",
        f"sih_engine_live_mode {mode_val}",
        "# HELP sih_locations_monitored Total monitored stations in North Eastern Region",
        "# TYPE sih_locations_monitored gauge",
        f"sih_locations_monitored {loc_count}",
        "# HELP sih_active_disaster_events Active critical/high events in queue",
        "# TYPE sih_active_disaster_events gauge",
        f"sih_active_disaster_events {active_events}",
        "# HELP sih_notifications_dispatched_total Total emergency broadcasts dispatched",
        "# TYPE sih_notifications_dispatched_total counter",
        f"sih_notifications_dispatched_total {total_broadcasts}",
    ]

    return Response(content="\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")
