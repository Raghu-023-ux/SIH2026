import pytest
from httpx import AsyncClient
from backend.app.services.email_provider import MockEmailProvider, ResendEmailProvider, get_email_provider
from backend.app.services.email_templates import EmailTemplateRenderer
from backend.app.schemas.alerting import BroadcastCreate
from backend.app.services.broadcast_service import BroadcastService


@pytest.mark.asyncio
async def test_mock_email_provider_dispatch():
    """Tests MockEmailProvider dispatch and failure simulation."""
    provider = MockEmailProvider()

    # 1. Successful operational dispatch
    res = await provider.send_email(
        to="duty.officer@sikkim.gov.in",
        subject="[CRITICAL] Landslide Early Warning",
        html_body="<h2>Critical Hazard Alert</h2><p>Evacuate slope perimeter.</p>",
        text_body="Critical Hazard Alert: Evacuate slope perimeter."
    )
    assert res["status"] == "SENT_TO_PROVIDER"
    assert "message_id" in res
    assert res["sender"] == "onboarding@resend.dev"

    # 2. Simulated invalid recipient failure
    res_fail = await provider.send_email(
        to="invalid@domain.test",
        subject="Test Alert",
        html_body="<p>Test</p>"
    )
    assert res_fail["status"] == "FAILED"
    assert "rejected" in res_fail["failure_reason"].lower()


@pytest.mark.asyncio
async def test_email_template_renderer():
    """Tests HTML entity escaping and structured template output for expert alerts."""
    factors = [
        {"name": "rainfall_1h", "raw_value": 45.0, "contribution": 25.0},
        {"name": "soil_saturation", "raw_value": 82.0, "contribution": 30.0}
    ]
    rendered = EmailTemplateRenderer.render_expert_alert(
        location_name="Gangtok Ridge <Station 1>",
        district="East Sikkim",
        state="Sikkim",
        risk_score=72.5,
        risk_level="HIGH",
        confidence=0.88,
        trajectory="INCREASING",
        primary_drivers=factors,
        data_quality_score=0.95,
        event_id="EVT-TEST-001",
        app_base_url="https://sih26001-disaster.gov.in"
    )

    assert "Gangtok Ridge &lt;Station 1&gt;" in rendered["html"]  # Escaped
    assert "[HIGH] Landslide Risk Assessment" in rendered["subject"]
    assert "72.5/100" in rendered["html"]
    assert "88%" in rendered["html"]
    assert "https://sih26001-disaster.gov.in/analytics?event_id=EVT-TEST-001" in rendered["html"]


@pytest.mark.asyncio
async def test_broadcast_with_email_channel(client: AsyncClient, db_session):
    """Tests creating a Broadcast with EMAIL channel and verifying notification records."""
    broadcast_payload = {
        "title": "Severe Precipitation & Debris Scour Warning",
        "message": "High landslide potential along transit arteries in Gangtok sector.",
        "priority": "CRITICAL",
        "target_type": "FIELD_TEAMS",
        "target_filter": {"emails": ["responder.unit@sikkim.gov.in", "command.chief@ner.gov.in"]},
        "channels": ["IN_APP", "SMS", "FCM", "EMAIL"]
    }
    res = await client.post("/api/v1/alerts/broadcast", json=broadcast_payload)
    assert res.status_code == 201
    b_data = res.json()
    broadcast_id = b_data["id"]

    # Check status
    status_res = await client.get(f"/api/v1/alerts/broadcasts/{broadcast_id}")
    assert status_res.status_code == 200
    s_data = status_res.json()
    assert s_data["total_recipients"] > 0
    
    email_notifs = [n for n in s_data["notifications"] if n["channel"] == "EMAIL"]
    assert len(email_notifs) == 2


@pytest.mark.asyncio
async def test_email_failure_isolation_preserves_assessment(db_session):
    """Verifies that an email provider failure never affects or rolls back the core assessment."""
    # Create broadcast with a failing recipient
    b_req = BroadcastCreate(
        title="Failure Isolation Test",
        message="Checking resilience against email gateway failure",
        priority="HIGH",
        target_type="CUSTOM_GROUP",
        target_filter={"emails": ["invalid@bounce-test.org"]},
        channels=["EMAIL"]
    )
    broadcast = await BroadcastService.create_broadcast(db_session, b_req)
    
    # Process broadcast
    await BroadcastService.process_broadcast(db_session, broadcast.id)

    status_resp = await BroadcastService.get_broadcast_status(db_session, broadcast.id)
    assert status_resp.email_failed == 1
    # Broadcast entity remains intact in PostgreSQL
    assert status_resp.id == broadcast.id
