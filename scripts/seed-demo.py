#!/usr/bin/env python3
"""
Comprehensive Demonstration Seeder for SIH26001.
Populates realistic North Eastern Region monitoring stations, simulated weather observations,
active landslide disaster events, response teams, field reports, safer points, and historical benchmarks.
"""

import asyncio
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.core.database import init_db, AsyncSessionLocal
from backend.app.services.location_service import LocationService
from backend.app.services.simulation_service import SimulationService
from backend.app.schemas.simulation import SimulationScenarioRequest
from backend.app.engine.pipeline import disaster_engine
from backend.app.services.field_service import field_service
from backend.app.services.public_safety_service import public_safety_service
from backend.app.services.disaster_playback_service import disaster_playback_service
from backend.app.services.model_calibration_service import model_calibration_service
from backend.app.core.logging import logger


async def run_seed():
    print("=" * 70)
    print("  SIH26001: Seeding North Eastern Region Early Warning System Demo  ")
    print("=" * 70)

    # 1. Initialize Database Tables
    print("\n[1/6] Initializing Database Schema...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # 2. Seed Locations
        print("[2/6] Seeding North Eastern Region Monitoring Stations...")
        await LocationService.seed_initial_locations(session)

        # 3. Seed Field Teams & Safer Reference Points
        print("[3/6] Seeding On-Ground Rescue Teams and Safer Assembly Shelters...")
        await field_service.seed_initial_teams(session)
        await public_safety_service.seed_initial_safety_points(session)

        # 4. Seed Historical Benchmarks & Calibration Runs
        print("[4/6] Seeding Historical Disaster Benchmarks (Lhonak, Haflong, Tupul)...")
        await disaster_playback_service.seed_historical_benchmarks(session)

        # 5. Execute Simulation Scenario
        print("[5/6] Injecting 'heavy_rain' Scenario and Computing Multi-Signal Risk Assessment...")
        sim_res = await SimulationService.run_scenario(
            session, SimulationScenarioRequest(scenario="heavy_rain", seed=42)
        )
        print(f"      {sim_res.message}")

        # 6. Run Disaster Intelligence Engine
        pipeline_res = await disaster_engine.run_pipeline(session)
        print(f"      Calculated multi-signal assessments across {pipeline_res.locations_evaluated} stations.")

        await session.commit()

    print("\n" + "=" * 70)
    print("  DEMO SEEDING COMPLETED SUCCESSFULLY!")
    print("  - Monitored Stations: 6 NER Key Corridor Sites")
    print("  - Active Severe Alert: Gangtok & Haflong (Heavy Rain Scenario)")
    print("  - Rescue Teams: 4 Units Deployed (NDRF 12th Bn, SDRF Team Alpha, Border Roads)")
    print("  - Public Safer Reference Points: Paljor Stadium, Tadong Relief Center")
    print("  - Historical Replays: 2023 South Lhonak GLOF & 2022 Haflong Railway Collapse")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_seed())
