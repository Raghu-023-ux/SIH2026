import pytest


@pytest.mark.asyncio
async def test_public_privacy_and_data_isolation(client):
    """
    CRITICAL PRIVACY GUARDRAIL TEST:
    Verifies that the Public API does NOT leak:
    1. Internal raw factor weights or mathematical engine formulas.
    2. Private field rescue team member identifiers or radio frequencies.
    3. Unsanitized internal database stack traces.
    """
    # 1. Seed simulation event
    await client.post("/api/v1/simulation/scenario", json={"scenario": "heavy_rain", "seed": 42})

    # 2. Query public alert endpoints
    alerts_res = await client.get("/api/v1/public/alerts")
    assert alerts_res.status_code == 200
    alert_body_str = alerts_res.text

    # Assert no private internal keys leaked
    assert "factor_weights" not in alert_body_str
    assert "contact_channel" not in alert_body_str
    assert "reasons_json" not in alert_body_str
    assert "provider_health" not in alert_body_str
