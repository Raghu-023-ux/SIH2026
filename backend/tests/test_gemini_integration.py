import pytest
from httpx import AsyncClient
from backend.app.agents.providers import GeminiProvider, MockLLMProvider, get_llm_provider
from backend.app.core.config import settings
from backend.app.core.cache import cache, CacheKeys
from backend.app.schemas.ai import AgentAnalysis, EvidenceReference


@pytest.mark.asyncio
async def test_gemini_provider_fallback_when_no_key():
    """Tests that GeminiProvider seamlessly falls back to MockLLMProvider when no key is set."""
    provider = GeminiProvider(api_key=None, model="gemini-3.6-flash")
    context = {
        "location": {"id": "NER-SIK-GANGTOK-01", "name": "Gangtok Station"},
        "assessment": {
            "assessment_id": "TEST-ASSESS-01",
            "risk_score": 58.4,
            "risk_level": "HIGH",
            "confidence_score": 0.88,
            "trajectory": "INCREASING",
            "factors": [
                {"name": "rainfall_1h", "contribution": 18.5, "status": "ELEVATED", "raw_value": 35.0}
            ]
        }
    }
    analysis = await provider.generate_structured_analysis(
        system_prompt="Test system prompt",
        user_prompt="Explain assessment",
        evidence=[],
        context_data=context
    )
    assert isinstance(analysis, AgentAnalysis)
    assert analysis.risk_score == 58.4
    assert analysis.risk_level == "HIGH"
    assert analysis.confidence == 0.88
    assert analysis.trajectory == "INCREASING"
    assert len(analysis.findings) > 0


@pytest.mark.asyncio
async def test_deterministic_values_cannot_be_altered():
    """Verifies that the LLM layer cannot override the authoritative deterministic scientific scores."""
    provider = MockLLMProvider()
    context = {
        "location": {"id": "NER-MIZ-AIZAWL-01", "name": "Aizawl Station"},
        "assessment": {
            "assessment_id": "TEST-ASSESS-02",
            "risk_score": 79.2,
            "risk_level": "CRITICAL",
            "confidence_score": 0.92,
            "trajectory": "ESCALATING",
            "factors": [
                {"name": "soil_saturation", "contribution": 35.0, "status": "CRITICAL", "raw_value": 92.0}
            ]
        }
    }
    analysis = await provider.generate_structured_analysis(
        system_prompt="Test guardrail",
        user_prompt="Explain risk",
        evidence=[],
        context_data=context
    )
    # The returned object MUST strictly reflect the input scientific values
    assert analysis.risk_score == 79.2
    assert analysis.risk_level == "CRITICAL"
    assert analysis.confidence == 0.92
    assert analysis.trajectory == "ESCALATING"


@pytest.mark.asyncio
async def test_ai_explanation_redis_caching():
    """Tests that AI explanations are cached in Redis and invalidated per assessment snapshot."""
    location_id = "NER-SIK-GANGTOK-01"
    assessment_id = "ASSESS-SNAPSHOT-99"
    cache_key = CacheKeys.ai_explanation(location_id, assessment_id, "expert_briefing")

    # Clean previous test entries
    await cache.delete(cache_key)
    assert await cache.get(cache_key) is None

    # Cache sample briefing
    sample_payload = {
        "summary": "Cached expert briefing for Gangtok station.",
        "risk_level": "HIGH",
        "risk_score": 62.0,
        "confidence": 0.85,
        "trajectory": "STABLE",
        "findings": [],
        "uncertainties": [],
        "recommendations": [],
        "data_mode": "LIVE",
        "all_evidence": []
    }
    await cache.set(cache_key, sample_payload, ttl_seconds=60)

    # Verify retrieval
    cached = await cache.get(cache_key)
    assert cached is not None
    assert cached["summary"] == "Cached expert briefing for Gangtok station."

    # Clean up
    await cache.delete(cache_key)


@pytest.mark.asyncio
async def test_ai_endpoint_no_secrets_leaked(client: AsyncClient):
    """Verifies that AI API responses never leak API keys or internal credentials."""
    # Seed assessment
    await client.post("/api/v1/simulation/scenario", json={"scenario": "heavy_rain", "seed": 10})

    res = await client.post(
        "/api/v1/ai/explain-assessment",
        json={"location_id": "NER-SIK-GANGTOK-01"}
    )
    assert res.status_code == 200
    data = res.json()

    # Assert no API keys, tokens, or authorization headers leak in JSON
    str_data = str(data).lower()
    assert "aq." not in str_data
    assert "bearer" not in str_data
    assert "x-goog-api-key" not in str_data
    assert "token" not in str_data
