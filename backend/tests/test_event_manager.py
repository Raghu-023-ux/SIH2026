from datetime import datetime, timezone
import pytest
from backend.app.engine.event_manager import EventManager
from backend.app.engine.base import AssessmentOutput, RiskLevel
from backend.app.models.location import Location
from backend.app.models.event import DisasterEvent


@pytest.mark.asyncio
async def test_event_lifecycle_creation_and_escalation(db_session):
    manager = EventManager()
    now = datetime.now(timezone.utc)

    location = Location(
        id="loc-event-test",
        name="Event Test Valley",
        latitude=25.5,
        longitude=91.8,
        district="East Khasi",
        state="Meghalaya",
        elevation=1400.0,
        slope_angle=35.0,
        susceptibility_score=0.8
    )
    db_session.add(location)
    await db_session.flush()

    # 1. First elevated assessment (Risk: 55 -> HIGH_RISK) -> Should create event
    assessment_1 = AssessmentOutput(
        location_id=location.id,
        timestamp=now,
        hazard_type="LANDSLIDE",
        risk_level=RiskLevel.HIGH,
        risk_score=55.0,
        confidence_score=0.9,
        reason="Elevated rainfall and soil moisture"
    )

    event_1, action_1 = await manager.process_assessment_event(db_session, location, assessment_1)
    assert action_1 == "created"
    assert event_1 is not None
    assert event_1.status == "HIGH_RISK"
    assert event_1.severity == "HIGH"
    event_id = event_1.id

    # 2. Second assessment with escalating risk (Risk: 82 -> CRITICAL) -> Should escalate SAME event, no duplicate
    assessment_2 = AssessmentOutput(
        location_id=location.id,
        timestamp=now,
        hazard_type="LANDSLIDE",
        risk_level=RiskLevel.CRITICAL,
        risk_score=82.0,
        confidence_score=0.95,
        reason="Critical pore saturation"
    )

    event_2, action_2 = await manager.process_assessment_event(db_session, location, assessment_2)
    assert action_2 == "escalated"
    assert event_2.id == event_id  # Deduplicated!
    assert event_2.status == "CRITICAL"
    assert event_2.severity == "CRITICAL"

    # 3. Third assessment returning to normal (Risk: 15 -> LOW) -> Should resolve event
    assessment_3 = AssessmentOutput(
        location_id=location.id,
        timestamp=now,
        hazard_type="LANDSLIDE",
        risk_level=RiskLevel.LOW,
        risk_score=15.0,
        confidence_score=0.9,
        reason="Baseline conditions restored"
    )

    event_3, action_3 = await manager.process_assessment_event(db_session, location, assessment_3)
    assert action_3 == "resolved"
    assert event_3.id == event_id
    assert event_3.status == "RESOLVED"
