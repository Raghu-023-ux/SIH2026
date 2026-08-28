import pytest


@pytest.mark.asyncio
async def test_simulation_progression_lifecycle(client):
    # 1. Start with Normal Scenario
    res_normal = await client.post("/api/v1/simulation/scenario", json={"scenario": "normal", "seed": 42})
    assert res_normal.status_code == 200
    data_normal = res_normal.json()
    assert data_normal["scenario"] == "normal"
    assert data_normal["assessment"]["risk_level"] == "LOW"
    assert data_normal["assessment"]["active_event"] is False

    # 2. Inject Heavy Rain Scenario
    res_heavy = await client.post("/api/v1/simulation/scenario", json={"scenario": "heavy_rain", "seed": 42})
    assert res_heavy.status_code == 200
    data_heavy = res_heavy.json()
    assert data_heavy["assessment"]["risk_score"] > data_normal["assessment"]["risk_score"]

    # 3. Inject Critical Landslide Scenario
    res_critical = await client.post("/api/v1/simulation/scenario", json={"scenario": "critical", "seed": 42})
    assert res_critical.status_code == 200
    data_critical = res_critical.json()
    assert data_critical["assessment"]["risk_level"] in ("HIGH", "CRITICAL")
    assert data_critical["assessment"]["active_event"] is True
    assert data_critical["assessment"]["event_id"] is not None

    # 4. Inject Recovery Scenario
    res_recovery = await client.post("/api/v1/simulation/scenario", json={"scenario": "recovery", "seed": 42})
    assert res_recovery.status_code == 200
    data_recovery = res_recovery.json()
    assert data_recovery["assessment"]["risk_score"] < data_critical["assessment"]["risk_score"]
    assert data_recovery["assessment"]["active_event"] is False


@pytest.mark.asyncio
async def test_simulation_invalid_scenario(client):
    response = await client.post("/api/v1/simulation/scenario", json={"scenario": "tornado_unknown"})
    assert response.status_code == 400
