from typing import List, Optional
from sqlalchemy import select, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.field import (
    FieldTeam,
    FieldReport,
    FieldReportImage,
    AssistanceRequest,
    OperationalMessage,
)
from backend.app.repositories.base import IRepository


class IFieldRepository(IRepository[FieldTeam]):
    """Repository interface for field teams, ground truth reports, and SOS requests."""
    pass


class SqlAlchemyFieldRepository(IFieldRepository):
    """SQLAlchemy/PostgreSQL implementation of FieldRepository."""

    async def get_by_id(self, session: AsyncSession, entity_id: str) -> Optional[FieldTeam]:
        stmt = select(FieldTeam).where(FieldTeam.id == entity_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_callsign_or_id(self, session: AsyncSession, identifier: str) -> Optional[FieldTeam]:
        stmt = select(FieldTeam).where(or_(FieldTeam.id == identifier, FieldTeam.callsign == identifier))
        result = await session.execute(stmt)
        return result.scalars().first()

    async def list_all(self, session: AsyncSession) -> List[FieldTeam]:
        stmt = select(FieldTeam).order_by(FieldTeam.team_name.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, session: AsyncSession, entity: FieldTeam) -> FieldTeam:
        session.add(entity)
        await session.flush()
        return entity

    async def save_report(self, session: AsyncSession, report: FieldReport) -> FieldReport:
        session.add(report)
        await session.flush()
        return report

    async def save_assistance_request(self, session: AsyncSession, req: AssistanceRequest) -> AssistanceRequest:
        session.add(req)
        await session.flush()
        return req

    async def save_operational_message(self, session: AsyncSession, msg: OperationalMessage) -> OperationalMessage:
        session.add(msg)
        await session.flush()
        return msg

    async def delete(self, session: AsyncSession, entity_id: str) -> bool:
        team = await self.get_by_id(session, entity_id)
        if team:
            await session.delete(team)
            await session.flush()
            return True
        return False


field_repository = SqlAlchemyFieldRepository()
