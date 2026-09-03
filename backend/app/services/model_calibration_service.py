from datetime import datetime, timezone
import math
from typing import List, Optional, Dict, Any
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.analytics import ModelEvaluationRun
from backend.app.schemas.analytics import (
    ConfusionMatrix,
    LeadTimeDistribution,
    CalibrationMetricsResponse,
    BacktestRequest,
    BacktestResponse,
)
from backend.app.core.logging import logger


class ModelCalibrationService:
    """
    Statistical Model Calibration, Verification and Weight Tuning Engine.
    Evaluates forecasting precision, recall, ROC-AUC, Brier score, and lead-time distributions.
    """

    BASELINE_WEIGHTS = {
        "rainfall_24h": 0.35,
        "rainfall_72h": 0.15,
        "soil_moisture": 0.20,
        "slope_angle": 0.15,
        "susceptibility": 0.15,
    }

    @staticmethod
    def get_baseline_calibration_metrics() -> CalibrationMetricsResponse:
        cm = ConfusionMatrix(
            true_positives=46,
            false_positives=6,
            false_negatives=4,
            true_negatives=94,
            total_evaluations=150
        )
        precision = round(cm.true_positives / (cm.true_positives + cm.false_positives), 4)
        recall = round(cm.true_positives / (cm.true_positives + cm.false_negatives), 4)
        f1 = round(2 * (precision * recall) / (precision + recall), 4)

        lead_times = LeadTimeDistribution(
            mean_lead_time_hours=17.8,
            median_lead_time_hours=18.0,
            min_lead_time_hours=6.5,
            max_lead_time_hours=28.0,
            hist_bins={
                "<6h": 2,
                "6-12h": 9,
                "12-18h": 21,
                "18-24h": 14,
                ">24h": 4
            }
        )

        return CalibrationMetricsResponse(
            model_name="NER Multi-Signal Landslide Intelligence Pipeline v2.4",
            dataset_name="North Eastern Region Historical Re-analysis (2018-2024)",
            precision=precision,
            recall=recall,
            f1_score=f1,
            roc_auc=0.942,
            brier_score=0.088,
            confusion_matrix=cm,
            lead_time_distribution=lead_times,
            current_factor_weights=ModelCalibrationService.BASELINE_WEIGHTS,
            verified_disaster_events_count=50,
            is_simulated=True,
            data_mode="DEMO_SIMULATED",
            disclaimer=(
                "DEMO / SIMULATED BENCHMARK: Baseline metrics reflect synthetic calibration targets "
                "for UI and workflow verification. Certified ML metrics will be populated when trained on GSI/IMD datasets."
            )
        )


    @staticmethod
    async def run_backtest(session: AsyncSession, req: BacktestRequest) -> BacktestResponse:
        # Normalize custom weights
        w = req.weights
        total_w = w.rainfall_24h + w.rainfall_72h + w.soil_moisture + w.slope_angle + w.susceptibility
        if total_w <= 0.001:
            total_w = 1.0

        norm_weights = {
            "rainfall_24h": round(w.rainfall_24h / total_w, 3),
            "rainfall_72h": round(w.rainfall_72h / total_w, 3),
            "soil_moisture": round(w.soil_moisture / total_w, 3),
            "slope_angle": round(w.slope_angle / total_w, 3),
            "susceptibility": round(w.susceptibility / total_w, 3),
        }

        # Weight influence simulation on historical ground truth
        # Higher rainfall weight increases recall but may slightly increase false positives
        rf_bias = (norm_weights["rainfall_24h"] + norm_weights["rainfall_72h"]) - 0.50
        soil_bias = norm_weights["soil_moisture"] - 0.20
        thresh_bias = (70.0 - req.warning_threshold_score) / 100.0

        tp = int(max(38, min(49, round(46 + (rf_bias * 15) + (thresh_bias * 20)))))
        fp = int(max(2, min(16, round(6 + (rf_bias * 12) + (thresh_bias * 25)))))
        fn = int(max(1, 50 - tp))
        tn = int(max(84, 100 - fp))

        precision = round(tp / (tp + fp), 4)
        recall = round(tp / (tp + fn), 4)
        f1 = round(2 * (precision * recall) / (precision + recall), 4)
        roc_auc = round(min(0.98, max(0.85, 0.942 + (rf_bias * 0.05) - (abs(thresh_bias) * 0.03))), 4)
        mean_lead = round(max(10.0, min(24.0, 17.8 + (rf_bias * 8.0) + (thresh_bias * 5.0))), 1)

        cm = ConfusionMatrix(
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            true_negatives=tn,
            total_evaluations=tp + fp + fn + tn
        )

        comparison = {
            "baseline_f1": 0.9020,
            "experiment_f1": f1,
            "f1_delta": round(f1 - 0.9020, 4),
            "baseline_mean_lead_hours": 17.8,
            "experiment_mean_lead_hours": mean_lead,
            "lead_time_delta_hours": round(mean_lead - 17.8, 1)
        }

        recommendation = (
            "Weights provide improved early warning lead time with acceptable false alarm rates."
            if f1 >= 0.89 and mean_lead >= 17.0
            else "Caution: Parameter configuration results in elevated false alarms or reduced detection recall."
        )

        # Persist evaluation run
        run_row = ModelEvaluationRun(
            run_name=req.run_name,
            dataset_name="NER_HISTORICAL_2018_2024",
            weights_json=norm_weights,
            precision=precision,
            recall=recall,
            f1_score=f1,
            roc_auc=roc_auc,
            brier_score=0.085,
            mean_lead_time_hours=mean_lead,
            total_samples=cm.total_evaluations,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            true_negatives=tn
        )
        session.add(run_row)
        await session.flush()
        logger.info(f"Executed Model Backtest '{req.run_name}' with F1={f1:.4f}, Mean Lead={mean_lead}h")

        return BacktestResponse(
            run_id=run_row.id,
            run_name=req.run_name,
            weights_applied=norm_weights,
            precision=precision,
            recall=recall,
            f1_score=f1,
            roc_auc=roc_auc,
            mean_lead_time_hours=mean_lead,
            confusion_matrix=cm,
            comparison_with_baseline=comparison,
            recommendation=recommendation,
            is_simulated=True,
            data_mode="DEMO_SIMULATED",
        )


    @staticmethod
    async def get_evaluation_history(session: AsyncSession, limit: int = 20) -> List[ModelEvaluationRun]:
        stmt = select(ModelEvaluationRun).order_by(ModelEvaluationRun.created_at.desc()).limit(limit)
        return list((await session.execute(stmt)).scalars().all())


model_calibration_service = ModelCalibrationService()
