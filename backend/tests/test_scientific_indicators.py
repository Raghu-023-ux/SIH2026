import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from backend.app.main import app
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.location import Location
from backend.app.models.weather import WeatherObservation
from backend.app.models.risk import RiskAssessment
from backend.app.services.scientific_indicators_service import scientific_indicators_service
from backend.app.core.scientific_thresholds import scientific_config


@pytest.mark.asyncio
async def test_rainfall_indicators_calculation():
    """
    Tests rolling accumulation, intensity burst rate, wet spell persistence,
    antecedent wetness, and standardized anomaly calculation.
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

    # 3. Verify Persistence
    assert pkg.persistence.current_wet_spell_hours >= 8
    assert pkg.persistence.persistence_level in ["HIGH", "CRITICAL"]

    # 4. Verify Anomaly
    assert pkg.anomaly.current_24h_mm >= 100.0
    assert pkg.anomaly.z_score > 1.0
    assert pkg.anomaly.anomaly_status in ["HIGHLY_UNUSUAL", "EXTREMELY_ABNORMAL", "MODERATELY_UNUSUAL"]

    # 5. Verify I-D Analysis
    assert pkg.intensity_duration.cumulative_rainfall_mm > 0
    assert len(pkg.intensity_duration.reference_curve) == len(scientific_config.rainfall.id_curve_reference)


@pytest.mark.asyncio
async def test_soil_moisture_profile_and_trend():
    """
    Tests vertical multi-depth profile and temporal infiltration rate calculation.
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
        # Soil moisture rising from 50% to 88%
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

    soil_pkg = scientific_indicators_service.calculate_soil_moisture_metrics(obs_list, loc)

    # 1. Verify vertical profile layers
    assert len(soil_pkg.vertical_profile) == 5
    depth_labels = [l.depth_range for l in soil_pkg.vertical_profile]
    assert "0–1 cm" in depth_labels
    assert "27–81 cm" in depth_labels
    # Surface layer should be wettest
    assert soil_pkg.vertical_profile[0].moisture_pct >= soil_pkg.vertical_profile[-1].moisture_pct

    # 2. Verify trend direction
    assert soil_pkg.trend.direction in ["INCREASING", "RAPIDLY_INCREASING"]
    assert soil_pkg.trend.delta_6h_pct > 0

    # 3. Verify percentile
    assert soil_pkg.percentile.historical_percentile >= 80


@pytest.mark.asyncio
async def test_scientific_investigation_endpoints():
    """
    Tests the FastAPI scientific station investigation endpoints.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Seed test location if needed
        async with AsyncSessionLocal() as session:
            loc = Location(
                id="NER-TEST-API-01",
                name="Scientific API Test Ridge",
                district="East Sikkim",
                state="Sikkim",
                latitude=27.35,
                longitude=88.62,
                elevation=1500.0,
                slope_angle=32.0,
                susceptibility_score=0.78
            )
            session.add(loc)
            obs = WeatherObservation(
                location_id=loc.id,
                timestamp=datetime.now(timezone.utc),
                rainfall_1h=12.0,
                rainfall_24h=85.0,
                soil_moisture=78.0,
                source="test"
            )
            session.add(obs)
            risk = RiskAssessment(
                location_id=loc.id,
                timestamp=datetime.now(timezone.utc),
                risk_level="HIGH",
                risk_score=68.5,
                confidence_score=0.88,
                reason="High antecedent rain + increasing soil saturation.",
                factors=[]
            )
            session.add(risk)
            await session.commit()

        # 1. Test /scientific-analysis
        resp1 = await client.get("/api/v1/locations/NER-TEST-API-01/scientific-analysis")
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert "rainfall" in data1
        assert "soil_moisture" in data1
        assert "hydrometeorological_state" in data1
        assert "evidence_summary" in data1
        assert "timeline_series" in data1
        assert "assessment_drivers" in data1

        # 2. Test /rainfall-analysis
        resp2 = await client.get("/api/v1/locations/NER-TEST-API-01/rainfall-analysis")
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert "intensity" in data2
        assert "short_duration_table" in data2
        assert "intensity_duration" in data2

        # 3. Test /soil-analysis
        resp3 = await client.get("/api/v1/locations/NER-TEST-API-01/soil-analysis")
        assert resp3.status_code == 200
        data3 = resp3.json()
        assert "vertical_profile" in data3
        assert "trend" in data3

        # 4. Test /risk-timeline
        resp4 = await client.get("/api/v1/locations/NER-TEST-API-01/risk-timeline")
        assert resp4.status_code == 200
        data4 = resp4.json()
        assert isinstance(data4, list)
