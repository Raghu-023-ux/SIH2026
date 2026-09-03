from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.weather import WeatherObservation
from backend.app.repositories.base import IRepository


class IWeatherRepository(IRepository[WeatherObservation]):
    """Repository interface for meteorological, precipitation, and soil moisture telemetry."""
    pass


class SqlAlchemyWeatherRepository(IWeatherRepository):
    """SQLAlchemy/PostgreSQL implementation of WeatherRepository."""

    async def get_by_id(self, session: AsyncSession, entity_id: str) -> Optional[WeatherObservation]:
        stmt = select(WeatherObservation).where(WeatherObservation.id == entity_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def list_all(self, session: AsyncSession) -> List[WeatherObservation]:
        stmt = select(WeatherObservation).order_by(WeatherObservation.timestamp.desc()).limit(100)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_for_location(
        self,
        session: AsyncSession,
        location_id: str
    ) -> Optional[WeatherObservation]:
        """Fetches the most recent observation for a location."""
        stmt = (
            select(WeatherObservation)
            .where(WeatherObservation.location_id == location_id)
            .order_by(WeatherObservation.timestamp.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_history_for_location(
        self,
        session: AsyncSession,
        location_id: str,
        limit: int = 48,
        since: Optional[datetime] = None
    ) -> List[WeatherObservation]:
        """Fetches time-series telemetry ordered chronologically for trend and anomaly calculations."""
        stmt = (
            select(WeatherObservation)
            .where(WeatherObservation.location_id == location_id)
        )
        if since:
            stmt = stmt.where(WeatherObservation.timestamp >= since)
        stmt = stmt.order_by(WeatherObservation.timestamp.asc()).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, session: AsyncSession, entity: WeatherObservation) -> WeatherObservation:
        session.add(entity)
        await session.flush()
        return entity

    async def save_batch(
        self,
        session: AsyncSession,
        entities: List[WeatherObservation]
    ) -> List[WeatherObservation]:
        session.add_all(entities)
        await session.flush()
        return entities

    async def delete(self, session: AsyncSession, entity_id: str) -> bool:
        obs = await self.get_by_id(session, entity_id)
        if obs:
            await session.delete(obs)
            await session.flush()
            return True
        return False


weather_repository = SqlAlchemyWeatherRepository()
