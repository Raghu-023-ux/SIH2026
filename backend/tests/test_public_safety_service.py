import pytest
from backend.app.services.public_safety_service import (
    PublicAlertPolicy,
    SafetyGuidanceService,
    public_safety_service,
)


def test_public_alert_policy_evaluations():
    # 1. Critical event inside immediate zone (<= 12km)
    alert, status, zone, title, summary = PublicAlertPolicy.evaluate_policy(
        severity="CRITICAL",
        event_status="ACTIVE",
        distance_km=5.0
    )
    assert alert is True
    assert status == "URGENT"
    assert zone == "CRITICAL_ZONE"

    # 2. Critical event in affected perimeter (12-25km)
    alert, status, zone, _, _ = PublicAlertPolicy.evaluate_policy(
        severity="CRITICAL",
        event_status="ACTIVE",
        distance_km=20.0
    )
    assert alert is True
    assert status == "URGENT"
    assert zone == "AFFECTED_ZONE"

    # 3. High event within 15km
    alert, status, zone, _, _ = PublicAlertPolicy.evaluate_policy(
        severity="HIGH",
        event_status="ACTIVE",
        distance_km=8.0
    )
    assert alert is True
    assert status == "ALERT"
    assert zone == "AFFECTED_ZONE"

    # 4. Resolved event returns NO_ALERT
    alert, status, zone, _, _ = PublicAlertPolicy.evaluate_policy(
        severity="CRITICAL",
        event_status="RESOLVED",
        distance_km=2.0
    )
    assert alert is False
    assert status == "NO_ALERT"
    assert zone == "SAFE_ZONE"


def test_safety_guidance_service_rules():
    # Urgent/Alert Landslide guidance
    guidance = SafetyGuidanceService.get_guidance_for_hazard("LANDSLIDE", "URGENT")
    assert len(guidance) >= 4
    categories = [g.category for g in guidance]
    assert "DO" in categories
    assert "DONT" in categories

    # Verify conservative wording
    instructions_text = " ".join([g.instruction for g in guidance])
    assert "steep" in instructions_text.lower() or "slope" in instructions_text.lower()


@pytest.mark.asyncio
async def test_public_risk_service_safety_points_and_ack(db_session):
    # Test seeding and safety points
    points = await public_safety_service.get_all_safety_points(db_session)
    assert len(points) >= 3
    gangtok_pt = next((p for p in points if "NER-SIK-GANGTOK-01" == p.location_id), None)
    assert gangtok_pt is not None
    assert gangtok_pt.availability == "OPEN"
