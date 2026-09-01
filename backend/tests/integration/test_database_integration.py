import pytest
import os
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.database import engine, check_database_health


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_supabase_integration():
    """
    Live integration test for Supabase PostgreSQL Database.
    Verifies connection, basic SELECT query, and schema health without modifying records.
    """
    is_postgres = "postgres" in settings.ASYNC_DATABASE_URL.lower()
    if not is_postgres:
        print("\nDATABASE_INTEGRATION=SKIPPED reason: PostgreSQL DATABASE_URL not configured")
        pytest.skip("PostgreSQL DATABASE_URL not configured for integration testing.")

    health = await check_database_health()
    if not health["reachable"]:
        print(f"\nDATABASE_INTEGRATION=FAIL reason: {health.get('error', 'unreachable')}")
        pytest.fail("Database connection failed during integration check.")

    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT 1"))
        assert res.scalar() == 1

    print("\nDATABASE_INTEGRATION=PASS")
