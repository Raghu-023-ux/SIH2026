import pytest
from sqlalchemy import select
from backend.app.models.event import DisasterEvent
from backend.app.services.multichannel_service import multichannel_service
from backend.app.schemas.alerting import BroadcastTriggerRequest


@pytest.mark.asyncio
async def test_multichannel_payload_formatting(client, db_session):
    # Seed event
    await client.post("/api/v1/simulation/scenario", json={"scenario": "heavy_rain", "seed": 42})

    events = list((await db_session.execute(select(DisasterEvent))).scalars().all())
    ev = events[0]

    pkg = await multichannel_service.build_payload_package(db_session, ev.id)
    assert pkg is not None

    # Verify SMS 160-char constraint
    assert pkg.sms.is_within_160_chars is True
    assert pkg.sms.character_count <= 160
    assert len(pkg.sms.text_hi) > 5

    # Verify WhatsApp formatting
    assert "URGENT LANDSLIDE SAFETY WARNING" in pkg.whatsapp.body
    assert "http" in pkg.whatsapp.action_url

    # Verify Email HTML
    assert "<h2>" in pkg.email.html_body
    assert "Landslide" in pkg.email.subject


@pytest.mark.asyncio
async def test_multichannel_broadcast_execution(client, db_session):
    # Seed event first
    await client.post("/api/v1/simulation/scenario", json={"scenario": "heavy_rain", "seed": 42})

    events = list((await db_session.execute(select(DisasterEvent))).scalars().all())
    assert len(events) >= 1
    ev = events[0]

    req = BroadcastTriggerRequest(
        event_id=ev.id,
        location_id=ev.location_id,
        channels=["SMS_GATEWAY", "WHATSAPP_BROADCAST", "CAP_FEED"],
        recipient_group="PUBLIC_AND_OFFICIALS"
    )
    resp = await multichannel_service.dispatch_broadcast(db_session, req)
    assert resp.total_dispatched == 3
    assert len(resp.dispatch_logs) == 3
    assert resp.dispatch_logs[0].status == "DISPATCHED"

    # Verify dispatch logs query
    logs = await multichannel_service.get_dispatch_logs(db_session, limit=10)
    assert len(logs) >= 3
