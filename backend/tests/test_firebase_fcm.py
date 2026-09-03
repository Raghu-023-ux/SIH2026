import pytest
from httpx import AsyncClient
from backend.app.services.fcm_provider import MockFCMProvider, FirebaseAdminFCMProvider, get_fcm_provider
from backend.app.services.device_service import DeviceService
from backend.app.schemas.device import DeviceRegisterRequest, DeviceUpdateRequest
from backend.app.schemas.alerting import BroadcastCreate
from backend.app.services.broadcast_service import BroadcastService


@pytest.mark.asyncio
async def test_mock_fcm_provider_dispatch():
    """Tests MockFCMProvider deterministic push delivery and error simulation."""
    provider = MockFCMProvider()
    
    # 1. Valid token push
    res = await provider.send_to_token(
        fcm_token="sample_valid_fcm_token_1234567890",
        title="Landslide Warning",
        body="High risk detected in Gangtok sector.",
        data={"event_id": "EVT-100", "severity": "HIGH"},
        priority="CRITICAL"
    )
    assert res["status"] == "SENT_TO_FCM"
    assert "message_id" in res
    assert res["priority"] == "CRITICAL"

    # 2. Invalid/expired token simulation
    res_invalid = await provider.send_to_token(
        fcm_token="invalid_token_99999",
        title="Test Alert",
        body="Test Body"
    )
    assert res_invalid["status"] == "TOKEN_INVALID"

    # 3. Topic broadcast
    res_topic = await provider.send_to_topic(
        topic="region:sikkim",
        title="Regional Advisory",
        body="Monsoon rainfall surge expected."
    )
    assert res_topic["status"] == "SENT_TO_FCM"
    assert res_topic["topic"] == "region:sikkim"


@pytest.mark.asyncio
async def test_device_registration_endpoint(client: AsyncClient):
    """Tests POST /api/v1/notifications/devices endpoint and idempotency."""
    payload = {
        "fcm_token": "fcm_test_token_alpha_9876543210",
        "platform": "ANDROID",
        "user_id": "user_citizen_001",
        "device_name": "Google Pixel 8",
        "app_version": "1.0.0",
        "latitude": 27.3389,
        "longitude": 88.6065,
        "topic_subscriptions": ["region:sikkim", "region:gangtok"]
    }

    # 1. First registration -> Created
    res1 = await client.post("/api/v1/notifications/devices", json=payload)
    assert res1.status_code == 201
    data1 = res1.json()
    assert data1["fcm_token"] == payload["fcm_token"]
    assert data1["platform"] == "ANDROID"
    assert data1["is_active"] is True
    dev_id = data1["id"]

    # 2. Second registration with updated coordinates -> Same device ID (Idempotent)
    payload["latitude"] = 27.3450
    payload["app_version"] = "1.0.1"
    res2 = await client.post("/api/v1/notifications/devices", json=payload)
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["id"] == dev_id
    assert data2["latitude"] == 27.3450
    assert data2["app_version"] == "1.0.1"


@pytest.mark.asyncio
async def test_device_update_and_deactivation_endpoints(client: AsyncClient):
    """Tests PUT and DELETE /api/v1/notifications/devices endpoints."""
    token = "fcm_token_to_update_and_delete_12345"
    reg_payload = {
        "fcm_token": token,
        "platform": "IOS",
        "latitude": 27.0,
        "longitude": 88.0
    }
    await client.post("/api/v1/notifications/devices", json=reg_payload)

    # 1. Update location
    update_res = await client.put(
        f"/api/v1/notifications/devices/{token}",
        json={"latitude": 27.1234, "longitude": 88.5678, "app_version": "2.0.0"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["latitude"] == 27.1234

    # 2. Deactivate / Unregister
    del_res = await client.delete(f"/api/v1/notifications/devices/{token}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "DEACTIVATED"

    # 3. Verify in list
    list_res = await client.get("/api/v1/notifications/devices?active_only=false")
    assert list_res.status_code == 200
    devices = list_res.json()
    matching = [d for d in devices if d["fcm_token"] == token]
    assert len(matching) == 1
    assert matching[0]["is_active"] is False


@pytest.mark.asyncio
async def test_broadcast_with_fcm_channel(client: AsyncClient, db_session):
    """Tests creating a Broadcast with FCM channel and processing background notifications."""
    # Register an active test device
    test_token = "fcm_broadcast_recipient_token_111222333"
    await client.post(
        "/api/v1/notifications/devices",
        json={
            "fcm_token": test_token,
            "platform": "ANDROID",
            "latitude": 27.3389,
            "longitude": 88.6065
        }
    )

    # 1. Create Broadcast with FCM channel
    broadcast_payload = {
        "title": "Severe Rain & Slope Movement Warning",
        "message": "Immediate precautionary evacuation along NH10 corridor.",
        "priority": "CRITICAL",
        "target_type": "PUBLIC_USERS",
        "channels": ["IN_APP", "SMS", "FCM"]
    }
    res = await client.post("/api/v1/alerts/broadcast", json=broadcast_payload)
    assert res.status_code == 201
    b_data = res.json()
    broadcast_id = b_data["id"]

    # 2. Check Broadcast Status
    status_res = await client.get(f"/api/v1/alerts/broadcasts/{broadcast_id}")
    assert status_res.status_code == 200
    s_data = status_res.json()
    assert s_data["total_recipients"] > 0
    # Notification item channels contain FCM
    fcm_notifs = [n for n in s_data["notifications"] if n["channel"] == "FCM"]
    assert len(fcm_notifs) >= 1


@pytest.mark.asyncio
async def test_invalid_fcm_token_auto_deactivation(db_session):
    """Tests that an invalid token returned during broadcast dispatch is deactivated in PostgreSQL."""
    invalid_token = "invalid_device_token_xyz999"
    # Register invalid token
    dev_req = DeviceRegisterRequest(
        fcm_token=invalid_token,
        platform="ANDROID"
    )
    dev = await DeviceService.register_or_update_device(db_session, dev_req)
    await db_session.commit()
    assert dev.is_active is True

    # Dispatch broadcast targeting this token
    b_req = BroadcastCreate(
        title="Test Alert",
        message="Testing auto deactivation",
        priority="HIGH",
        target_type="PUBLIC_USERS",
        channels=["FCM"]
    )
    broadcast = await BroadcastService.create_broadcast(db_session, b_req)
    
    # Process notifications using db_session
    await BroadcastService.process_broadcast(db_session, broadcast.id)

    # Refresh device state from DB
    updated_dev = await DeviceService.update_device_location_or_preferences(
        db_session,
        invalid_token,
        DeviceUpdateRequest()
    )
    assert updated_dev.is_active is False
    assert updated_dev.deactivation_reason == "TOKEN_INVALID"



@pytest.mark.asyncio
async def test_send_test_push_endpoint(client: AsyncClient):
    """Tests POST /api/v1/notifications/send-test for administrative/testing workflows."""
    res_topic = await client.post(
        "/api/v1/notifications/send-test",
        json={
            "topic": "region:all",
            "title": "System Drill Alert",
            "body": "This is a simulated disaster communication test.",
            "priority": "HIGH"
        }
    )
    assert res_topic.status_code == 200
    assert res_topic.json()["status"] == "SENT_TO_FCM"
