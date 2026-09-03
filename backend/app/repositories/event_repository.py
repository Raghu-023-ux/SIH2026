from typing import List, Optional
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.event import DisasterEvent
from backend.app.repositories.base import IRepository


class IEventRepository(IRepository[DisasterEvent]):
    """Repository interface for disaster event lifecycle management."""
    pass


class SqlAlchemyEventRepository(IEventRepository):
    """SQLAlchemy/PostgreSQL implementation of EventRepository."""

    async def get_by_id(self, session: AsyncSession, entity_id: str) -> Optional[DisasterEvent]:
        stmt = select(DisasterEvent).where(DisasterEvent.id == entity_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def list_all(self, session: AsyncSession) -> List[DisasterEvent]:
        stmt = select(DisasterEvent).order_by(DisasterEvent.updated_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_for_location(
        self,
        session: AsyncSession,
        location_id: str
    ) -> Optional[DisasterEvent]:
        """Fetches the active (non-resolved) disaster event for a monitored location."""
        stmt = (
            select(DisasterEvent)
            .where(
                and_(
                    DisasterEvent.location_id == location_id,
                    DisasterEvent.status != "RESOLVED"
                )
            )
            .order_by(DisasterEvent.updated_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def list_active_events(self, session: AsyncSession) -> List[DisasterEvent]:
        """Lists all currently unresolved active disaster events across the region."""
        stmt = (
            select(DisasterEvent)
            .where(DisasterEvent.status != "RESOLVED")
            .order_by(DisasterEvent.risk_score.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, session: AsyncSession, entity: DisasterEvent) -> DisasterEvent:
        session.add(entity)
        await session.flush()
        return entity

    async def delete(self, session: AsyncSession, entity_id: str) -> bool:
        ev = await self.get_by_id(session, entity_id)
        if ev:
            await session.delete(ev)
            await session.flush()
            return True
        return False


event_repository = SqlAlchemyEventRepository()
