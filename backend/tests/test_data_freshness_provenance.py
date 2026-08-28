import pytest
from datetime import datetime, timezone, timedelta
from backend.app.services.environmental_data_service import environmental_data_service
from backend.app.providers.base import FreshnessStatus


def test_freshness_evaluation():
    now = datetime.now(timezone.utc)

    # 1. Observation 20 minutes ago -> FRESH
    fresh_time = now - timedelta(minutes=20)
    assert environmental_data_service.evaluate_freshness(fresh_time) == FreshnessStatus.FRESH

    # 2. Observation 120 minutes ago -> AGING (between 60 and 180 min)
    aging_time = now - timedelta(minutes=120)
    assert environmental_data_service.evaluate_freshness(aging_time) == FreshnessStatus.AGING

    # 3. Observation 300 minutes ago -> STALE (> 180 min)
    stale_time = now - timedelta(minutes=300)
    assert environmental_data_service.evaluate_freshness(stale_time) == FreshnessStatus.STALE
