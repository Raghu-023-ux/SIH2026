from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.services.ingestion import mock_data_source
from backend.app.engine.pipeline import disaster_engine
from backend.app.schemas.simulation import SimulationScenarioRequest, SimulationScenarioResponse
from backend.app.core.logging import logger


class SimulationService:
    @staticmethod
    async def run_scenario(
        session: AsyncSession,
        request: SimulationScenarioRequest
    ) -> SimulationScenarioResponse:
        """
        Injects time-series weather and environmental data for the requested scenario,
        runs the Disaster Intelligence Engine pipeline, and returns the resulting risk assessment.
        """
        # Find target location
        if request.location_id:
            loc_res = await session.execute(select(Location).where(Location.id == request.location_id))
            location = loc_res.scalars().first()
            if not location:
                raise ValueError(f"Location with ID '{request.location_id}' not found.")
        else:
            # Default to primary Himalayan monitoring station (e.g. Gangtok or first station)
            loc_res = await session.execute(select(Location).order_by(Location.id))
            location = loc_res.scalars().first()
            if not location:
                raise ValueError("No monitoring locations registered in the database.")

        logger.info(
            f"Simulating scenario '{request.scenario}' for location '{location.name}' ({location.id}) "
            f"with seed {request.seed}."
        )

        # 1. Clean previous observations for clean deterministic scenario evaluation
        await session.execute(
            delete(WeatherObservation).where(WeatherObservation.location_id == location.id)
        )

        # 2. Generate and inject new scenario time-series
        now = datetime.now(timezone.utc)
        observations = mock_data_source.generate_series(
            location_id=location.id,
            scenario=request.scenario,
            num_points=24,
            end_time=now,
            seed=request.seed
        )

        for obs in observations:
            session.add(obs)
        await session.flush()

        # 3. Evaluate location through disaster intelligence engine
        assessment_out, event, action = await disaster_engine.evaluate_location(
            session=session,
            location=location,
            force_fresh=False
        )
        await session.commit()

        formatted_assessment = disaster_engine.format_assessment_response(location, assessment_out, event)

        message = (
            f"Scenario '{request.scenario}' injected successfully ({len(observations)} observations). "
            f"Engine evaluated risk at {assessment_out.risk_score:.1f}/100 ({assessment_out.risk_level.value}). "
            f"Event lifecycle action: {action.upper()}."
        )

        return SimulationScenarioResponse(
            scenario=request.scenario,
            location_id=location.id,
            location_name=location.name,
            message=message,
            observations_injected=len(observations),
            assessment=formatted_assessment,
            timestamp=now
        )
