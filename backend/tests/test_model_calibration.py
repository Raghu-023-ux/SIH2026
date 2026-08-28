import pytest
from backend.app.services.model_calibration_service import model_calibration_service
from backend.app.schemas.analytics import BacktestRequest, BacktestWeightConfig


def test_baseline_calibration_metrics():
    metrics = model_calibration_service.get_baseline_calibration_metrics()
    assert metrics.precision > 0.80
    assert metrics.recall > 0.85
    assert metrics.f1_score > 0.85
    assert metrics.roc_auc >= 0.90
    assert metrics.lead_time_distribution.mean_lead_time_hours >= 15.0

    # Verify confusion matrix consistency
    cm = metrics.confusion_matrix
    expected_prec = cm.true_positives / (cm.true_positives + cm.false_positives)
    assert abs(metrics.precision - round(expected_prec, 4)) < 0.001


@pytest.mark.asyncio
async def test_run_backtest_weight_tuning(db_session):
    custom_cfg = BacktestWeightConfig(
        rainfall_24h=0.45,
        rainfall_72h=0.15,
        soil_moisture=0.20,
        slope_angle=0.10,
        susceptibility=0.10
    )
    req = BacktestRequest(
        run_name="High Rainfall Weight Experiment",
        weights=custom_cfg,
        warning_threshold_score=68.0
    )
    resp = await model_calibration_service.run_backtest(db_session, req)
    assert resp.run_id is not None
    assert resp.f1_score > 0.80
    assert resp.mean_lead_time_hours >= 15.0
    assert "baseline_f1" in resp.comparison_with_baseline

    # Verify history persistence
    hist = await model_calibration_service.get_evaluation_history(db_session, limit=5)
    assert len(hist) >= 1
