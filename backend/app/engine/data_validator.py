from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from backend.app.models.weather import WeatherObservation
from backend.app.engine.base import (
    QualityStatus,
    DataQualityReport,
    EnvironmentalState,
)
from backend.app.core.logging import logger


class DataValidator:
    """
    Validation and Quality Assessment Layer for environmental & sensor data.
    Ensures impossible values, corrupt readings, or stale telemetry are flagged
    and safely sanitized before entering analytical risk models.
    """

    def validate_observation(
        self,
        observation: WeatherObservation,
        reference_time: Optional[datetime] = None
    ) -> Tuple[DataQualityReport, EnvironmentalState]:
        """
        Validates an individual weather observation and converts it into a sanitized EnvironmentalState.
        """
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)

        missing_fields: List[str] = []
        invalid_fields: List[str] = []
        notes: List[str] = []

        # 1. Timestamp Freshness Check
        obs_time = observation.timestamp
        if obs_time.tzinfo is None:
            obs_time = obs_time.replace(tzinfo=timezone.utc)

        time_diff = reference_time - obs_time
        age_hours = time_diff.total_seconds() / 3600.0

        if age_hours < -0.1:  # Future timestamp
            invalid_fields.append("timestamp (future timestamp detected)")
            freshness_score = 0.5
        elif age_hours <= 1.0:
            freshness_score = 1.0
        elif age_hours <= 6.0:
            freshness_score = max(0.5, 1.0 - (age_hours / 12.0))
        elif age_hours <= 24.0:
            freshness_score = max(0.2, 0.5 - ((age_hours - 6.0) / 36.0))
        else:
            freshness_score = 0.1
            notes.append(f"Stale telemetry: observation is {age_hours:.1f} hours old.")

        # 2. Rainfall Validations
        r1h = observation.rainfall_1h
        if r1h is None:
            missing_fields.append("rainfall_1h")
            sanitized_r1h = 0.0
        elif r1h < 0.0:
            invalid_fields.append("rainfall_1h (negative value)")
            sanitized_r1h = 0.0
        elif r1h > 300.0:  # Physically implausible 1-hour burst
            invalid_fields.append("rainfall_1h (extreme implausible rate >300mm/h)")
            sanitized_r1h = min(200.0, r1h)
        else:
            sanitized_r1h = float(r1h)

        r6h = observation.rainfall_6h
        if r6h is None:
            sanitized_r6h = sanitized_r1h * 3.0
        elif r6h < 0.0:
            invalid_fields.append("rainfall_6h (negative)")
            sanitized_r6h = sanitized_r1h
        else:
            sanitized_r6h = float(r6h)

        r24h = observation.rainfall_24h
        if r24h is None:
            missing_fields.append("rainfall_24h")
            sanitized_r24h = sanitized_r6h * 2.0
        elif r24h < 0.0:
            invalid_fields.append("rainfall_24h (negative)")
            sanitized_r24h = sanitized_r6h
        else:
            sanitized_r24h = float(r24h)

        # 3. Soil Moisture Validations (0.0 to 100.0% volumetric)
        sm = observation.soil_moisture
        if sm is None:
            missing_fields.append("soil_moisture")
            sanitized_sm = None
        elif sm < 0.0 or sm > 100.0:
            invalid_fields.append(f"soil_moisture (out of range: {sm}%)")
            sanitized_sm = max(0.0, min(100.0, float(sm)))
        else:
            sanitized_sm = float(sm)

        # 4. Pressure Validations (750 to 1080 hPa typical in NER elevations)
        pres = observation.pressure
        if pres is None:
            missing_fields.append("pressure")
            sanitized_pres = None
        elif pres < 600.0 or pres > 1100.0:
            invalid_fields.append(f"pressure (out of physical bounds: {pres}hPa)")
            sanitized_pres = 1013.25
        else:
            sanitized_pres = float(pres)

        # 5. Temperature Validations (-30 to 55°C)
        temp = observation.temperature
        if temp is None:
            missing_fields.append("temperature")
            sanitized_temp = None
        elif temp < -40.0 or temp > 60.0:
            invalid_fields.append(f"temperature (out of range: {temp}°C)")
            sanitized_temp = 20.0
        else:
            sanitized_temp = float(temp)

        # 6. Humidity Validations (0 to 100%)
        hum = observation.humidity
        if hum is not None and (hum < 0.0 or hum > 100.0):
            invalid_fields.append(f"humidity (out of range: {hum}%)")
            sanitized_hum = max(0.0, min(100.0, float(hum)))
        else:
            sanitized_hum = hum

        # 7. Compute Completeness & Quality Status
        total_required_metrics = 5  # r1h, r24h, soil_moisture, pressure, temperature
        present_count = total_required_metrics - len(missing_fields)
        completeness_score = max(0.0, min(1.0, present_count / total_required_metrics))

        if len(invalid_fields) > 2:
            status = QualityStatus.INVALID
            notes.append("Multiple sensor channels failed validation checks.")
        elif age_hours > 12.0:
            status = QualityStatus.STALE
            notes.append("Telemetry feed is stale (>12 hours old).")
        elif len(missing_fields) > 0 or completeness_score < 0.8:
            status = QualityStatus.PARTIAL
            notes.append(f"Partial telemetry: {len(missing_fields)} channels missing ({', '.join(missing_fields)}).")
        else:
            status = QualityStatus.VALID

        quality_report = DataQualityReport(
            status=status,
            completeness_score=completeness_score,
            freshness_score=freshness_score,
            missing_fields=missing_fields,
            invalid_fields=invalid_fields,
            quality_notes="; ".join(notes) if notes else "All telemetry signals within valid operating bounds."
        )

        state = EnvironmentalState(
            location_id=observation.location_id,
            timestamp=obs_time,
            rainfall_1h=sanitized_r1h,
            rainfall_6h=sanitized_r6h,
            rainfall_24h=sanitized_r24h,
            rainfall_72h=sanitized_r24h * 1.5,  # Estimated baseline when not provided
            soil_moisture=sanitized_sm,
            temperature=sanitized_temp,
            pressure=sanitized_pres,
            humidity=sanitized_hum,
            wind_speed=observation.wind_speed,
            wind_direction=observation.wind_direction,
            data_quality=quality_report
        )

        return quality_report, state

    def validate_series(
        self,
        observations: List[WeatherObservation]
    ) -> Tuple[List[EnvironmentalState], DataQualityReport]:
        """
        Validates and normalizes an entire time series of observations.
        Sorts chronologically, filters out duplicates, and computes 72h accumulated rainfall.
        """
        if not observations:
            empty_report = DataQualityReport(
                status=QualityStatus.INVALID,
                completeness_score=0.0,
                freshness_score=0.0,
                missing_fields=["all"],
                quality_notes="No observations provided."
            )
            return [], empty_report

        # Sort chronologically
        sorted_obs = sorted(observations, key=lambda o: o.timestamp)

        # Deduplicate identical timestamps
        unique_obs: List[WeatherObservation] = []
        seen_times = set()
        for o in sorted_obs:
            t_key = o.timestamp.isoformat()
            if t_key not in seen_times:
                seen_times.add(t_key)
                unique_obs.append(o)

        states: List[EnvironmentalState] = []
        for o in unique_obs:
            _, state = self.validate_observation(o)
            states.append(state)

        # Calculate actual 72h cumulative rainfall across series
        for i, st in enumerate(states):
            # Sum 1h rainfall of past up to 72 points
            window = states[max(0, i - 71):i + 1]
            cum_72h = sum(w.rainfall_1h for w in window if w.rainfall_1h is not None)
            st.rainfall_72h = round(max(st.rainfall_24h, cum_72h), 2)

        # The overall quality report is governed by the latest observation
        latest_report, _ = self.validate_observation(unique_obs[-1])
        return states, latest_report


data_validator = DataValidator()
