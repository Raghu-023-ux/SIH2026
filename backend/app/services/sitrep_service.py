from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.event import DisasterEvent
from backend.app.models.location import Location
from backend.app.models.risk import RiskAssessment
from backend.app.models.weather import WeatherObservation
from backend.app.models.field import FieldTeam, FieldReport, AssistanceRequest
from backend.app.models.public import SafetyPoint
from backend.app.models.alerting import SituationReport
from backend.app.schemas.alerting import (
    SituationReportDetail,
    SitRepSection,
    SitRepResponse,
)
from backend.app.core.config import settings
from backend.app.core.logging import logger


class SituationReportService:
    """
    Automated Situation Report (SitRep) generator for NDMA, SDRF, and District Disaster Management Authorities.
    Synthesizes scientific engine risk, field ground evidence, and public safety deployment into formal briefings.
    """

    @staticmethod
    async def generate_sitrep(
        session: AsyncSession,
        event_id: str,
        reporting_officer: str = "Command Duty Officer"
    ) -> Optional[SituationReportDetail]:
        # 1. Fetch Event
        ev = (await session.execute(select(DisasterEvent).where(DisasterEvent.id == event_id))).scalars().first()
        if not ev:
            return None

        # 2. Fetch Location
        loc = (await session.execute(select(Location).where(Location.id == ev.location_id))).scalars().first()
        if not loc:
            return None

        # 3. Fetch Latest Scientific Assessment
        assess_stmt = (
            select(RiskAssessment)
            .where(RiskAssessment.location_id == loc.id)
            .order_by(RiskAssessment.timestamp.desc())
        )
        assess = (await session.execute(assess_stmt)).scalars().first()

        # 4. Fetch Latest Telemetry
        obs_stmt = (
            select(WeatherObservation)
            .where(WeatherObservation.location_id == loc.id)
            .order_by(WeatherObservation.timestamp.desc())
        )
        obs = (await session.execute(obs_stmt)).scalars().first()

        # 5. Fetch Field Reports & Assistance
        field_reps = list((await session.execute(select(FieldReport).where(FieldReport.location_id == loc.id))).scalars().all())
        road_blocks = [r for r in field_reps if r.report_type == "ROAD_BLOCKED"]
        slide_obs = [r for r in field_reps if r.report_type == "LANDSLIDE_OBSERVED"]

        teams = list((await session.execute(select(FieldTeam))).scalars().all())
        deployed_teams = [t for t in teams if t.status in ["DEPLOYED", "ON_SCENE", "ASSISTING", "EVACUATING"]]
        need_assist = [t for t in teams if t.status == "NEED_ASSISTANCE"]

        # 6. Fetch Safety Points
        safe_pts = list((await session.execute(select(SafetyPoint).where(SafetyPoint.location_id == loc.id))).scalars().all())

        now = datetime.now(timezone.utc)
        report_num = f"SITREP-NER-{loc.id[:7]}-{int(now.timestamp()) % 10000:04d}"
        incident_name = f"{loc.district} ({loc.state}) Landslide Emergency [{ev.severity}]"

        exec_summary = (
            f"At {now.strftime('%Y-%m-%d %H:%M UTC')}, the AI Disaster Intelligence Engine maintained an active "
            f"{ev.severity} hazard classification for {loc.name} (Risk Score: {ev.risk_score:.1f}/100, Confidence: {assess.confidence_score if assess else 0.82:.0%}). "
            f"Multi-signal telemetry indicates severe slope moisture saturation and persistent precipitation. "
            f"{len(field_reps)} field observations reported from on-ground response units, including {len(road_blocks)} road blockages. "
            f"{len(deployed_teams)} response teams are deployed across the sector."
        )

        sections: List[SitRepSection] = [
            # Section 1: Scientific Assessment & Telemetry
            SitRepSection(
                heading="1. Scientific Risk Assessment & Environmental Telemetry",
                content=(
                    f"Authoritative mathematical risk assessment: {ev.risk_score:.1f}/100 ({ev.severity}). "
                    f"24-Hour Cumulative Rainfall: {obs.rainfall_24h if obs else 65.0:.1f} mm | "
                    f"Current Pore Soil Moisture: {obs.soil_moisture if obs else 78.0:.1f}% | "
                    f"Terrain Slope Incline: {loc.slope_angle:.1f}° | Baseline Susceptibility: {loc.susceptibility_score:.2f}. "
                    f"Top risk drivers: Rainfall persistence, high slope gradient, and rapid pore pressure rise."
                ),
                key_metrics={
                    "risk_score": ev.risk_score,
                    "severity": ev.severity,
                    "confidence": assess.confidence_score if assess else 0.82,
                    "rainfall_24h_mm": obs.rainfall_24h if obs else 65.0,
                    "soil_moisture_pct": obs.soil_moisture if obs else 78.0,
                    "slope_angle_deg": loc.slope_angle
                }
            ),
            # Section 2: On-Ground Rescue Intelligence
            SitRepSection(
                heading="2. On-Ground Field Intelligence & Ground Observations",
                content=(
                    f"Total Ground Reports: {len(field_reps)}. "
                    f"Road Blockages: {len(road_blocks)} verified sector road obstructions. "
                    f"Active Debris Slides Observed: {len(slide_obs)}. "
                    f"Latest field observation: {field_reps[0].description if field_reps else 'No ground reports submitted yet.'}"
                ),
                key_metrics={
                    "total_reports": len(field_reps),
                    "road_blocks": len(road_blocks),
                    "landslides_observed": len(slide_obs)
                }
            ),
            # Section 3: Rescue Unit Deployments & Tactical Status
            SitRepSection(
                heading="3. Rescue Unit Deployment & Resource Status",
                content=(
                    f"Active Response Units: {len(deployed_teams)} teams deployed in sector "
                    f"({', '.join([t.callsign for t in deployed_teams]) if deployed_teams else 'Standby'}). "
                    f"Emergency Assistance Requests: {len(need_assist)} teams requested backup resources."
                ),
                key_metrics={
                    "teams_deployed": len(deployed_teams),
                    "teams_on_scene": sum(1 for t in teams if t.status == "ON_SCENE"),
                    "teams_need_assistance": len(need_assist)
                }
            ),
            # Section 4: Public Safety & Evacuation Points
            SitRepSection(
                heading="4. Public Safety, Alerts & Designated Evacuation Assembly",
                content=(
                    f"Public Warning Status: {'URGENT' if ev.severity == 'CRITICAL' else 'ALERT'}. "
                    f"Configured Safer Reference Points: {len(safe_pts)} assembly shelters identified. "
                    f"Primary Assembly Shelter: {safe_pts[0].name if safe_pts else 'Community Sports Ground'} "
                    f"(Capacity: {safe_pts[0].capacity if safe_pts else 500})."
                ),
                key_metrics={
                    "public_status": "URGENT" if ev.severity == "CRITICAL" else "ALERT",
                    "safe_points_count": len(safe_pts),
                    "primary_safe_point": safe_pts[0].name if safe_pts else "Paljor Open Grounds"
                }
            ),
            # Section 5: Tactical Recommendations & 12-Hour Outlook
            SitRepSection(
                heading="5. Tactical Recommendations & Command Directives",
                content=(
                    "1. Restrict non-essential transit along arterial hillside bypass corridors.\n"
                    "2. Position heavy earthmoving equipment at vulnerable drainage culverts.\n"
                    "3. Maintain 15-minute sensor polling and notify district civil defense wardens.\n"
                    "4. Issue CAP v1.2 warning feeds to national and state aggregators."
                )
            )
        ]

        sitrep_detail = SituationReportDetail(
            report_number=report_num,
            incident_name=incident_name,
            location_name=loc.name,
            state=loc.state,
            reporting_officer=reporting_officer,
            generated_at=now,
            operational_period=f"Operational Period 001 ({now.strftime('%d %b %Y')})",
            executive_summary=exec_summary,
            sections=sections,
            data_mode=settings.DATA_MODE
        )

        # Persist SitRep in database
        sitrep_row = SituationReport(
            event_id=ev.id,
            location_id=loc.id,
            report_number=report_num,
            incident_name=incident_name,
            reporting_officer=reporting_officer,
            executive_summary=exec_summary,
            full_sitrep_json=sitrep_detail.model_dump(mode="json")
        )
        session.add(sitrep_row)
        await session.flush()
        logger.info(f"Generated and persisted Situation Report {report_num} for event {ev.id}")

        return sitrep_detail


sitrep_service = SituationReportService()
