import pytest
from backend.app.agents.orchestrator import agent_orchestrator
from backend.app.engine.pipeline import disaster_engine
from backend.app.services.location_service import LocationService
from backend.app.core.config import settings


@pytest.mark.asyncio
async def test_agent_scientific_invariance_guardrail(client, db_session):
    """
    CRITICAL GUARDRAIL TEST:
    Verifies that the Agentic AI layer NEVER alters, mutates, or overrides
    the scientific engine's mathematical risk score, risk level, or confidence.
    """
    # 1. Run scientific engine to establish authoritative baseline
    loc = await LocationService.get_location_by_id(db_session, "NER-SIK-GANGTOK-01")
    engine_output, _, _ = await disaster_engine.evaluate_location(db_session, loc, force_fresh=False)
    await db_session.flush()

    authoritative_score = engine_output.risk_score
    authoritative_level = engine_output.risk_level.value
    authoritative_conf = engine_output.confidence_score

    # 2. Run all three specialized agents
    for agent_type in ["analyst", "investigation", "explanation"]:
        ai_resp = await agent_orchestrator.execute(
            session=db_session,
            location_id="NER-SIK-GANGTOK-01",
            question="Analyze the current disaster state.",
            agent_type=agent_type
        )

        # Assert zero alteration of scientific values
        assert ai_resp.analysis.risk_score == pytest.approx(authoritative_score, rel=1e-3)
        assert ai_resp.analysis.risk_level == authoritative_level
        assert ai_resp.analysis.confidence == pytest.approx(authoritative_conf, rel=1e-3)

        # Assert evidence citations exist
        assert len(ai_resp.evidence) > 0


@pytest.mark.asyncio
async def test_agent_simulation_mode_awareness(client, db_session):
    """
    Verifies that agent responses explicitly indicate simulation mode
    when the system is operating under simulated data feeds.
    """
    settings.DATA_MODE = "SIMULATION"

    ai_resp = await agent_orchestrator.execute(
        session=db_session,
        location_id="NER-SIK-GANGTOK-01",
        question="What is the current risk status?",
        agent_type="analyst"
    )

    assert ai_resp.data_mode == "SIMULATION"
    assert "SIMULATION" in ai_resp.answer or "simulated" in ai_resp.answer.lower()
