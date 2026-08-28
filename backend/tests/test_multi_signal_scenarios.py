import pytest
from datetime import datetime, timezone
from backend.app.models.location import Location
from backend.app.services.simulation_service import SimulationService
from backend.app.schemas.simulation import SimulationScenarioRequest


@pytest.mark.asyncio
async def test_all_simulation_scenarios(db_session):
    loc = Location(
        id="SIM-TEST-GANGTOK-01",
        name="Gangtok Ridge Simulation Station",
        district="East Sikkim",
        state="Sikkim",
        latitude=27.3389,
        longitude=88.6065,
        elevation=1650.0,
        slope_angle=38.0,
        susceptibility_score=0.82
    )
    db_session.add(loc)
    await db_session.flush()

    # 1. Normal scenario
    req_norm = SimulationScenarioRequest(scenario="normal", location_id=loc.id, seed=42)
    res_norm = await SimulationService.run_scenario(db_session, req_norm)
    assert res_norm.assessment.risk_score < 35.0
    assert res_norm.assessment.risk_level in ("LOW", "MODERATE")

    # 2. Heavy Rain scenario
    req_heavy = SimulationScenarioRequest(scenario="heavy_rain", location_id=loc.id, seed=42)
    res_heavy = await SimulationService.run_scenario(db_session, req_heavy)
    assert res_heavy.assessment.risk_score > res_norm.assessment.risk_score

    # 3. Persistent Rain scenario
    req_pers = SimulationScenarioRequest(scenario="persistent_rain", location_id=loc.id, seed=42)
    res_pers = await SimulationService.run_scenario(db_session, req_pers)
    assert res_pers.assessment.risk_score >= 45.0
    assert any(f["name"] == "Rainfall Persistence & Trend" for f in res_pers.assessment.factors)

    # 4. Critical scenario
    req_crit = SimulationScenarioRequest(scenario="critical", location_id=loc.id, seed=42)
    res_crit = await SimulationService.run_scenario(db_session, req_crit)
    assert res_crit.assessment.risk_score >= 70.0
    assert res_crit.assessment.risk_level in ("HIGH", "CRITICAL")
    assert res_crit.assessment.active_event is True

    # 5. Recovery scenario
    req_rec = SimulationScenarioRequest(scenario="recovery", location_id=loc.id, seed=42)
    res_rec = await SimulationService.run_scenario(db_session, req_rec)
    assert res_rec.assessment.risk_score < res_crit.assessment.risk_score
