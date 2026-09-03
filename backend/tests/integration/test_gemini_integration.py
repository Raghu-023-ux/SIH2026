import pytest
import os
import httpx
from backend.app.core.config import settings


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gemini_llm_provider_integration():
    """
    Live integration test for Google AI Studio Gemini API provider.
    Verifies backend communication directly with minimal deterministic prompt ('Return exactly OK.').
    Never logs or exposes GEMINI_API_KEY.
    """
    api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
    if not api_key:
        print("\nGEMINI_INTEGRATION=SKIPPED reason: GEMINI_API_KEY not configured")
        pytest.skip("GEMINI_API_KEY not configured for integration test.")

    model = getattr(settings, "GEMINI_MODEL", "gemini-3.6-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": "Return exactly the word OK."}]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 10}
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url, json=payload)
            if res.status_code != 200:
                print(f"\nGEMINI_INTEGRATION=FAIL HTTP {res.status_code}")
                pytest.fail(f"Gemini API returned error HTTP {res.status_code}")

            data = res.json()
            assert "candidates" in data
            text_out = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            assert len(text_out) > 0

        print("\nGEMINI_INTEGRATION=PASS")
    except Exception as err:
        print(f"\nGEMINI_INTEGRATION=FAIL reason: {err}")
        pytest.fail(f"Gemini integration test failed: {err}")
