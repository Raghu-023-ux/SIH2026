import pytest
from backend.app.agents.orchestrator import agent_orchestrator


def test_orchestrator_intent_classification():
    # 1. Explicit agent type
    assert agent_orchestrator.classify_intent("any question", "investigation") == "investigation"
    assert agent_orchestrator.classify_intent("any question", "explanation") == "explanation"
    assert agent_orchestrator.classify_intent("any question", "analyst") == "analyst"

    # 2. Inferred investigation intent
    assert agent_orchestrator.classify_intent("Why did risk change over the past 3 hours?", "auto") == "investigation"
    assert agent_orchestrator.classify_intent("What is the history and delta of this event?", "auto") == "investigation"

    # 3. Inferred explanation intent
    assert agent_orchestrator.classify_intent("Explain why risk is at this level", "auto") == "explanation"
    assert agent_orchestrator.classify_intent("What is the meaning of these factor contributions?", "auto") == "explanation"

    # 4. Inferred analyst default intent
    assert agent_orchestrator.classify_intent("What are the recommended actions?", "auto") == "analyst"
    assert agent_orchestrator.classify_intent(None, "auto") == "analyst"


@pytest.mark.asyncio
async def test_orchestrator_execution(client, db_session):
    # Seed assessment via scenario
    await client.post("/api/v1/simulation/scenario", json={"scenario": "heavy_rain", "seed": 42})

    response = await agent_orchestrator.execute(
        session=db_session,
        location_id="NER-SIK-GANGTOK-01",
        question="Provide full situational analysis.",
        agent_type="auto"
    )

    assert response.agent == "analyst"
    assert response.analysis.risk_score > 0
    assert len(response.evidence) > 0
    assert response.latency_ms >= 0.0
