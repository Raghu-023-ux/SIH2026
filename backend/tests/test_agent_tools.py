import pytest
from backend.app.agents.tools import agent_tools
from backend.app.models.location import Location


@pytest.mark.asyncio
async def test_agent_tools_location_retrieval(db_session):
    # 1. Valid location
    loc_data = await agent_tools.get_location(db_session, "NER-SIK-GANGTOK-01")
    assert "error" not in loc_data
    assert "Gangtok" in loc_data["name"]
    assert loc_data["state"] == "Sikkim"
    assert loc_data["slope_angle_deg"] > 0

    # 2. Invalid location
    inv_data = await agent_tools.get_location(db_session, "INVALID-LOC-999")
    assert "error" in inv_data


@pytest.mark.asyncio
async def test_agent_tools_assessment_and_history(client, db_session):
    # First inject scenario to populate assessment
    sim_res = await client.post("/api/v1/simulation/scenario", json={"scenario": "heavy_rain", "seed": 42})
    assert sim_res.status_code == 200

    # Test get_current_assessment
    assess_data = await agent_tools.get_current_assessment(db_session, "NER-SIK-GANGTOK-01")
    assert "error" not in assess_data
    assert assess_data["risk_score"] > 0
    assert len(assess_data["factors"]) > 0

    # Test get_assessment_history
    hist_data = await agent_tools.get_assessment_history(db_session, "NER-SIK-GANGTOK-01", limit=5)
    assert hist_data["count"] >= 1
    assert len(hist_data["history"]) >= 1


@pytest.mark.asyncio
async def test_agent_tools_nearby_and_quality(db_session):
    # Test get_nearby_risk
    nearby = await agent_tools.get_nearby_risk(db_session, "NER-SIK-GANGTOK-01", radius_km=500.0)
    assert "target_location" in nearby
    assert nearby["nearby_stations_count"] >= 1

    # Test get_data_quality
    quality = await agent_tools.get_data_quality(db_session, "NER-SIK-GANGTOK-01")
    assert "data_mode" in quality
