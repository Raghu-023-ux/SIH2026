import math
from typing import List, Optional, Sequence
from backend.app.models.weather import WeatherObservation
from backend.app.engine.base import AnomalyResult
from backend.app.core.config import settings
from backend.app.core.logging import logger


class AnomalyDetector:
    """
    Statistical Anomaly Detector for meteorological and environmental time-series.
    Calculates z-scores against rolling historical baseline statistics.
    NOTE: Prototype analytical model for landslide early-warning demonstration.
    """

    def __init__(self, z_threshold: float = settings.ANOMALY_Z_THRESHOLD):
        self.z_threshold = z_threshold

    def calculate_z_score(
        self,
        current_val: float,
        history: Sequence[float],
        min_std_eps: float = 1e-3,
        zero_std_scale: float = 10.0
    ) -> tuple[float, float, float]:
        """
        Calculates mean, standard deviation, and z-score safely.
        Returns: (mean, std_dev, z_score)
        """
        if not history:
            return current_val, 0.0, 0.0

        n = len(history)
        mean = sum(history) / n

        variance = sum((x - mean) ** 2 for x in history) / max(1, n - 1)
        std_dev = math.sqrt(variance)

        if std_dev < min_std_eps:
            # Handle near-zero baseline variance (e.g. baseline had 0 rain throughout)
            diff = current_val - mean
            if abs(diff) < 1e-4:
                z_score = 0.0
            else:
                # If baseline is near 0 and value is positive, scale departure proportionally
                z_score = diff / max(zero_std_scale, 1.0)
        else:
            z_score = (current_val - mean) / std_dev

        return mean, std_dev, z_score

    def detect_anomalies(
        self,
        current: WeatherObservation,
        history: List[WeatherObservation]
    ) -> List[AnomalyResult]:
        """
        Detects anomalies across all relevant environmental indicators:
        - rainfall_24h
        - rainfall_1h
        - soil_moisture
        - pressure
        - temperature
        """
        results: List[AnomalyResult] = []

        if not history:
            # If no history, treat current as baseline
            return results

        # 1. 24h Rainfall Anomaly
        r24_history = [obs.rainfall_24h for obs in history if obs.rainfall_24h is not None]
        if current.rainfall_24h is not None and r24_history:
            mean, std, z = self.calculate_z_score(current.rainfall_24h, r24_history, zero_std_scale=20.0)
            is_anomaly = z >= self.z_threshold and current.rainfall_24h > 25.0
            results.append(
                AnomalyResult(
                    metric="rainfall_24h",
                    value=round(current.rainfall_24h, 2),
                    baseline=round(mean, 2),
                    anomaly_score=round(z, 2),
                    is_anomalous=is_anomaly,
                    description=f"24h Rainfall {current.rainfall_24h:.1f}mm vs baseline mean {mean:.1f}mm (z={z:.2f})"
                )
            )

        # 2. 1h Rainfall Anomaly (Flash precipitation burst)
        r1_history = [obs.rainfall_1h for obs in history if obs.rainfall_1h is not None]
        if current.rainfall_1h is not None and r1_history:
            mean, std, z = self.calculate_z_score(current.rainfall_1h, r1_history, zero_std_scale=5.0)
            is_anomaly = z >= self.z_threshold and current.rainfall_1h > 10.0
            results.append(
                AnomalyResult(
                    metric="rainfall_1h",
                    value=round(current.rainfall_1h, 2),
                    baseline=round(mean, 2),
                    anomaly_score=round(z, 2),
                    is_anomalous=is_anomaly,
                    description=f"1h Rainfall burst {current.rainfall_1h:.1f}mm vs baseline {mean:.1f}mm (z={z:.2f})"
                )
            )

        # 3. Soil Moisture Anomaly (Pore saturation surge)
        sm_history = [obs.soil_moisture for obs in history if obs.soil_moisture is not None]
        if current.soil_moisture is not None and sm_history:
            mean, std, z = self.calculate_z_score(current.soil_moisture, sm_history, zero_std_scale=5.0)
            is_anomaly = z >= 1.8 and current.soil_moisture > 65.0
            results.append(
                AnomalyResult(
                    metric="soil_moisture",
                    value=round(current.soil_moisture, 2),
                    baseline=round(mean, 2),
                    anomaly_score=round(z, 2),
                    is_anomalous=is_anomaly,
                    description=f"Soil moisture {current.soil_moisture:.1f}% vs baseline {mean:.1f}% (z={z:.2f})"
                )
            )

        # 4. Atmospheric Pressure Drop Anomaly (Storm indicator)
        pres_history = [obs.pressure for obs in history if obs.pressure is not None]
        if current.pressure is not None and pres_history:
            mean, std, z = self.calculate_z_score(current.pressure, pres_history, zero_std_scale=2.0)
            # Pressure anomaly is significant when it drops sharply (negative z)
            is_anomaly = z <= -self.z_threshold or (mean - current.pressure) >= 6.0
            results.append(
                AnomalyResult(
                    metric="pressure",
                    value=round(current.pressure, 2),
                    baseline=round(mean, 2),
                    anomaly_score=round(z, 2),
                    is_anomalous=is_anomaly,
                    description=f"Atmospheric pressure {current.pressure:.1f}hPa vs baseline {mean:.1f}hPa (z={z:.2f})"
                )
            )

        # 5. Temperature Anomaly
        temp_history = [obs.temperature for obs in history if obs.temperature is not None]
        if current.temperature is not None and temp_history:
            mean, std, z = self.calculate_z_score(current.temperature, temp_history, zero_std_scale=2.0)
            is_anomaly = abs(z) >= self.z_threshold
            results.append(
                AnomalyResult(
                    metric="temperature",
                    value=round(current.temperature, 2),
                    baseline=round(mean, 2),
                    anomaly_score=round(z, 2),
                    is_anomalous=is_anomaly,
                    description=f"Temperature {current.temperature:.1f}°C vs baseline {mean:.1f}°C (z={z:.2f})"
                )
            )

        return results
