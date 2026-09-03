import pytest
import asyncio
from backend.app.core.redis import RedisService, InMemoryTTLCache, RateLimiter
from backend.app.core.cache import CacheKeys


@pytest.mark.asyncio
async def test_in_memory_ttl_cache_crud():
    """Tests basic CRUD and expiration on InMemoryTTLCache."""
    cache = InMemoryTTLCache(default_ttl=2)
    await cache.set("test:k1", {"foo": "bar"}, ttl_seconds=2)

    # Exists & Get
    assert await cache.exists("test:k1") is True
    val = await cache.get("test:k1")
    assert val == {"foo": "bar"}

    # Delete
    await cache.delete("test:k1")
    assert await cache.exists("test:k1") is False
    assert await cache.get("test:k1") is None


@pytest.mark.asyncio
async def test_in_memory_ttl_cache_expiration():
    """Tests that keys expire after their TTL."""
    cache = InMemoryTTLCache(default_ttl=1)
    await cache.set("test:exp", "hello", ttl_seconds=1)
    assert await cache.get("test:exp") == "hello"

    # Wait for TTL expiration
    await asyncio.sleep(1.1)
    assert await cache.get("test:exp") is None
    assert await cache.exists("test:exp") is False


@pytest.mark.asyncio
async def test_redis_service_fallback_mode():
    """Tests RedisService functions transparently in in-memory fallback mode."""
    svc = RedisService()
    # Write complex nested dict
    payload = {
        "station_id": "NER-SIK-GANGTOK-01",
        "rainfall_1h": 14.2,
        "soil_moisture": 68.5
    }
    key = CacheKeys.weather_live("NER-SIK-GANGTOK-01")
    await svc.set(key, payload, ttl_seconds=300)

    # Cache HIT
    hit = await svc.get(key)
    assert hit is not None
    assert hit["station_id"] == "NER-SIK-GANGTOK-01"
    assert hit["rainfall_1h"] == 14.2

    # Cache MISS
    miss = await svc.get("weather:live:NON_EXISTENT")
    assert miss is None

    # Delete
    await svc.delete(key)
    assert await svc.get(key) is None


@pytest.mark.asyncio
async def test_redis_service_health_probe():
    """Tests check_health exposes no tokens and returns valid operational info."""
    svc = RedisService()
    health = await svc.check_health()
    assert health["reachable"] is True
    assert "latency_ms" in health
    assert "backend" in health
    assert "mode" in health
    # Verify no tokens or keys are leaked
    assert "token" not in str(health).lower()
    assert "secret" not in str(health).lower()


@pytest.mark.asyncio
async def test_rate_limiter():
    """Tests atomic rate limiter counting and threshold blocking."""
    svc = RedisService()
    limiter = RateLimiter(svc)

    action = "unit_test_action"
    user_id = "test_user_42"

    # First 3 requests allowed (max 3)
    allowed1, cnt1, _ = await limiter.check_rate_limit(user_id, action, max_requests=3, window_seconds=60)
    assert allowed1 is True
    assert cnt1 == 1

    allowed2, cnt2, _ = await limiter.check_rate_limit(user_id, action, max_requests=3, window_seconds=60)
    assert allowed2 is True
    assert cnt2 == 2

    allowed3, cnt3, _ = await limiter.check_rate_limit(user_id, action, max_requests=3, window_seconds=60)
    assert allowed3 is True
    assert cnt3 == 3

    # 4th request throttled
    allowed4, cnt4, retry_after = await limiter.check_rate_limit(user_id, action, max_requests=3, window_seconds=60)
    assert allowed4 is False
    assert cnt4 == 4
    assert retry_after > 0
