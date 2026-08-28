from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.models.risk import RiskAssessment
from backend.app.models.event import DisasterEvent
from backend.app.models.history import RiskAssessmentHistory

from backend.app.engine.base import AssessmentOutput, RiskLevel, EnvironmentalState
from backend.app.engine.data_validator import data_validator
from backend.app.engine.anomaly_detector import AnomalyDetector
from backend.app.engine.trend_analyzer import TrendAnalyzer
from backend.app.engine.terrain_source import terrain_data_source
from backend.app.engine.historical_source import historical_risk_source
from backend.app.engine.landslide_risk_analyzer import landslide_risk_analyzer
from backend.app.engine.risk_aggregator import RiskAggregator
from backend.app.engine.event_manager import event_manager
from backend.app.services.ingestion import mock_data_source

from backend.app.schemas.engine import (
    AnomalyReport,
    TrendReport,
    EngineAssessmentResponse,
    MultiLocationEngineResponse,
)
from backend.app.core.config import settings
from backend.app.core.logging import logger


class DisasterIntelligenceEngine:
    """
    Upgraded Multi-Signal Disaster Intelligence Pipeline.
    Orchestrates Data Validation, Environmental Normalization,
    Statistical Anomaly Detection, Temporal Trend/Persistence Analysis,
    Terrain Profile Integration, Historical Susceptibility,
    Factor Scoring, Multi-Signal Agreement, and Event State Machine.
    """

    def __init__(self):
        self.validator = data_validator
        self.anomaly_detector = AnomalyDetector()
        self.trend_analyzer = TrendAnalyzer()
        self.terrain_source = terrain_data_source
        self.historical_source = historical_risk_source
        self.risk_analyzer = landslide_risk_analyzer
        self.risk_aggregator = RiskAggregator()
        self.event_manager = event_manager

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
        Runs the multi-signal assessment pipeline on a monitored location.
        """
        # 1. Fetch raw observations
        observations = await self.get_or_ingest_observations(session, location.id, force_fresh=force_fresh)
        if not observations:
            raise ValueError(f"No observations available for location {location.id}")

        # 2. Stage 1 & 2: Data Validation and Normalization into EnvironmentalState
        env_states, quality_report = self.validator.validate_series(observations)
        latest_env = env_states[-1]
        historical_obs = observations[:-1] if len(observations) > 1 else observations
        latest_raw = observations[-1]

        # 3. Stage 3: Statistical Anomaly Detection
        anomalies = self.anomaly_detector.detect_anomalies(latest_raw, historical_obs)

        # 4. Stage 4: Temporal Trend & Persistence Analysis
        trends, is_persistent, is_increasing = self.trend_analyzer.analyze_trends(observations)

        # 5. Stage 5: Terrain and Historical Context Retrieval
        terrain_profile = await self.terrain_source.get_terrain_profile(location)
        historical_context = await self.historical_source.get_historical_context(location)

        # 6. Fetch recent historical risk assessments for trajectory analysis
        recent_assess_stmt = (
            select(RiskAssessment)
            .where(RiskAssessment.location_id == location.id)
            .order_by(RiskAssessment.timestamp.asc())
            .limit(10)
        )
        recent_assess_res = await session.execute(recent_assess_stmt)
        recent_assessments = list(recent_assess_res.scalars().all())

        # 7. Stage 6, 7 & 8: Landslide Risk Calculation, Signal Agreement, Confidence, Reasons, Trajectory
        assessment_output = self.risk_analyzer.assess_risk(
            location=location,
            env_state=latest_env,
            terrain=terrain_profile,
            historical=historical_context,
            anomalies=anomalies,
            trends=trends,
            is_persistent_rain=is_persistent,
            is_increasing_rain=is_increasing,
            recent_assessments=recent_assessments,
            historical_points_count=len(observations)
        )

        # 8. Persist Risk Assessment Record
        db_assessment = RiskAssessment(
            location_id=location.id,
            timestamp=assessment_output.timestamp,
            hazard_type=assessment_output.hazard_type,
            risk_level=assessment_output.risk_level.value,
            risk_score=assessment_output.risk_score,
            confidence_score=assessment_output.confidence_score,
            reason=assessment_output.reason,
            factors=[f.to_dict() for f in assessment_output.factors],
            assessment_version=settings.ENGINE_VERSION
        )
        session.add(db_assessment)

        # 9. Stage 9: Process Event Lifecycle State Machine
        event, action = await self.event_manager.process_assessment_event(
            session=session,
            location=location,
            assessment=assessment_output
        )

        # 10. Persist Detailed Assessment History for Auditing & Trend Analysis
        history_record = RiskAssessmentHistory(
            event_id=event.id if event else None,
            location_id=location.id,
            timestamp=assessment_output.timestamp,
            risk_score=assessment_output.risk_score,
            risk_level=assessment_output.risk_level.value,
            confidence=assessment_output.confidence_score,
            trajectory=assessment_output.trajectory.value,
            factors_json=[f.to_dict() for f in assessment_output.factors],
            reasons_json=[c.value for c in assessment_output.reason_codes],
            quality_json=assessment_output.data_quality.to_dict(),
            engine_version=settings.ENGINE_VERSION
        )
        session.add(history_record)

        await session.flush()
        return assessment_output, event, action

    def format_assessment_response(
        self,
        location: Location,
        assessment: AssessmentOutput,
        event: Optional[DisasterEvent]
    ) -> EngineAssessmentResponse:
        """Formats internal assessment into a comprehensive API response schema."""
        return EngineAssessmentResponse(
            location_id=location.id,
            location=location.name,
            state=location.state,
            hazard=assessment.hazard_type,
            risk_level=assessment.risk_level.value,
            risk_score=assessment.risk_score,
            confidence=assessment.confidence_score,
            trajectory=assessment.trajectory.value,
            trend=next((t.direction.value for t in assessment.trends if t.metric == "rainfall_1h"), "UNKNOWN"),
            active_event=event is not None and event.status != "RESOLVED",
            event_id=event.id if event else None,
            event_status=event.status if event else None,
            event_severity=event.severity if event else None,
            initial_risk=event.initial_risk if event else None,
            peak_risk=event.peak_risk if event else None,
            reason_codes=[c.value for c in assessment.reason_codes],
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
            data_quality=assessment.data_quality.to_dict(),
            signal_agreement={
                "agreement_score": assessment.signal_agreement.agreement_score,
                "coherent_signals_count": assessment.signal_agreement.coherent_signals_count,
                "conflicting_signals_count": assessment.signal_agreement.conflicting_signals_count,
                "agreement_level": assessment.signal_agreement.agreement_level,
                "details": assessment.signal_agreement.details,
            } if assessment.signal_agreement else None,
            summary=assessment.reason,
            timestamp=assessment.timestamp,
            engine_version=assessment.engine_version
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
                engine_version=settings.ENGINE_VERSION,
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
            f"Disaster Engine [{settings.ENGINE_VERSION}] run completed for {len(locations)} stations. "
            f"Highest risk: {agg['highest_risk_score']} ({agg['highest_risk_level']}), Active events: {active_events}"
        )

        return MultiLocationEngineResponse(
            executed_at=now,
            locations_evaluated=len(locations),
            active_events_count=active_events,
            highest_risk_score=agg["highest_risk_score"],
            highest_risk_level=agg["highest_risk_level"],
            engine_version=settings.ENGINE_VERSION,
            assessments=assessments_res
        )


disaster_engine = DisasterIntelligenceEngine()
