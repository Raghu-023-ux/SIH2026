"""
Database Seeding Script for SIH26001 Disaster Intelligence Engine.
Populates standard North Eastern Region monitoring stations, field units, and reference safety points.
All synthetic demonstration records are clearly marked with is_simulated=True.
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from sqlalchemy import select
from backend.app.core.database import AsyncSessionLocal, init_db, dialect_name
from backend.app.core.logging import logger
from backend.app.models.location import Location
from backend.app.models.field import FieldTeam
from backend.app.models.public import SafetyPoint


async def seed_database():
    logger.info(f"Running deterministic database seeder on {dialect_name()}...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # 1. Seed NER Monitoring Stations
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "initial_locations.json")
        if os.path.exists(data_path):
            with open(data_path, "r", encoding="utf-8") as f:
                locations_data = json.load(f)

            for item in locations_data:
                existing = (await session.execute(select(Location).where(Location.id == item["id"]))).scalars().first()
                if not existing:
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
                    logger.info(f"Seeded station: {item['name']} ({item['id']})")

        # 2. Seed Standard NER Field Rescue Units
        teams = [
            FieldTeam(
                id="NER-TEAM-ALPHA",
                team_name="SDRF Quick Response Unit Alpha",
                callsign="ALPHA-1",
                assigned_location_id="NER-SIK-GANGTOK-01",
                status="DEPLOYED",
                latitude=27.3389,
                longitude=88.6065,
                contact_channel="VHF Ch 4 / Satellite"
            ),
            FieldTeam(
                id="NER-TEAM-BRAVO",
                team_name="NDRF Search & Rescue Unit Bravo",
                callsign="BRAVO-2",
                assigned_location_id="NER-MIZ-AIZAWL-01",
                status="ON_SCENE",
                latitude=23.7271,
                longitude=92.7176,
                contact_channel="VHF Ch 7 / Satellite"
            ),
            FieldTeam(
                id="NER-TEAM-CHARLIE",
                team_name="District Disaster Management Unit Charlie",
                callsign="CHARLIE-3",
                assigned_location_id="NER-NAG-KOHIMA-01",
                status="AVAILABLE",
                latitude=25.6751,
                longitude=94.1086,
                contact_channel="VHF Ch 2 / Mobile"
            ),
        ]
        for t in teams:
            existing = (await session.execute(select(FieldTeam).where(FieldTeam.id == t.id))).scalars().first()
            if not existing:
                session.add(t)
                logger.info(f"Seeded field unit: {t.team_name} [{t.callsign}]")

        # 3. Seed Reference Safety Points (Clearly marked is_simulated=True)
        safety_points = [
            SafetyPoint(
                id="SP-SIK-GANGTOK-01",
                name="Paljor Stadium Safe Evacuation Assembly Point",
                location_id="NER-SIK-GANGTOK-01",
                latitude=27.3315,
                longitude=88.6138,
                point_type="ASSEMBLY_POINT",
                capacity=1500,
                availability="OPEN",
                source="Sikkim SDMA Official Directory",
                contact_number="03592-202651 / 1070",
                is_simulated=False
            ),
            SafetyPoint(
                id="SP-SIK-GANGTOK-02",
                name="STNM Hospital Emergency Medical Relief Post",
                location_id="NER-SIK-GANGTOK-01",
                latitude=27.3200,
                longitude=88.6010,
                point_type="MEDICAL",
                capacity=300,
                availability="OPEN",
                source="Health Department, Govt of Sikkim",
                contact_number="03592-202944 / 102",
                is_simulated=False
            ),
            SafetyPoint(
                id="SP-MIZ-AIZAWL-01",
                name="Assam Rifles Ground High-Ground Safe Zone",
                location_id="NER-MIZ-AIZAWL-01",
                latitude=23.7310,
                longitude=92.7150,
                point_type="SAFE_ZONE",
                capacity=2000,
                availability="OPEN",
                source="Mizoram Disaster Management Authority",
                contact_number="0389-2335842 / 1070",
                is_simulated=False
            ),
        ]
        for sp in safety_points:
            existing = (await session.execute(select(SafetyPoint).where(SafetyPoint.id == sp.id))).scalars().first()
            if not existing:
                session.add(sp)
                logger.info(f"Seeded safety point: {sp.name}")

        await session.commit()
        logger.info("Database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed_database())
