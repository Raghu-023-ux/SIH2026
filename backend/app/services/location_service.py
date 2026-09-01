import json
import os
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.location import Location
from backend.app.core.logging import logger


class LocationService:
    @staticmethod
    async def get_all_locations(session: AsyncSession) -> List[Location]:
        result = await session.execute(select(Location).order_by(Location.state, Location.name))
        locations = list(result.scalars().all())
        if not locations:
            await LocationService.seed_initial_locations(session)
            result = await session.execute(select(Location).order_by(Location.state, Location.name))
            locations = list(result.scalars().all())
        return locations


    @staticmethod
    async def get_location_by_id(session: AsyncSession, location_id: str) -> Optional[Location]:
        result = await session.execute(select(Location).where(Location.id == location_id))
        return result.scalars().first()

    @staticmethod
    async def seed_initial_locations(session: AsyncSession):
        """Seeds initial North Eastern Region monitoring stations if database is empty."""
        result = await session.execute(select(Location))
        existing = result.scalars().first()
        if existing:
            return  # Already seeded

        # Look for initial_locations.json
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "initial_locations.json")
        if not os.path.exists(data_path):
            logger.warning(f"Initial locations data file not found at {data_path}")
            return

        with open(data_path, "r", encoding="utf-8") as f:
            locations_data = json.load(f)

        logger.info(f"Seeding {len(locations_data)} North Eastern Region locations...")
        for item in locations_data:
            loc = Location(
                id=item["id"],
                name=item["name"],
                latitude=item["latitude"],
                longitude=item["longitude"],
                district=item["district"],
                state=item["state"],
                elevation=item.get("elevation", 1000.0),
                slope_angle=item.get("slope_angle", 30.0),
                susceptibility_score=item.get("susceptibility_score", 0.7),
            )
            session.add(loc)

        await session.commit()
        logger.info("Successfully seeded North Eastern Region monitoring stations.")
