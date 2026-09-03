import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport

from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.models.risk import RiskAssessment
from backend.app.services.scientific_indicators_service import scientific_indicators_service
from backend.app.core.scientific_thresholds import scientific_config


@pytest.mark.asyncio
async def test_rainfall_indicators_calculation():
    """
    Tests rolling accumulation, intensity burst rate, max short duration,
    event segmentation, antecedent wetness index (API), wet spell persistence,
    and standardized anomaly calculation.
    """
    now = datetime.now(timezone.utc)
    loc = Location(
        id="TEST-NER-01",
        name="Test Ridge Station",
        district="East Sikkim",
        state="Sikkim",
        latitude=27.33,
        longitude=88.60,
        elevation=1600.0,
        slope_angle=35.0,
        susceptibility_score=0.85
    )

    # Construct 48-hour synthetic observations with intensifying rain
    obs_list = []
    for i in range(48):
        dt = now - timedelta(hours=47 - i)
        rate = 18.5 if i >= 40 else (8.0 if i >= 24 else 1.0)
        obs_list.append(
            WeatherObservation(
                location_id=loc.id,
                timestamp=dt,
                rainfall_1h=rate,
                rainfall_6h=rate * 4.0,
                rainfall_24h=145.0 if i == 47 else 50.0,
                soil_moisture=82.0 if i >= 40 else 60.0,
                source="test_simulator"
            )
        )

    pkg = scientific_indicators_service.calculate_rainfall_metrics(obs_list, loc)

    # 1. Verify Intensity
    assert pkg.intensity.current_intensity_mm_h == 18.5
    assert pkg.intensity.classification in ["HEAVY", "MODERATE"]

    # 2. Verify Short-Duration Table
    table_dict = {item.period: item for item in pkg.short_duration_table}
    assert "1 hour" in table_dict
    assert table_dict["1 hour"].rainfall_mm == 18.5
    assert "6 hours" in table_dict
    assert table_dict["6 hours"].rainfall_mm == round(18.5 * 6, 1)

    # 3. Verify Maximum Short Duration
    assert pkg.max_short_duration.max_1h_mm >= 18.5
    assert pkg.max_short_duration.max_3h_mm >= 18.5 * 3
    assert pkg.max_short_duration.max_6h_mm >= 18.5 * 6

    # 4. Verify Event Segmentation & Antecedent Wetness Index
    assert pkg.event_segmentation.status == "ONGOING_WET_EVENT"
    assert pkg.event_segmentation.active_wet_duration_hours >= 8
    assert pkg.antecedent_wetness_index.api_value > 0
    assert pkg.antecedent_wetness_index.is_prototype is True

    # 5. Verify Persistence & Anomaly
    assert pkg.persistence.current_wet_spell_hours >= 8
    assert pkg.persistence.persistence_level in ["HIGH", "CRITICAL"]
    assert pkg.anomaly.current_24h_mm >= 100.0
    assert pkg.anomaly.z_score > 1.0

    # 6. Verify I-D Analysis
    assert pkg.intensity_duration.cumulative_rainfall_mm > 0
    assert len(pkg.intensity_duration.reference_curve) == len(scientific_config.rainfall.id_curve_reference)


@pytest.mark.asyncio
async def test_soil_moisture_profile_and_trend():
    """
    Tests vertical multi-depth profile, infiltration velocity, and rainfall response.
    """
    now = datetime.now(timezone.utc)
    loc = Location(
        id="TEST-NER-02",
        name="Test Hill Station",
        district="Aizawl",
        state="Mizoram",
        latitude=23.72,
        longitude=92.71,
        elevation=1100.0,
        slope_angle=40.0,
        susceptibility_score=0.90
    )

    obs_list = []
    for i in range(24):
        dt = now - timedelta(hours=23 - i)
        moist = 50.0 + (i * 1.6)
        obs_list.append(
            WeatherObservation(
                location_id=loc.id,
                timestamp=dt,
                rainfall_1h=5.0,
                soil_moisture=moist,
                source="test_simulator"
            )
        )

    soil_pkg = scientific_indicators_service.calculate_soil_metrics(obs_list, loc)

    # 1. Verify vertical profile layers (4 geotechnical layers)
    assert len(soil_pkg.vertical_profile) == 4
    depth_labels = [l.depth_range for l in soil_pkg.vertical_profile]
    assert "0 - 10 cm" in depth_labels
    assert "100 - 200 cm" in depth_labels
    # Surface layer should be highest moisture
    assert soil_pkg.vertical_profile[0].moisture_pct >= soil_pkg.vertical_profile[-1].moisture_pct

    # 2. Verify trend direction & change rate
    assert soil_pkg.trend.direction in ["INCREASING", "RAPIDLY_INCREASING"]
    assert soil_pkg.trend.delta_6h_pct > 0

    # 3. Verify percentile & rainfall response
    assert soil_pkg.percentile.historical_percentile >= 80
    assert soil_pkg.rainfall_response.response_detected is True


@pytest.mark.asyncio
async def test_scientific_investigation_and_canonical_endpoints(client):
    """
    Tests the FastAPI scientific station investigation and canonical assessment endpoints.
    """
    # Seed scenario so monitored location has active data
    sim_res = await client.post("/api/v1/simulation/scenario", json={"scenario": "heavy_rain", "seed": 42})
    assert sim_res.status_code == 200

    location_id = "NER-SIK-GANGTOK-01"

    # 1. Test /scientific-analysis
    resp1 = await client.get(f"/api/v1/locations/{location_id}/scientific-analysis")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert "rainfall" in data1
    assert "soil_moisture" in data1
    assert "hydrometeorological_state" in data1
    assert "terrain" in data1
    assert "triggers" in data1
    assert "conditioning_factors" in data1
    assert "uncertainty" in data1
    assert "data_quality_matrix" in data1
    assert "timeline_series" in data1
    assert data1["engine_version"] == "1.0.0"

    # 2. Test /canonical-assessment
    resp_canon = await client.get(f"/api/v1/locations/{location_id}/canonical-assessment")
    assert resp_canon.status_code == 200
    canon = resp_canon.json()
    assert canon["engine_version"] == "1.0.0"

    assert "environment" in canon
    assert "indicators" in canon
    assert "triggers" in canon
    assert "conditioning_factors" in canon
    assert "uncertainty" in canon
    assert len(canon["triggers"]) >= 1
    assert len(canon["conditioning_factors"]) >= 1

    # 3. Test /rainfall-analysis
    resp2 = await client.get(f"/api/v1/locations/{location_id}/rainfall-analysis")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert "intensity" in data2
    assert "short_duration_table" in data2
    assert "max_short_duration" in data2

    # 4. Test /soil-analysis
    resp3 = await client.get(f"/api/v1/locations/{location_id}/soil-analysis")
    assert resp3.status_code == 200
    data3 = resp3.json()
    assert "vertical_profile" in data3
    assert "trend" in data3
