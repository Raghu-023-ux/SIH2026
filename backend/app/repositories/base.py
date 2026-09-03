from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class IRepository(Generic[T], ABC):
    """Abstract base repository interface defining domain data access operations."""

    @abstractmethod
    async def get_by_id(self, session: AsyncSession, entity_id: str) -> Optional[T]:
        """Fetch entity by primary key."""
        pass

    @abstractmethod
    async def list_all(self, session: AsyncSession) -> List[T]:
        """List all entities."""
        pass

    @abstractmethod
    async def save(self, session: AsyncSession, entity: T) -> T:
        """Persist or update an entity."""
        pass

    @abstractmethod
    async def delete(self, session: AsyncSession, entity_id: str) -> bool:
        """Delete an entity by primary key."""
        pass
