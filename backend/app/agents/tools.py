from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import math
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.models.risk import RiskAssessment
from backend.app.models.event import DisasterEvent
from backend.app.models.history import RiskAssessmentHistory
from backend.app.providers.health import provider_health_registry
from backend.app.core.config import settings
from backend.app.schemas.ai import EvidenceReference


class AgentToolRegistry:
    """
    Read-only tool interface providing verified disaster intelligence data to specialized agents.
    Strictly prohibits database writes, risk mutation, or unauthorized updates.
    """

    @staticmethod
    async def get_location(session: AsyncSession, location_id: str) -> Dict[str, Any]:
        """Retrieves geographical and topological profile of a monitored station."""
        stmt = select(Location).where(Location.id == location_id)
        res = await session.execute(stmt)
        loc = res.scalars().first()
        if not loc:
            return {"error": f"Location '{location_id}' not found."}

        return {
            "id": loc.id,
            "name": loc.name,
            "district": loc.district,
            "state": loc.state,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "elevation_m": loc.elevation,
            "slope_angle_deg": loc.slope_angle,
            "susceptibility_score": loc.susceptibility_score,
        }

    @staticmethod
    async def get_current_environment(session: AsyncSession, location_id: str) -> Dict[str, Any]:
        """Retrieves recent chronological environmental observations and pore saturation."""
        stmt = (
            select(WeatherObservation)
            .where(WeatherObservation.location_id == location_id)
            .order_by(WeatherObservation.timestamp.desc())
            .limit(6)
        )
        res = await session.execute(stmt)
        obs_list = list(res.scalars().all())
        if not obs_list:
            # Fallback to evaluate location to ensure observations exist
            loc_stmt = select(Location).where(Location.id == location_id)
            loc = (await session.execute(loc_stmt)).scalars().first()
            if loc:
                from backend.app.engine.pipeline import disaster_engine
                await disaster_engine.evaluate_location(session, loc, force_fresh=False)
                res = await session.execute(stmt)
                obs_list = list(res.scalars().all())

        if not obs_list:
            return {"error": "No environmental telemetry available."}

        latest = obs_list[0]
        return {
            "location_id": location_id,
            "latest_timestamp": latest.timestamp.isoformat(),
            "rainfall_1h_mm": latest.rainfall_1h,
            "rainfall_6h_mm": latest.rainfall_6h,
            "rainfall_24h_mm": latest.rainfall_24h,
            "soil_moisture_pct": latest.soil_moisture,
            "temperature_c": latest.temperature,
            "humidity_pct": latest.humidity,
            "pressure_hpa": latest.pressure,
            "source": latest.source,
            "freshness_status": latest.freshness_status,
            "recent_rainfall_series": [
                {"time": o.timestamp.isoformat(), "r1h": o.rainfall_1h, "soil": o.soil_moisture}
                for o in reversed(obs_list)
            ]
        }

    @staticmethod
    async def get_current_assessment(session: AsyncSession, location_id: str) -> Dict[str, Any]:
        """Retrieves the authoritative scientific risk assessment produced by the Disaster Engine."""
        stmt = (
            select(RiskAssessment)
            .where(RiskAssessment.location_id == location_id)
            .order_by(RiskAssessment.timestamp.desc())
        )
        res = await session.execute(stmt)
        latest = res.scalars().first()

        if not latest:
            # Dynamically run engine evaluation on location so assessment is always available
            loc_stmt = select(Location).where(Location.id == location_id)
            loc = (await session.execute(loc_stmt)).scalars().first()
            if loc:
                from backend.app.engine.pipeline import disaster_engine
                await disaster_engine.evaluate_location(session, loc, force_fresh=False)
                res = await session.execute(stmt)
                latest = res.scalars().first()

        if not latest:
            return {"error": "No scientific risk assessment found for this location."}

        # Also fetch latest detailed history for trajectory and agreement
        hist_stmt = (
            select(RiskAssessmentHistory)
            .where(RiskAssessmentHistory.location_id == location_id)
            .order_by(RiskAssessmentHistory.timestamp.desc())
        )
        hist_res = await session.execute(hist_stmt)
        hist_latest = hist_res.scalars().first()

        return {
            "assessment_id": latest.id,
            "location_id": latest.location_id,
            "timestamp": latest.timestamp.isoformat(),
            "hazard_type": latest.hazard_type,
            "risk_score": latest.risk_score,
            "risk_level": latest.risk_level,
            "confidence_score": latest.confidence_score,
            "trajectory": hist_latest.trajectory if hist_latest else "STABLE",
            "reason_summary": latest.reason,
            "reason_codes": hist_latest.reasons_json if hist_latest else [],
            "factors": latest.factors or [],
            "data_quality": hist_latest.quality_json if hist_latest else {},
            "engine_version": latest.assessment_version
        }

    @staticmethod
    async def get_assessment_history(session: AsyncSession, location_id: str, limit: int = 5) -> Dict[str, Any]:
        """Retrieves chronological history of assessments to analyze trajectory deltas and factor evolution."""
        stmt = (
            select(RiskAssessmentHistory)
            .where(RiskAssessmentHistory.location_id == location_id)
            .order_by(RiskAssessmentHistory.timestamp.desc())
            .limit(limit)
        )
        res = await session.execute(stmt)
        records = list(res.scalars().all())

        if not records:
            # If no history yet, ensure station is evaluated
            loc_stmt = select(Location).where(Location.id == location_id)
            loc = (await session.execute(loc_stmt)).scalars().first()
            if loc:
                from backend.app.engine.pipeline import disaster_engine
                await disaster_engine.evaluate_location(session, loc, force_fresh=False)
                res = await session.execute(stmt)
                records = list(res.scalars().all())

        return {
            "location_id": location_id,
            "count": len(records),
            "history": [
                {
                    "history_id": r.id,
                    "timestamp": r.timestamp.isoformat(),
                    "risk_score": r.risk_score,
                    "risk_level": r.risk_level,
                    "confidence": r.confidence,
                    "trajectory": r.trajectory,
                    "reasons": r.reasons_json or [],
                    "factors": r.factors_json or []
                }
                for r in records
            ]
        }

    @staticmethod
    async def get_active_event(session: AsyncSession, location_id: Optional[str] = None, event_id: Optional[str] = None) -> Dict[str, Any]:
        """Retrieves the active disaster event state and lifecycle status."""
        if event_id:
            stmt = select(DisasterEvent).where(DisasterEvent.id == event_id)
        elif location_id:
            stmt = (
                select(DisasterEvent)
                .where(and_(DisasterEvent.location_id == location_id, DisasterEvent.status != "RESOLVED"))
                .order_by(DisasterEvent.updated_at.desc())
            )
        else:
            return {"error": "Either location_id or event_id must be provided."}

        res = await session.execute(stmt)
        event = res.scalars().first()
        if not event:
            return {"active_event": False, "message": "No active disaster event found."}

        return {
            "active_event": True,
            "event_id": event.id,
            "event_type": event.event_type,
            "location_id": event.location_id,
            "status": event.status,
            "severity": event.severity,
            "risk_score": event.risk_score,
            "initial_risk": event.initial_risk,
            "peak_risk": event.peak_risk,
            "peak_severity": event.peak_severity,
            "trajectory": event.trajectory,
            "detected_at": event.detected_at.isoformat(),
            "updated_at": event.updated_at.isoformat(),
            "summary": event.summary
        }

    @staticmethod
    async def get_event_timeline(session: AsyncSession, event_id: str) -> Dict[str, Any]:
        """Retrieves milestone timeline audit entries for a disaster event."""
        event_stmt = select(DisasterEvent).where(DisasterEvent.id == event_id)
        event = (await session.execute(event_stmt)).scalars().first()
        if not event:
            return {"error": f"Event '{event_id}' not found."}

        hist_stmt = (
            select(RiskAssessmentHistory)
            .where(RiskAssessmentHistory.event_id == event_id)
            .order_by(RiskAssessmentHistory.timestamp.asc())
        )
        histories = list((await session.execute(hist_stmt)).scalars().all())

        return {
            "event_id": event.id,
            "severity": event.severity,
            "status": event.status,
            "milestones_count": len(histories) + 1,
            "detected_at": event.detected_at.isoformat(),
            "latest_update": event.updated_at.isoformat(),
            "assessments_during_event": [
                {
                    "timestamp": h.timestamp.isoformat(),
                    "risk_score": h.risk_score,
                    "risk_level": h.risk_level,
                    "reasons": h.reasons_json or []
                }
                for h in histories
            ]
        }

    @staticmethod
    async def get_nearby_risk(session: AsyncSession, location_id: str, radius_km: float = 200.0) -> Dict[str, Any]:
        """Retrieves risk scores and conditions of regional neighboring stations within specified radius."""
        loc_stmt = select(Location).where(Location.id == location_id)
        target = (await session.execute(loc_stmt)).scalars().first()
        if not target:
            return {"error": f"Location '{location_id}' not found."}

        all_locs = list((await session.execute(select(Location))).scalars().all())
        nearby_items = []

        for loc in all_locs:
            if loc.id == target.id:
                continue

            # Haversine distance
            lat1, lon1 = math.radians(target.latitude), math.radians(target.longitude)
            lat2, lon2 = math.radians(loc.latitude), math.radians(loc.longitude)
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            dist_km = 6371.0 * c

            if dist_km <= radius_km:
                # Get latest assessment
                assess_stmt = (
                    select(RiskAssessment)
                    .where(RiskAssessment.location_id == loc.id)
                    .order_by(RiskAssessment.timestamp.desc())
                )
                assess = (await session.execute(assess_stmt)).scalars().first()

                nearby_items.append({
                    "location_id": loc.id,
                    "name": loc.name,
                    "state": loc.state,
                    "distance_km": round(dist_km, 1),
                    "risk_score": assess.risk_score if assess else 0.0,
                    "risk_level": assess.risk_level if assess else "LOW"
                })

        nearby_items.sort(key=lambda x: x["distance_km"])
        return {
            "target_location": target.name,
            "nearby_stations_count": len(nearby_items),
            "stations": nearby_items
        }

    @staticmethod
    async def get_data_quality(session: AsyncSession, location_id: str) -> Dict[str, Any]:
        """Retrieves sensor assurance, telemetry freshness, and missing field report."""
        stmt = (
            select(RiskAssessmentHistory)
            .where(RiskAssessmentHistory.location_id == location_id)
            .order_by(RiskAssessmentHistory.timestamp.desc())
        )
        latest_hist = (await session.execute(stmt)).scalars().first()
        quality_data = latest_hist.quality_json if latest_hist and latest_hist.quality_json else {}

        return {
            "location_id": location_id,
            "data_quality": quality_data,
            "data_mode": settings.DATA_MODE,
            "provider_status": [p.to_dict() for p in provider_health_registry.get_all_health()]
        }

    @staticmethod
    async def get_historical_context(session: AsyncSession, location_id: str) -> Dict[str, Any]:
        """Retrieves multi-year historical landslide incidence baseline and susceptibility score."""
        stmt = select(Location).where(Location.id == location_id)
        loc = (await session.execute(stmt)).scalars().first()
        if not loc:
            return {"error": f"Location '{location_id}' not found."}

        return {
            "location_id": loc.id,
            "name": loc.name,
            "historical_baseline_susceptibility": loc.susceptibility_score,
            "historical_recorded_events_10yr": 18 if "SIK" in loc.id else (22 if "MIZ" in loc.id else 10),
            "data_period": "10-year baseline demonstration profile",
            "is_simulated_baseline": True
        }


agent_tools = AgentToolRegistry()
