import math
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.field import (
    FieldTeam,
    FieldReport,
    FieldReportImage,
    AssistanceRequest,
    OperationalMessage,
)
from backend.app.models.location import Location
from backend.app.models.event import DisasterEvent
from backend.app.models.risk import RiskAssessment
from backend.app.models.weather import WeatherObservation
from backend.app.schemas.field import (
    FieldReportCreate,
    FieldReportUpdate,
    FieldReportImageResponse,
    AssistanceRequestCreate,
    AssistanceRequestUpdate,
    OperationalMessageCreate,
    FieldTeamCreate,
    NearbyIncidentItem,
    ImmediateConditionsSummary,
    FieldAssignmentResponse,
    FieldOperationsSummary,
    FieldTeamResponse,
    FieldReportResponse,
    AssistanceRequestResponse,
    OperationalMessageResponse,
)
from backend.app.services.storage_provider import get_storage_provider
from backend.app.core.logging import logger


class FieldOperationsService:
    """
    Service layer for on-ground rescue teams and field intelligence feedback loops.
    """

    @staticmethod
    def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine formula for distance between two points in km."""
        r = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(r * c, 2)

    @staticmethod
    async def seed_initial_teams(session: AsyncSession):
        """Seeds standard NER response units if table is empty."""
        stmt = select(FieldTeam)
        existing = (await session.execute(stmt)).scalars().first()
        if existing:
            return

        # Seed initial rescue teams
        teams = [
            FieldTeam(
                id="NER-TEAM-ALPHA",
                team_name="SDRF Quick Response Unit Alpha",
                callsign="ALPHA-1",
                assigned_location_id="NER-SIK-GANGTOK-01",
                status="DEPLOYED",
                latitude=27.3389,
                longitude=88.6065,
                contact_channel="VHF Ch 4 / Satellite"
            ),
            FieldTeam(
                id="NER-TEAM-BRAVO",
                team_name="NDRF Search & Rescue Unit Bravo",
                callsign="BRAVO-2",
                assigned_location_id="NER-MIZ-AIZAWL-01",
                status="ON_SCENE",
                latitude=23.7271,
                longitude=92.7176,
                contact_channel="VHF Ch 7 / Satellite"
            ),
            FieldTeam(
                id="NER-TEAM-CHARLIE",
                team_name="District Disaster Management Unit Charlie",
                callsign="CHARLIE-3",
                assigned_location_id="NER-NAG-KOHIMA-01",
                status="AVAILABLE",
                latitude=25.6751,
                longitude=94.1086,
                contact_channel="VHF Ch 2 / Mobile"
            ),
        ]
        for t in teams:
            session.add(t)
        await session.flush()
        logger.info("Successfully seeded 3 North Eastern Region Field Response Units.")

    @staticmethod
    async def get_all_teams(session: AsyncSession) -> List[FieldTeam]:
        await FieldOperationsService.seed_initial_teams(session)
        stmt = select(FieldTeam).order_by(FieldTeam.team_name.asc())
        return list((await session.execute(stmt)).scalars().all())

    @staticmethod
    async def get_team_by_id_or_callsign(session: AsyncSession, identifier: str) -> Optional[FieldTeam]:
        await FieldOperationsService.seed_initial_teams(session)
        stmt = select(FieldTeam).where(or_(FieldTeam.id == identifier, FieldTeam.callsign == identifier))
        return (await session.execute(stmt)).scalars().first()

    VALID_TEAM_STATUSES = {
        "AVAILABLE", "ASSIGNED", "EN_ROUTE", "DEPLOYED", "ON_SITE", "ON_SCENE",
        "ASSESSING", "REPORT_SUBMITTED", "ASSISTING", "EVACUATING", "NEED_ASSISTANCE",
        "RESOLVED", "OFFLINE"
    }

    @staticmethod
    async def update_team_status(
        session: AsyncSession,
        team_id: str,
        status: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> Optional[FieldTeam]:
        norm_status = status.upper().replace(" ", "_")
        if norm_status not in FieldOperationsService.VALID_TEAM_STATUSES:
            raise ValueError(f"Invalid field unit status '{status}'. Valid statuses: {FieldOperationsService.VALID_TEAM_STATUSES}")

        stmt = select(FieldTeam).where(FieldTeam.id == team_id)
        team = (await session.execute(stmt)).scalars().first()
        if not team:
            return None

        team.status = norm_status
        if latitude is not None:
            team.latitude = latitude
        if longitude is not None:
            team.longitude = longitude
        team.last_active_at = datetime.now(timezone.utc)
        await session.flush()
        return team

    @staticmethod
    def format_report_response(report: FieldReport) -> FieldReportResponse:
        storage = get_storage_provider()
        image_list = []
        raw_images = report.__dict__.get("images")
        if raw_images:
            for img in raw_images:
                image_list.append(
                    FieldReportImageResponse(
                        id=img.id,
                        report_id=img.report_id,
                        storage_key=img.storage_key,
                        mime_type=img.mime_type,
                        file_size=img.file_size,
                        url=storage.get_url(img.storage_key),
                        uploaded_by=img.uploaded_by,
                        created_at=img.created_at,
                    )
                )
        return FieldReportResponse(
            id=report.id,
            event_id=report.event_id,
            location_id=report.location_id,
            team_id=report.team_id,
            reported_by=report.reported_by,
            report_type=report.report_type,
            severity=report.severity,
            description=report.description,
            latitude=report.latitude,
            longitude=report.longitude,
            location_accuracy=report.location_accuracy,
            location_source=report.location_source,
            timestamp=report.timestamp,
            status=report.status,
            reviewed_by=report.reviewed_by,
            review_notes=report.review_notes,
            images=image_list,
            created_at=report.created_at,
            updated_at=report.updated_at,
        )

    @staticmethod
    async def submit_field_report(session: AsyncSession, report_in: FieldReportCreate) -> FieldReport:
        # Validate severity
        norm_sev = report_in.severity.upper()
        if norm_sev not in ["LOW", "MODERATE", "HIGH", "CRITICAL"]:
            raise ValueError(f"Invalid severity '{report_in.severity}'. Must be LOW, MODERATE, HIGH, or CRITICAL.")

        # Validate GPS if provided
        if report_in.latitude is not None and not (-90.0 <= report_in.latitude <= 90.0):
            raise ValueError("Latitude must be between -90.0 and 90.0")
        if report_in.longitude is not None and not (-180.0 <= report_in.longitude <= 180.0):
            raise ValueError("Longitude must be between -180.0 and 180.0")

        report = FieldReport(
            event_id=report_in.event_id,
            location_id=report_in.location_id,
            team_id=report_in.team_id,
            reported_by=report_in.reported_by,
            report_type=report_in.report_type.upper().replace(" ", "_"),
            severity=norm_sev,
            description=report_in.description,
            latitude=report_in.latitude,
            longitude=report_in.longitude,
            location_accuracy=report_in.location_accuracy,
            location_source=report_in.location_source or "UNKNOWN",
            status="SUBMITTED",
            timestamp=datetime.now(timezone.utc)
        )
        session.add(report)
        await session.flush()

        # Handle image attachments if any storage keys passed
        created_images = []
        if report_in.image_storage_keys:
            for key in report_in.image_storage_keys:
                if key and key.strip():
                    img = FieldReportImage(
                        report_id=report.id,
                        storage_key=key.strip(),
                        mime_type="image/jpeg" if (key.endswith(".jpg") or key.endswith(".jpeg")) else "image/png",
                        file_size=0.0,
                        uploaded_by=report.reported_by,
                        created_at=datetime.now(timezone.utc),
                    )
                    session.add(img)
                    created_images.append(img)
            await session.flush()
            report.__dict__["images"] = created_images

        # Dispatch push notification to Core Command Center if configured
        try:
            from backend.app.services.fcm_provider import get_fcm_provider
            fcm = get_fcm_provider()
            await fcm.send_to_topic(
                topic="command_center_alerts",
                title=f"FIELD REPORT: {report.report_type} [{report.severity}]",
                body=f"{report.reported_by} at location {report.location_id}: {report.description[:100]}",
                data={
                    "report_id": str(report.id),
                    "location_id": str(report.location_id),
                    "severity": str(report.severity),
                    "report_type": str(report.report_type),
                },
                priority="HIGH" if report.severity in ["HIGH", "CRITICAL"] else "NORMAL"
            )
        except Exception as ex:
            logger.warning(f"FCM push notification bypass for field report: {ex}")

        logger.info(f"New field report [{report.report_type} - {report.severity}] submitted by {report.reported_by}")
        return report


    @staticmethod
    async def update_report_status(session: AsyncSession, report_id: str, update_in: FieldReportUpdate) -> Optional[FieldReport]:
        from sqlalchemy.orm import selectinload
        stmt = select(FieldReport).options(selectinload(FieldReport.images)).where(FieldReport.id == report_id)
        report = (await session.execute(stmt)).scalars().first()
        if not report:
            return None

        report.status = update_in.status
        report.reviewed_by = update_in.reviewed_by
        if update_in.review_notes:
            report.review_notes = update_in.review_notes
        report.updated_at = datetime.now(timezone.utc)
        await session.flush()
        return report

    @staticmethod
    async def get_field_reports(
        session: AsyncSession,
        location_id: Optional[str] = None,
        event_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[FieldReport]:
        from sqlalchemy.orm import selectinload
        stmt = select(FieldReport).options(selectinload(FieldReport.images))
        filters = []
        if location_id:
            filters.append(FieldReport.location_id == location_id)
        if event_id:
            filters.append(FieldReport.event_id == event_id)
        if status:
            filters.append(FieldReport.status == status)

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(FieldReport.timestamp.desc()).limit(limit)
        return list((await session.execute(stmt)).scalars().all())


    @staticmethod
    async def request_assistance(session: AsyncSession, req_in: AssistanceRequestCreate) -> AssistanceRequest:
        req = AssistanceRequest(
            event_id=req_in.event_id,
            team_id=req_in.team_id,
            request_type=req_in.request_type,
            priority=req_in.priority,
            description=req_in.description,
            latitude=req_in.latitude,
            longitude=req_in.longitude,
            status="REQUESTED"
        )
        session.add(req)

        # Update team status to NEED_ASSISTANCE
        team_stmt = select(FieldTeam).where(FieldTeam.id == req_in.team_id)
        team = (await session.execute(team_stmt)).scalars().first()
        if team:
            team.status = "NEED_ASSISTANCE"
            team.last_active_at = datetime.now(timezone.utc)

        await session.flush()
        logger.warning(f"URGENT Assistance requested by team {req_in.team_id}: {req_in.request_type} ({req_in.priority})")
        return req

    @staticmethod
    async def update_assistance_status(session: AsyncSession, request_id: str, update_in: AssistanceRequestUpdate) -> Optional[AssistanceRequest]:
        stmt = select(AssistanceRequest).where(AssistanceRequest.id == request_id)
        req = (await session.execute(stmt)).scalars().first()
        if not req:
            return None

        req.status = update_in.status
        if update_in.assigned_unit:
            req.assigned_unit = update_in.assigned_unit
        if update_in.resolution_notes:
            req.resolution_notes = update_in.resolution_notes
        req.updated_at = datetime.now(timezone.utc)
        await session.flush()
        return req

    @staticmethod
    async def get_assistance_requests(session: AsyncSession, event_id: Optional[str] = None, limit: int = 50) -> List[AssistanceRequest]:
        stmt = select(AssistanceRequest)
        if event_id:
            stmt = stmt.where(AssistanceRequest.event_id == event_id)
        stmt = stmt.order_by(AssistanceRequest.created_at.desc()).limit(limit)
        return list((await session.execute(stmt)).scalars().all())

    @staticmethod
    async def send_operational_message(session: AsyncSession, msg_in: OperationalMessageCreate) -> OperationalMessage:
        msg = OperationalMessage(
            event_id=msg_in.event_id,
            sender_id=msg_in.sender_id,
            recipient_team=msg_in.recipient_team,
            priority=msg_in.priority,
            message=msg_in.message
        )
        session.add(msg)
        await session.flush()
        logger.info(f"Operational message broadcast [{msg.priority}] to {msg.recipient_team}: {msg.message}")
        return msg

    @staticmethod
    async def acknowledge_operational_message(session: AsyncSession, message_id: str, acknowledged_by: str) -> Optional[OperationalMessage]:
        stmt = select(OperationalMessage).where(OperationalMessage.id == message_id)
        msg = (await session.execute(stmt)).scalars().first()
        if not msg:
            return None

        msg.acknowledged_at = datetime.now(timezone.utc)
        msg.acknowledged_by = acknowledged_by
        msg.read_at = datetime.now(timezone.utc)
        await session.flush()
        return msg

    @staticmethod
    async def get_operational_messages(session: AsyncSession, team_callsign: Optional[str] = None, limit: int = 20) -> List[OperationalMessage]:
        stmt = select(OperationalMessage)
        if team_callsign:
            stmt = stmt.where(or_(OperationalMessage.recipient_team == "ALL_FIELD_TEAMS", OperationalMessage.recipient_team == team_callsign))
        stmt = stmt.order_by(OperationalMessage.created_at.desc()).limit(limit)
        return list((await session.execute(stmt)).scalars().all())

    @staticmethod
    async def get_assignment_briefing(session: AsyncSession, team_id_or_callsign: str) -> Optional[FieldAssignmentResponse]:
        """Synthesizes high-priority tactical briefing for an on-ground field unit."""
        team = await FieldOperationsService.get_team_by_id_or_callsign(session, team_id_or_callsign)
        if not team:
            return None

        # Resolve assigned location
        loc_id = team.assigned_location_id or "NER-SIK-GANGTOK-01"
        loc_stmt = select(Location).where(Location.id == loc_id)
        loc = (await session.execute(loc_stmt)).scalars().first()

        # Resolve active event
        ev_stmt = (
            select(DisasterEvent)
            .where(and_(DisasterEvent.location_id == loc_id, DisasterEvent.status != "RESOLVED"))
            .order_by(DisasterEvent.updated_at.desc())
        )
        event = (await session.execute(ev_stmt)).scalars().first()

        # Resolve scientific assessment
        assess_stmt = (
            select(RiskAssessment)
            .where(RiskAssessment.location_id == loc_id)
            .order_by(RiskAssessment.timestamp.desc())
        )
        assess = (await session.execute(assess_stmt)).scalars().first()

        # Resolve latest weather observation
        obs_stmt = (
            select(WeatherObservation)
            .where(WeatherObservation.location_id == loc_id)
            .order_by(WeatherObservation.timestamp.desc())
        )
        obs = (await session.execute(obs_stmt)).scalars().first()

        # Calculate road blockage reports in sector
        road_stmt = select(FieldReport).where(
            and_(
                FieldReport.location_id == loc_id,
                FieldReport.report_type == "ROAD_BLOCKED",
                FieldReport.status.in_(["SUBMITTED", "ACKNOWLEDGED", "INCORPORATED"])
            )
        )
        road_reports = list((await session.execute(road_stmt)).scalars().all())
        road_status = f"BLOCKED ({len(road_reports)} reports)" if road_reports else "CLEAR / PASSABLE"

        # Calculate immediate conditions
        slope_risk = assess.risk_level if assess else "MODERATE"
        rainfall_state = "HIGH" if obs and (obs.rainfall_1h or 0) > 15.0 else ("MODERATE" if obs and (obs.rainfall_1h or 0) > 5.0 else "LOW")
        soil_sat = "CRITICAL" if obs and (obs.soil_moisture or 0) > 85.0 else ("HIGH" if obs and (obs.soil_moisture or 0) > 65.0 else "NORMAL")

        immediate = ImmediateConditionsSummary(
            slope_risk=slope_risk,
            rainfall_state=rainfall_state,
            soil_saturation_state=soil_sat,
            road_status=road_status,
            nearest_hazard_km=2.4
        )

        # Calculate nearby active incidents within 150km
        nearby_incidents: List[NearbyIncidentItem] = []
        all_events_stmt = select(DisasterEvent).where(DisasterEvent.status != "RESOLVED")
        all_active_events = list((await session.execute(all_events_stmt)).scalars().all())

        t_lat = team.latitude or (loc.latitude if loc else 27.3389)
        t_lon = team.longitude or (loc.longitude if loc else 88.6065)

        for ev in all_active_events:
            ev_loc = (await session.execute(select(Location).where(Location.id == ev.location_id))).scalars().first()
            if ev_loc:
                dist = FieldOperationsService.calculate_distance_km(t_lat, t_lon, ev_loc.latitude, ev_loc.longitude)
                if dist <= 150.0:
                    nearby_incidents.append(
                        NearbyIncidentItem(
                            event_id=ev.id,
                            location_id=ev_loc.id,
                            location_name=ev_loc.name,
                            hazard_type=ev.event_type,
                            severity=ev.severity,
                            risk_score=ev.risk_score,
                            distance_km=dist,
                            updated_at=ev.updated_at
                        )
                    )

        nearby_incidents.sort(key=lambda x: x.distance_km)

        # Recent messages & reports
        messages = await FieldOperationsService.get_operational_messages(session, team.callsign, limit=5)
        reports = await FieldOperationsService.get_field_reports(session, location_id=loc_id, limit=6)

        return FieldAssignmentResponse(
            team=FieldTeamResponse.model_validate(team),
            assigned_location={
                "id": loc.id,
                "name": loc.name,
                "district": loc.district,
                "state": loc.state,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "elevation": loc.elevation,
                "slope_angle": loc.slope_angle,
                "susceptibility_score": loc.susceptibility_score,
                "risk_score": assess.risk_score if assess else 10.0,
                "risk_level": assess.risk_level if assess else "LOW",
                "confidence_score": assess.confidence_score if assess else 0.85,
                "trajectory": assess.trajectory if assess else "STABLE",
                "primary_factor": assess.reason if assess else "Baseline stability",
                "rainfall_24h": obs.rainfall_24h if obs else 0.0,
                "soil_moisture": obs.soil_moisture if obs else 0.0,
            } if loc else None,

            assigned_event={
                "id": event.id,
                "hazard_type": event.event_type,
                "severity": event.severity,
                "status": event.status,
                "risk_score": event.risk_score,
                "confidence_score": assess.confidence_score if assess else 0.82,
                "summary": event.summary,
                "detected_at": event.detected_at.isoformat(),
                "updated_at": event.updated_at.isoformat()
            } if event else None,
            immediate_conditions=immediate,
            nearby_incidents=nearby_incidents,
            recent_messages=[OperationalMessageResponse.model_validate(m) for m in messages],
            recent_reports=[FieldOperationsService.format_report_response(r) for r in reports]
        )

    @staticmethod
    async def get_operations_summary(session: AsyncSession) -> FieldOperationsSummary:
        teams = await FieldOperationsService.get_all_teams(session)
        reports = await FieldOperationsService.get_field_reports(session, limit=10)
        assistance = await FieldOperationsService.get_assistance_requests(session, limit=10)

        deployed = sum(1 for t in teams if t.status in ["DEPLOYED", "ON_SCENE", "ASSISTING", "EVACUATING"])
        on_scene = sum(1 for t in teams if t.status == "ON_SCENE")
        need_assist = sum(1 for t in teams if t.status == "NEED_ASSISTANCE")
        unack_reports = sum(1 for r in reports if r.status == "SUBMITTED")
        active_assist = sum(1 for a in assistance if a.status in ["REQUESTED", "ACKNOWLEDGED"])

        return FieldOperationsSummary(
            total_teams=len(teams),
            teams_deployed=deployed,
            teams_on_scene=on_scene,
            teams_need_assistance=need_assist,
            unacknowledged_reports_count=unack_reports,
            active_assistance_requests_count=active_assist,
            teams=[FieldTeamResponse.model_validate(t) for t in teams],
            recent_reports=[FieldOperationsService.format_report_response(r) for r in reports],
            assistance_requests=[AssistanceRequestResponse.model_validate(a) for a in assistance]
        )


field_service = FieldOperationsService()
