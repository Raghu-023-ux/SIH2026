import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

import backend.app.models  # Register all models on Base.metadata
from backend.app.core.database import Base, get_db, init_db
from backend.app.core.config import settings
from backend.app.main import app
from backend.app.services.location_service import LocationService
from backend.app.engine.scheduler import background_engine_scheduler

# Ensure background scheduler is stopped during unit test execution
background_engine_scheduler.stop()

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_main_db():
    await init_db()



@pytest_asyncio.fixture(scope="function")
async def db_session():
    # Set data mode to SIMULATION for fast, reliable, offline-safe unit test execution
    original_mode = settings.DATA_MODE
    settings.DATA_MODE = "SIMULATION"

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        await LocationService.seed_initial_locations(session)
        yield session
        await session.rollback()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    settings.DATA_MODE = original_mode


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
