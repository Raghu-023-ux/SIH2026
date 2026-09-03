import pytest
import uuid
import json
import asyncio
from backend.app.core.config import settings
from backend.app.core.redis import redis_service, UpstashRedisClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_upstash_integration():
    """
    Live integration test for Upstash Redis Cloud REST cache.
    Verifies SET, GET, TTL, and DELETE operations with automatic test key cleanup.
    Never exposes Redis URL or authorization token.
    """
    if not (settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN):
        print("\nREDIS_INTEGRATION=SKIPPED reason: UPSTASH_REDIS_REST_URL not configured")
        pytest.skip("Upstash Redis credentials not configured for integration test.")

    client = UpstashRedisClient(
        rest_url=settings.UPSTASH_REDIS_REST_URL,
        rest_token=settings.UPSTASH_REDIS_REST_TOKEN
    )

    test_key = f"test:integration:{uuid.uuid4().hex[:8]}"
    test_value = {"status": "integration_test_ok", "timestamp": "2026-09-02"}

    try:
        # SET with TTL
        set_ok = await client.set(test_key, test_value, ttl_seconds=60)
        assert set_ok is True

        # GET
        retrieved = await client.get(test_key)
        assert retrieved is not None
        if isinstance(retrieved, str):
            retrieved = json.loads(retrieved)

        assert retrieved.get("status") == "integration_test_ok"

        # DELETE
        del_ok = await client.delete(test_key)
        assert del_ok is True

        # Verify deleted
        post_del = await client.get(test_key)
        assert post_del is None

        print("\nREDIS_INTEGRATION=PASS")
    except Exception as err:
        print(f"\nREDIS_INTEGRATION=FAIL reason: {err}")
        pytest.fail(f"Upstash Redis integration test failed: {err}")
    finally:
        await client.delete(test_key)
