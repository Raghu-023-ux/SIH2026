import pytest
from datetime import datetime, timezone
from backend.app.models.location import Location
from backend.app.models.event import DisasterEvent
from backend.app.engine.event_manager import event_manager
from backend.app.engine.base import AssessmentOutput, RiskLevel, RiskTrajectory, QualityStatus, DataQualityReport


@pytest.mark.asyncio
async def test_event_hysteresis_critical_downgrade(db_session):
    loc = Location(
        id="LOC-TEST-HYST",
        name="Hysteresis Test Station",
        district="East Sikkim",
        state="Sikkim",
        latitude=27.3,
        longitude=88.6,
        elevation=1600.0,
        slope_angle=35.0,
        susceptibility_score=0.8
    )
    db_session.add(loc)
    await db_session.flush()

    # 1. First trigger CRITICAL event at risk 80.0
    out_crit = AssessmentOutput(
        location_id=loc.id,
        timestamp=datetime.now(timezone.utc),
        hazard_type="LANDSLIDE",
        risk_level=RiskLevel.CRITICAL,
        risk_score=80.0,
        confidence_score=0.90,
        trajectory=RiskTrajectory.INCREASING,
        reason="Critical rainfall spike",
        factors=[],
        anomalies=[],
        trends=[],
        data_quality=DataQualityReport(QualityStatus.VALID, 1.0, 1.0)
    )

    ev, act = await event_manager.process_assessment_event(db_session, loc, out_crit)
    assert act == "created"
    assert ev.status == "CRITICAL"
    assert ev.severity == "CRITICAL"
    assert ev.peak_risk == 80.0
    assert ev.initial_risk == 80.0

    # 2. Risk drops slightly to 73.0 (above 75 - 4.0 = 71.0 buffer) -> Hysteresis should KEEP it CRITICAL
    out_drop_slight = AssessmentOutput(
        location_id=loc.id,
        timestamp=datetime.now(timezone.utc),
        hazard_type="LANDSLIDE",
        risk_level=RiskLevel.HIGH,
        risk_score=73.0,
        confidence_score=0.88,
        trajectory=RiskTrajectory.DECREASING,
        reason="Slight drop",
        factors=[],
        anomalies=[],
        trends=[],
        data_quality=DataQualityReport(QualityStatus.VALID, 1.0, 1.0)
    )

    ev, act = await event_manager.process_assessment_event(db_session, loc, out_drop_slight)
    assert ev.status == "CRITICAL" # Retained CRITICAL due to hysteresis buffer!
    assert ev.peak_risk == 80.0    # Peak risk preserved

    # 3. Risk drops further to 65.0 (below 71.0 buffer) -> Now de-escalates to HIGH
    out_drop_high = AssessmentOutput(
        location_id=loc.id,
        timestamp=datetime.now(timezone.utc),
        hazard_type="LANDSLIDE",
        risk_level=RiskLevel.HIGH,
        risk_score=65.0,
        confidence_score=0.85,
        trajectory=RiskTrajectory.DECREASING,
        reason="De-escalating",
        factors=[],
        anomalies=[],
        trends=[],
        data_quality=DataQualityReport(QualityStatus.VALID, 1.0, 1.0)
    )

    ev, act = await event_manager.process_assessment_event(db_session, loc, out_drop_high)
    assert ev.status == "HIGH"
    assert act == "deescalated"
    assert ev.peak_risk == 80.0

    # 4. Risk drops to 15.0 -> Resolves event
    out_low = AssessmentOutput(
        location_id=loc.id,
        timestamp=datetime.now(timezone.utc),
        hazard_type="LANDSLIDE",
        risk_level=RiskLevel.LOW,
        risk_score=15.0,
        confidence_score=0.90,
        trajectory=RiskTrajectory.DECREASING,
        reason="Clear weather",
        factors=[],
        anomalies=[],
        trends=[],
        data_quality=DataQualityReport(QualityStatus.VALID, 1.0, 1.0)
    )

    ev, act = await event_manager.process_assessment_event(db_session, loc, out_low)
    assert ev.status == "RESOLVED"
    assert act == "resolved"
