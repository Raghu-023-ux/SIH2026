from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.models.risk import RiskAssessment
from backend.app.models.event import DisasterEvent

from backend.app.engine.base import AssessmentOutput, RiskLevel
from backend.app.engine.anomaly_detector import AnomalyDetector
from backend.app.engine.trend_analyzer import TrendAnalyzer
from backend.app.engine.landslide_risk_analyzer import LandslideRiskAnalyzer
from backend.app.engine.risk_aggregator import RiskAggregator
from backend.app.engine.event_manager import EventManager
from backend.app.services.ingestion import mock_data_source

from backend.app.schemas.engine import (
    AnomalyReport,
    TrendReport,
    EngineAssessmentResponse,
    MultiLocationEngineResponse,
)
from backend.app.core.logging import logger


class DisasterIntelligenceEngine:
    """
    Main Disaster Intelligence Engine Pipeline Orchestrator.
    Integrates Data Processing, Anomaly Detection, Trend Analysis,
    Landslide Risk Modeling, and Disaster Event Lifecycle Management.
    """

    def __init__(self):
        self.anomaly_detector = AnomalyDetector()
        self.trend_analyzer = TrendAnalyzer()
        self.risk_analyzer = LandslideRiskAnalyzer()
        self.risk_aggregator = RiskAggregator()
        self.event_manager = EventManager()

    async def get_or_ingest_observations(
        self,
        session: AsyncSession,
        location_id: str,
        force_fresh: bool = False
    ) -> List[WeatherObservation]:
        """
        Retrieves existing observations from DB or generates initial baseline if empty.
        """
        stmt = (
            select(WeatherObservation)
            .where(WeatherObservation.location_id == location_id)
            .order_by(WeatherObservation.timestamp.asc())
        )
        res = await session.execute(stmt)
        observations = list(res.scalars().all())

        if not observations or force_fresh:
            logger.info(f"Ingesting fresh simulated observations for location {location_id}")
            fresh_obs = await mock_data_source.fetch(location_id=location_id, limit=24)
            for obs in fresh_obs:
                session.add(obs)
            await session.flush()
            observations = fresh_obs

        return observations

    async def evaluate_location(
        self,
        session: AsyncSession,
        location: Location,
        force_fresh: bool = False
    ) -> Tuple[AssessmentOutput, Optional[DisasterEvent], str]:
        """
        Runs the full assessment pipeline on a single monitored location.
        """
        # 1. Fetch time series observations
        observations = await self.get_or_ingest_observations(session, location.id, force_fresh=force_fresh)
        if not observations:
            raise ValueError(f"No observations available for location {location.id}")

        current_obs = observations[-1]
        historical_obs = observations[:-1] if len(observations) > 1 else observations

        # 2. Anomaly Detection
        anomalies = self.anomaly_detector.detect_anomalies(current_obs, historical_obs)

        # 3. Trend Analysis
        trends, is_persistent, is_increasing = self.trend_analyzer.analyze_trends(observations)

        # 4. Landslide Risk Calculation
        assessment_output = self.risk_analyzer.assess_risk(
            location=location,
            current_observation=current_obs,
            anomalies=anomalies,
            trends=trends,
            is_persistent_rain=is_persistent,
            is_increasing_rain=is_increasing,
            historical_count=len(observations)
        )

        # 5. Persist Risk Assessment Record
        db_assessment = RiskAssessment(
            location_id=location.id,
            timestamp=assessment_output.timestamp,
            hazard_type=assessment_output.hazard_type,
            risk_level=assessment_output.risk_level.value,
            risk_score=assessment_output.risk_score,
            confidence_score=assessment_output.confidence_score,
            reason=assessment_output.reason,
            factors=[f.to_dict() for f in assessment_output.factors],
            assessment_version="v1.0-prototype"
        )
        session.add(db_assessment)

        # 6. Manage Disaster Event State & Transitions
        event, action = await self.event_manager.process_assessment_event(
            session=session,
            location=location,
            assessment=assessment_output
        )

        await session.flush()
        return assessment_output, event, action

    def format_assessment_response(
        self,
        location: Location,
        assessment: AssessmentOutput,
        event: Optional[DisasterEvent]
    ) -> EngineAssessmentResponse:
        """Formats the internal assessment into a clean API response schema."""
        return EngineAssessmentResponse(
            location_id=location.id,
            location=location.name,
            state=location.state,
            hazard=assessment.hazard_type,
            risk_level=assessment.risk_level.value,
            risk_score=assessment.risk_score,
            confidence=assessment.confidence_score,
            trend=next((t.direction.value for t in assessment.trends if t.metric == "rainfall_1h"), "UNKNOWN"),
            active_event=event is not None and event.status != "RESOLVED",
            event_id=event.id if event else None,
            event_status=event.status if event else None,
            anomalies=[
                AnomalyReport(
                    metric=a.metric,
                    value=a.value,
                    baseline=a.baseline,
                    anomaly_score=a.anomaly_score,
                    is_anomalous=a.is_anomalous,
                    description=a.description
                )
                for a in assessment.anomalies
            ],
            trends=[
                TrendReport(
                    metric=t.metric,
                    direction=t.direction.value,
                    slope=t.slope,
                    description=t.description
                )
                for t in assessment.trends
            ],
            factors=[f.to_dict() for f in assessment.factors],
            summary=assessment.reason,
            timestamp=assessment.timestamp
        )

    async def run_pipeline(
        self,
        session: AsyncSession,
        target_location_id: Optional[str] = None,
        force_fresh: bool = False
    ) -> MultiLocationEngineResponse:
        """
        Executes engine run across all locations or a targeted location.
        """
        now = datetime.now(timezone.utc)

        if target_location_id:
            query = select(Location).where(Location.id == target_location_id)
        else:
            query = select(Location)

        result = await session.execute(query)
        locations = list(result.scalars().all())

        if not locations:
            logger.warning("No locations found in database for engine execution.")
            return MultiLocationEngineResponse(
                executed_at=now,
                locations_evaluated=0,
                active_events_count=0,
                highest_risk_score=0.0,
                highest_risk_level="LOW",
                assessments=[]
            )

        assessments_res: List[EngineAssessmentResponse] = []
        raw_assessments: List[AssessmentOutput] = []

        for loc in locations:
            assessment_out, event, _ = await self.evaluate_location(session, loc, force_fresh=force_fresh)
            raw_assessments.append(assessment_out)
            formatted = self.format_assessment_response(loc, assessment_out, event)
            assessments_res.append(formatted)

        agg = self.risk_aggregator.aggregate_assessments(raw_assessments)
        active_events = sum(1 for a in assessments_res if a.active_event)

        logger.info(
            f"Engine run completed for {len(locations)} locations. "
            f"Highest risk: {agg['highest_risk_score']} ({agg['highest_risk_level']}), Active events: {active_events}"
        )

        return MultiLocationEngineResponse(
            executed_at=now,
            locations_evaluated=len(locations),
            active_events_count=active_events,
            highest_risk_score=agg["highest_risk_score"],
            highest_risk_level=agg["highest_risk_level"],
            assessments=assessments_res
        )


disaster_engine = DisasterIntelligenceEngine()
