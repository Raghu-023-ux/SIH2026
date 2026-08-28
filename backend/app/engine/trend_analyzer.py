from typing import List, Tuple, Optional
from backend.app.models.weather import WeatherObservation
from backend.app.engine.base import TrendResult, TrendDirection
from backend.app.core.logging import logger


class TrendAnalyzer:
    """
    Analyzes short-term temporal trends and rates of change for environmental factors.
    Differentiates isolated heavy rainfall from heavy + persistent + increasing precipitation.
    """

    def __init__(self, stable_slope_threshold: float = 0.15):
        self.stable_slope_threshold = stable_slope_threshold

    def calculate_linear_slope(self, values: List[float]) -> float:
        """
        Calculates the ordinary least squares linear regression slope over evenly spaced points.
        Returns: change per unit step (time step).
        """
        n = len(values)
        if n < 2:
            return 0.0

        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def classify_direction(self, slope: float, threshold: Optional[float] = None) -> TrendDirection:
        thresh = threshold if threshold is not None else self.stable_slope_threshold
        if slope > thresh:
            return TrendDirection.INCREASING
        elif slope < -thresh:
            return TrendDirection.DECREASING
        else:
            return TrendDirection.STABLE

    def analyze_trends(
        self,
        observations: List[WeatherObservation]
    ) -> Tuple[List[TrendResult], bool, bool]:
        """
        Analyzes observations sorted chronologically (oldest to newest).
        Returns:
            (trend_results, is_persistent_rain, is_increasing_rain)
        """
        results: List[TrendResult] = []

        if len(observations) < 2:
            return [
                TrendResult(
                    metric="rainfall",
                    direction=TrendDirection.UNKNOWN,
                    slope=0.0,
                    description="Insufficient historical observations for trend calculation"
                )
            ], False, False

        # Sort observations by timestamp ascending
        sorted_obs = sorted(observations, key=lambda x: x.timestamp)
        recent_window = sorted_obs[-12:]  # Focus on past up to 12 hours for trend

        # 1. 1h Rainfall Trend
        r1_vals = [obs.rainfall_1h for obs in recent_window if obs.rainfall_1h is not None]
        r1_slope = self.calculate_linear_slope(r1_vals) if len(r1_vals) >= 2 else 0.0
        r1_dir = self.classify_direction(r1_slope, threshold=0.5)
        results.append(
            TrendResult(
                metric="rainfall_1h",
                direction=r1_dir,
                slope=round(r1_slope, 3),
                description=f"1h Rainfall trend is {r1_dir.value} (slope: {r1_slope:+.2f} mm/h)"
            )
        )

        # 2. 24h Cumulative Rainfall Trend
        r24_vals = [obs.rainfall_24h for obs in recent_window if obs.rainfall_24h is not None]
        r24_slope = self.calculate_linear_slope(r24_vals) if len(r24_vals) >= 2 else 0.0
        r24_dir = self.classify_direction(r24_slope, threshold=1.0)
        results.append(
            TrendResult(
                metric="rainfall_24h",
                direction=r24_dir,
                slope=round(r24_slope, 3),
                description=f"24h Rainfall accumulation trend is {r24_dir.value} (slope: {r24_slope:+.2f} mm/step)"
            )
        )

        # 3. Soil Moisture Trend
        sm_vals = [obs.soil_moisture for obs in recent_window if obs.soil_moisture is not None]
        sm_slope = self.calculate_linear_slope(sm_vals) if len(sm_vals) >= 2 else 0.0
        sm_dir = self.classify_direction(sm_slope, threshold=0.2)
        results.append(
            TrendResult(
                metric="soil_moisture",
                direction=sm_dir,
                slope=round(sm_slope, 3),
                description=f"Soil moisture trend is {sm_dir.value} (slope: {sm_slope:+.2f} %/step)"
            )
        )

        # 4. Pressure Trend
        pres_vals = [obs.pressure for obs in recent_window if obs.pressure is not None]
        pres_slope = self.calculate_linear_slope(pres_vals) if len(pres_vals) >= 2 else 0.0
        pres_dir = self.classify_direction(pres_slope, threshold=0.1)
        results.append(
            TrendResult(
                metric="pressure",
                direction=pres_dir,
                slope=round(pres_slope, 3),
                description=f"Barometric pressure trend is {pres_dir.value} (slope: {pres_slope:+.2f} hPa/step)"
            )
        )

        # Analyze Rainfall Persistence & Compounding Pattern
        # Persistent: continuous rainfall (>5mm/h) across >60% of recent observations or cumulative 24h > 100mm
        rainy_steps = sum(1 for obs in recent_window if (obs.rainfall_1h or 0.0) >= 4.0)
        latest_24h = sorted_obs[-1].rainfall_24h or 0.0
        is_persistent = (rainy_steps >= len(recent_window) * 0.5 and len(recent_window) >= 4) or latest_24h >= 120.0
        is_increasing = r1_dir == TrendDirection.INCREASING or r24_slope > 2.0

        return results, is_persistent, is_increasing
