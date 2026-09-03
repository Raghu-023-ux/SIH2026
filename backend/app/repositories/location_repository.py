from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.location import Location
from backend.app.repositories.base import IRepository


class ILocationRepository(IRepository[Location]):
    """Repository interface for monitored weather stations & geographic sectors."""
    pass


class SqlAlchemyLocationRepository(ILocationRepository):
    """SQLAlchemy/PostgreSQL implementation of LocationRepository."""

    async def get_by_id(self, session: AsyncSession, entity_id: str) -> Optional[Location]:
        stmt = select(Location).where(Location.id == entity_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def list_all(self, session: AsyncSession) -> List[Location]:
        stmt = select(Location).order_by(Location.name.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_name(self, session: AsyncSession, name: str) -> Optional[Location]:
        stmt = select(Location).where(Location.name == name)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_state(self, session: AsyncSession, state: str) -> List[Location]:
        stmt = select(Location).where(Location.state == state).order_by(Location.name.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, session: AsyncSession, entity: Location) -> Location:
        session.add(entity)
        await session.flush()
        return entity

    async def delete(self, session: AsyncSession, entity_id: str) -> bool:
        loc = await self.get_by_id(session, entity_id)
        if loc:
            await session.delete(loc)
            await session.flush()
            return True
        return False


location_repository = SqlAlchemyLocationRepository()
