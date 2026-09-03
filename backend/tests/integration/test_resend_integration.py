import pytest
import os
import httpx
from backend.app.core.config import settings


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resend_email_provider_integration():
    """
    Live integration test for Resend Email Provider.
    Level 1: Verifies API key configuration.
    Level 2: Sends a test email ONLY if RUN_EMAIL_INTEGRATION_TESTS=true and INTEGRATION_TEST_EMAIL is set.
    Never logs or exposes RESEND_API_KEY.
    """
    api_key = os.getenv("RESEND_API_KEY") or getattr(settings, "RESEND_API_KEY", None)
    if not api_key:
        print("\nRESEND_INTEGRATION=SKIPPED reason: RESEND_API_KEY not configured")
        pytest.skip("RESEND_API_KEY not configured for integration test.")

    run_email_send = os.getenv("RUN_EMAIL_INTEGRATION_TESTS", "").lower() == "true"
    test_email = os.getenv("INTEGRATION_TEST_EMAIL")

    if not run_email_send or not test_email:
        print("\nRESEND_INTEGRATION=SKIPPED reason: RUN_EMAIL_INTEGRATION_TESTS / INTEGRATION_TEST_EMAIL not set")
        pytest.skip("Email dispatch test skipped (set RUN_EMAIL_INTEGRATION_TESTS=true and INTEGRATION_TEST_EMAIL to test live dispatch).")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "from": getattr(settings, "RESEND_FROM_EMAIL", "onboarding@resend.dev"),
        "to": [test_email],
        "subject": "SIH26001 Disaster Intelligence Command Center - Automated Integration Test",
        "html": "<p>This is an automated integration test email from the SIH26001 Disaster Intelligence Platform.</p>"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post("https://api.resend.com/emails", headers=headers, json=payload)
            if res.status_code not in (200, 201):
                print(f"\nRESEND_INTEGRATION=FAIL HTTP {res.status_code}")
                pytest.fail(f"Resend API returned error HTTP {res.status_code}")

        print("\nRESEND_INTEGRATION=PASS")
    except Exception as err:
        print(f"\nRESEND_INTEGRATION=FAIL reason: {err}")
        pytest.fail(f"Resend integration test failed: {err}")
