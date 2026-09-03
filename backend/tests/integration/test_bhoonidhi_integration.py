import pytest
from backend.app.core.config import settings
from backend.app.services.earth_observation_provider import BhoonidhiProvider, get_earth_observation_provider


@pytest.mark.integration
@pytest.mark.asyncio
async def test_bhoonidhi_provider_integration():
    """
    Live integration test for ISRO / NRSC Bhoonidhi Open Data Gateway.
    Verifies credential presence, token authentication, and status reporting.
    Never logs or exposes user_id, password, or token.
    """
    provider = BhoonidhiProvider()
    if not provider.is_configured():
        print("\nBHOONIDHI_INTEGRATION=SKIPPED reason: BHOONIDHI_USER_ID / BHOONIDHI_PASSWORD not configured")
        pytest.skip("Bhoonidhi credentials not configured.")

    health = provider.get_health_status()
    assert health.configured is True

    # Attempt authentication
    authenticated = await provider.authenticate()
    if not authenticated:
        post_auth_health = provider.get_health_status()
        print(f"\nBHOONIDHI_INTEGRATION=FAIL status: {post_auth_health.status}")
        pytest.fail(f"Bhoonidhi integration authentication failed with status: {post_auth_health.status}")

    print("\nBHOONIDHI_INTEGRATION=PASS")
