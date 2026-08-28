from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.event import DisasterEvent
from backend.app.models.location import Location
from backend.app.engine.base import AssessmentOutput, RiskLevel, EventStatus
from backend.app.core.config import settings
from backend.app.core.logging import logger


class EventManager:
    """
    Manages the lifecycle, state transitions, and deduplication of DisasterEvent entities.
    Prevents redundant event creation and tracks worsening, improving, or resolving disaster situations.
    """

    def determine_event_status_and_severity(self, risk_score: float) -> Tuple[str, str]:
        """
        Maps risk score to EventStatus and DisasterEvent severity string.
        """
        if risk_score >= settings.THRESHOLD_CRITICAL:  # >= 75
            return EventStatus.CRITICAL.value, "CRITICAL"
        elif risk_score >= settings.THRESHOLD_HIGH:     # >= 50
            return EventStatus.HIGH_RISK.value, "HIGH"
        elif risk_score >= 40.0:                        # 40 - 49.9
            return EventStatus.ELEVATED.value, "MODERATE"
        elif risk_score >= settings.THRESHOLD_MODERATE: # 25 - 39.9
            return EventStatus.WATCH.value, "LOW"
        else:
            return EventStatus.NORMAL.value, "LOW"

    async def get_active_event(
        self,
        session: AsyncSession,
        location_id: str,
        event_type: str = "LANDSLIDE"
    ) -> Optional[DisasterEvent]:
        """
        Fetches an active non-resolved disaster event for the specified location.
        """
        query = select(DisasterEvent).where(
            and_(
                DisasterEvent.location_id == location_id,
                DisasterEvent.event_type == event_type,
                DisasterEvent.status != EventStatus.RESOLVED.value
            )
        ).order_by(DisasterEvent.detected_at.desc())

        result = await session.execute(query)
        return result.scalars().first()

    async def process_assessment_event(
        self,
        session: AsyncSession,
        location: Location,
        assessment: AssessmentOutput
    ) -> Tuple[Optional[DisasterEvent], str]:
        """
        Processes risk assessment against the event lifecycle state machine.
        Returns: (event_instance_or_none, lifecycle_action_string)
        Actions: 'created', 'escalated', 'deescalated', 'updated', 'resolved', 'none'
        """
        active_event = await self.get_active_event(session, location.id, assessment.hazard_type)
        new_status, new_severity = self.determine_event_status_and_severity(assessment.risk_score)
        now = datetime.now(timezone.utc)

        # Case 1: Risk is low (< 25)
        if new_status == EventStatus.NORMAL.value:
            if active_event:
                # Active event has now subsided -> transition to RESOLVED
                active_event.status = EventStatus.RESOLVED.value
                active_event.risk_score = assessment.risk_score
                active_event.confidence_score = assessment.confidence_score
                active_event.updated_at = now
                active_event.summary = (
                    f"Resolved: Landslide risk at {location.name} returned to safe baseline "
                    f"(Score: {assessment.risk_score:.1f}, {assessment.risk_level.value})."
                )
                logger.info(f"Resolved DisasterEvent {active_event.id} for location {location.name}")
                return active_event, "resolved"
            else:
                # Normal conditions, no active event needed
                return None, "none"

        # Case 2: Risk is elevated (>= 25) but NO active event currently exists -> Create new event
        if not active_event:
            est_peak = now + timedelta(hours=12) if assessment.is_increasing_rain else now + timedelta(hours=6)
            est_start = now if assessment.risk_score >= settings.THRESHOLD_HIGH else now + timedelta(hours=3)

            summary = (
                f"Active {new_status} alert: Potential landslide activity detected at {location.name}, "
                f"{location.district}, {location.state}. Risk Score: {assessment.risk_score:.1f}/100. {assessment.reason}"
            )

            new_event = DisasterEvent(
                event_type=assessment.hazard_type,
                location_id=location.id,
                status=new_status,
                severity=new_severity,
                risk_score=assessment.risk_score,
                confidence_score=assessment.confidence_score,
                detected_at=now,
                updated_at=now,
                expected_start=est_start,
                expected_peak=est_peak,
                affected_area=f"{location.name} and surrounding {location.district} hill slopes",
                summary=summary
            )
            session.add(new_event)
            await session.flush()
            logger.info(f"Created new DisasterEvent {new_event.id} [{new_status}] for location {location.name}")
            return new_event, "created"

        # Case 3: Active event ALREADY exists -> Update existing event state
        prev_score = active_event.risk_score
        active_event.updated_at = now
        active_event.risk_score = assessment.risk_score
        active_event.confidence_score = assessment.confidence_score

        if assessment.risk_score > prev_score + 3.0:
            action = "escalated"
            active_event.status = new_status
            active_event.severity = new_severity
            active_event.summary = (
                f"ESCALATED to {new_status}: Landslide hazard increasing at {location.name} "
                f"(Risk: {prev_score:.1f} -> {assessment.risk_score:.1f}). {assessment.reason}"
            )
            logger.info(f"Escalated DisasterEvent {active_event.id} for {location.name} to {new_status}")
        elif assessment.risk_score < prev_score - 3.0:
            action = "deescalated"
            active_event.status = new_status
            active_event.severity = new_severity
            active_event.summary = (
                f"Easing: Landslide hazard decreasing at {location.name} "
                f"(Risk: {prev_score:.1f} -> {assessment.risk_score:.1f}, Status: {new_status})."
            )
            logger.info(f"De-escalated DisasterEvent {active_event.id} for {location.name} to {new_status}")
        else:
            action = "updated"
            active_event.status = new_status
            active_event.severity = new_severity
            logger.debug(f"Updated DisasterEvent {active_event.id} for {location.name}")

        return active_event, action
