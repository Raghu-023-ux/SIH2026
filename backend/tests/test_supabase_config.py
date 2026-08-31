import pytest
from backend.app.core.config import Settings


def test_async_database_url_conversion():
    """Tests automatic asyncpg dialect normalization for Supabase URLs."""
    # Test standard postgres://
    s1 = Settings(DATABASE_URL="postgres://postgres:pass@aws-0.supabase.com:5432/postgres")
    assert s1.ASYNC_DATABASE_URL == "postgresql+asyncpg://postgres:pass@aws-0.supabase.com:5432/postgres"

    # Test postgresql://
    s2 = Settings(DATABASE_URL="postgresql://postgres:pass@aws-0.supabase.com:6543/postgres?ssl=require")
    assert s2.ASYNC_DATABASE_URL == "postgresql+asyncpg://postgres:pass@aws-0.supabase.com:6543/postgres?ssl=require"

    # Test already asyncpg
    s3 = Settings(DATABASE_URL="postgresql+asyncpg://postgres:pass@localhost:5432/db")
    assert s3.ASYNC_DATABASE_URL == "postgresql+asyncpg://postgres:pass@localhost:5432/db"

    # Test sqlite unchanged
    s4 = Settings(DATABASE_URL="sqlite+aiosqlite:///./test.db")
    assert s4.ASYNC_DATABASE_URL == "sqlite+aiosqlite:///./test.db"


def test_database_pool_settings_defaults():
    """Tests database pool settings have production-ready defaults for Supabase."""
    s = Settings()
    assert s.DB_POOL_SIZE >= 5
    assert s.DB_MAX_OVERFLOW >= 2
    assert s.DB_POOL_RECYCLE >= 300
    assert s.DB_POOL_TIMEOUT >= 10.0
    assert s.DB_SSL_MODE in ["disable", "prefer", "require"]
