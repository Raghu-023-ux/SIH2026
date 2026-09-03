from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.risk import RiskAssessment
from backend.app.models.history import RiskAssessmentHistory
from backend.app.repositories.base import IRepository


class IRiskRepository(IRepository[RiskAssessment]):
    """Repository interface for real-time risk assessments and historical audit logs."""
    pass


class SqlAlchemyRiskRepository(IRiskRepository):
    """SQLAlchemy/PostgreSQL implementation of RiskRepository."""

    async def get_by_id(self, session: AsyncSession, entity_id: str) -> Optional[RiskAssessment]:
        stmt = select(RiskAssessment).where(RiskAssessment.id == entity_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def list_all(self, session: AsyncSession) -> List[RiskAssessment]:
        stmt = select(RiskAssessment).order_by(RiskAssessment.timestamp.desc()).limit(100)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_for_location(
        self,
        session: AsyncSession,
        location_id: str
    ) -> Optional[RiskAssessment]:
        stmt = (
            select(RiskAssessment)
            .where(RiskAssessment.location_id == location_id)
            .order_by(RiskAssessment.timestamp.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_recent_assessments(
        self,
        session: AsyncSession,
        location_id: str,
        limit: int = 10
    ) -> List[RiskAssessment]:
        stmt = (
            select(RiskAssessment)
            .where(RiskAssessment.location_id == location_id)
            .order_by(RiskAssessment.timestamp.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, session: AsyncSession, entity: RiskAssessment) -> RiskAssessment:
        session.add(entity)
        await session.flush()
        return entity

    async def save_history(
        self,
        session: AsyncSession,
        history: RiskAssessmentHistory
    ) -> RiskAssessmentHistory:
        session.add(history)
        await session.flush()
        return history

    async def delete(self, session: AsyncSession, entity_id: str) -> bool:
        ra = await self.get_by_id(session, entity_id)
        if ra:
            await session.delete(ra)
            await session.flush()
            return True
        return False


risk_repository = SqlAlchemyRiskRepository()
