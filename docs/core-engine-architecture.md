# Disaster Intelligence Core Engine Architecture (v0.3)

## 1. System Overview

The SIH26001 Disaster Intelligence Core Engine is a deterministic, modular, explainable, auditable, and versioned landslide risk assessment and early warning engine. The engine ingests multi-source hydrometeorological and geophysical observations, validates data provenance and freshness, derives physical indicators, fuses multi-modal signals, assesses landslide risk and confidence, manages event lifecycles, and dispatches structured alerts.

```
┌──────────────────────────────────────────────────────────┐
│                    DATA SOURCES                          │
│                                                          │
│ Weather APIs │ Soil Moisture │ DEM/Terrain │ Historical │
│ Field Reports │ Future Remote Sensing │ Future Sensors  │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                  DATA INGESTION LAYER                    │
│                                                          │
│ Collect → Validate → Normalize → Timestamp → Provenance│
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                  ENVIRONMENTAL STATE                     │
│                                                          │
│ Current observations + derived state + quality metadata │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│             SCIENTIFIC INDICATOR ENGINE                  │
│                                                          │
│ Rainfall                    Soil Moisture                │
│ ├─ Intensity                ├─ Current                   │
│ ├─ Accumulation             ├─ Trend                     │
│ ├─ Persistence              ├─ Anomaly                   │
│ ├─ Antecedent               ├─ Percentile                │
│ ├─ Anomaly                  └─ Depth Profile             │
│ └─ Intensity-Duration                                    │
│                                                          │
│ Terrain                     Temporal                     │
│ ├─ Elevation                ├─ Trend                     │
│ ├─ Slope                    ├─ Persistence               │
│ ├─ Susceptibility           └─ Change Detection          │
│ └─ Historical Context                                     │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                SIGNAL FUSION LAYER                       │
│                                                          │
│ Cross-signal agreement                                   │
│ Data completeness                                        │
│ Data freshness                                           │
│ Signal persistence                                       │
│ Contradictory evidence                                   │
│ Field evidence                                           │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│               LANDSLIDE ASSESSMENT ENGINE                │
│                                                          │
│ Trigger indicators                                       │
│ Antecedent wetness                                       │
│ Terrain susceptibility                                   │
│ Prototype threshold comparison                           │
│ Risk scoring                                             │
│ Confidence                                               │
│ Uncertainty                                              │
│ Risk trajectory                                          │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                    EVENT ENGINE                          │
│                                                          │
│ Detect → Create → Update → Escalate → De-escalate       │
│ → Recover → Resolve                                     │
└──────────────────────────┬───────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
       Expert Command   Field Ops    Public Alert
              │            │            │
              └────────────┼────────────┘
                           ▼
                    Evidence Feedback
                           │
                           ▼
                    Future Reassessment
```

---

## 2. Core Engine Principles

1. **Deterministic & Reproducible**: Given identical environmental inputs, the engine will always produce the identical numerical risk index, confidence score, and trigger classification.
2. **Modular Pipeline**: Each analysis phase (`collect`, `validate`, `normalize`, `derive_indicators`, `detect_anomalies`, `analyze_temporal_patterns`, `analyze_susceptibility`, `fuse_signals`, `calculate_risk`, `calculate_confidence`, `calculate_uncertainty`, `update_event`, `publish_assessment`) is isolated and testable.
3. **Scientific Separation (Triggers vs. Conditioning Factors)**:
   - **Trigger Indicators**: Dynamic driving forces (Rainfall intensity, rolling accumulations, persistence, extreme short-duration rainfall).
   - **Conditioning / Susceptibility Factors**: Static or slow-moving slope vulnerability (Slope angle, soil saturation state, geological susceptibility, historical incident density).
4. **Transparent Uncertainty**: The engine never outputs a raw score without an explicit breakdown of **Assessment Confidence**, **Data Completeness**, **Data Freshness**, **Signal Agreement**, and **Known Missing Inputs**.
5. **AI Downstream Architecture**: Large Language Models (LLMs) and agentic workflows are strictly downstream consumers of structured assessments for natural language synthesis, situation reports, and operator queries. LLMs never compute or modify raw physical risk scores.

---

## 3. Data Pipeline Stages

### Stage 1: Collect
Ingests raw metrics from Open-Meteo API, IMD endpoints, synthetic sensor grids, DEM rasters, and field situation reports.

### Stage 2: Validate
Sanitizes inputs against physical domain bounds ($Rainfall \in [0, 500]\text{ mm/h}$, $Soil \in [0, 100]\%$, $Slope \in [0, 90]^\circ$). Rejects corrupted or impossible telemetry.

### Stage 3: Normalize
Converts varying provider units into canonical scientific units ($\text{mm}$, $\text{mm/h}$, $\text{m}^3/\text{m}^3$, $\text{degrees}$).

### Stage 4: Derive Indicators
Computes physical indicators:
- Rolling accumulation ($1\text{h}, 3\text{h}, 6\text{h}, 12\text{h}, 24\text{h}, 48\text{h}, 72\text{h}, 7\text{d}$)
- Maximum short-duration rainfall ($1\text{h}_{\max}, 3\text{h}_{\max}, 6\text{h}_{\max}$)
- Rainfall event segmentation (start, peak, dry periods, duration)
- Wet-spell duration ($N$ consecutive wet hours)
- Antecedent Wetness Index (API):
  $$API(t) = P(t) + \sum_{i=1}^n k^i P(t-i)$$
- Soil moisture trend, historical percentile, and anomaly.
- Intensity-Duration ($I\text{-}D$) comparison against prototype thresholds ($I = \alpha D^{-\beta}$).

### Stage 5: Detect Anomalies
Evaluates standard deviations ($Z\text{-score}$) against location historical baselines for precipitation and saturation.

### Stage 6: Analyze Temporal Patterns & Lag
Calculates rainfall-to-soil saturation response, lag time, and moisture retention persistence.

### Stage 7: Analyze Susceptibility
Fuses slope gradient, DEM elevation profile, lithology, and historical incident proximity into static susceptibility score.

### Stage 8: Fuse Signals & Assess Consistency
Measures multi-signal agreement ($M/N$ agreeing elevated signals). Calculates data freshness penalty and completeness weights.

### Stage 9: Calculate Risk & Trajectory
Calculates Prototype Risk Index ($0\text{--}100$) using weighted trigger and conditioning combinations:
$$\text{Risk} = w_{\text{trig}} \cdot S_{\text{trig}} + w_{\text{cond}} \cdot S_{\text{cond}}$$
Determines 6-hour risk trajectory (`INCREASING`, `DECREASING`, `STABLE`).

### Stage 10: Calculate Confidence & Uncertainty
Determines confidence ($0\text{--}100\%$) based on:
$$\text{Confidence} = 0.35 \cdot \text{Completeness} + 0.35 \cdot \text{Freshness} + 0.30 \cdot \text{Agreement}$$
Lists explicit missing sensory inputs (e.g., ground displacement radar, piezometric pore pressure).

### Stage 11: Manage Event Lifecycle
Applies hysteresis filtering to transition events across state transitions:
$$\text{DETECT} \rightarrow \text{CREATE} \rightarrow \text{UPDATE} \rightarrow \text{ESCALATE} \rightarrow \text{DE-ESCALATE} \rightarrow \text{RECOVERY} \rightarrow \text{RESOLVE}$$

### Stage 12: Publish Canonical Assessment Object
Publishes single standardized assessment structure (`prototype-v0.3`) consumed by Expert Command Center, Field Operations, Public Alerting, and Downstream AI Agents.

---

## 4. Canonical Assessment Object Schema

```json
{
  "location": {
    "id": "NER-SK-01",
    "name": "Gangtok Ridge Sector A",
    "district": "East Sikkim",
    "state": "Sikkim",
    "coordinates": {"latitude": 27.3389, "longitude": 88.6065},
    "elevation_m": 1650.0,
    "slope_angle_deg": 34.5
  },
  "timestamp": "2026-08-29T15:00:00Z",
  "engine_version": "prototype-v0.3",
  "environment": {
    "data_mode": "SIMULATION",
    "rainfall_rate_mmh": 22.4,
    "rainfall_24h_mm": 118.6,
    "soil_moisture_pct": 84.2,
    "temperature_c": 18.2
  },
  "indicators": {
    "rainfall": {
      "hourly_rate_mmh": 22.4,
      "accumulations_mm": {
        "1h": 22.4, "3h": 58.2, "6h": 82.0, "12h": 104.5, "24h": 118.6, "48h": 142.0, "72h": 178.0, "7d": 210.5
      },
      "max_short_duration_mm": {"1h": 26.0, "3h": 62.0, "6h": 85.0},
      "wet_spell_duration_hours": 18,
      "antecedent_wetness_index_api": 94.6,
      "anomaly_z_score": 2.85,
      "intensity_duration_status": "EXCEEDED_PROTOTYPE_REFERENCE"
    },
    "soil_moisture": {
      "current_pct": 84.2,
      "trend": "RAPIDLY_INCREASING",
      "delta_6h_pct": 9.4,
      "historical_percentile": 96.0,
      "saturation_state": "CRITICAL_SATURATION"
    },
    "terrain": {
      "slope_angle_deg": 34.5,
      "terrain_susceptibility_score": 0.82,
      "data_source": "SRTM-30m / DEMO TERRAIN DATA",
      "historical_incident_count": 14
    }
  },
  "triggers": [
    {"name": "Heavy Hourly Precipitation", "value": "22.4 mm/h", "severity": "HIGH"},
    {"name": "Rainfall Persistence", "value": "18 hours continuous", "severity": "CRITICAL"},
    {"name": "Antecedent Wetness Index", "value": "94.6 (API)", "severity": "CRITICAL"}
  ],
  "conditioning_factors": [
    {"name": "Steep Slope Angle", "value": "34.5°", "severity": "HIGH"},
    {"name": "Near-Complete Soil Saturation", "value": "84.2%", "severity": "CRITICAL"},
    {"name": "Geological Susceptibility", "value": "0.82 / 1.0", "severity": "HIGH"}
  ],
  "risk": {
    "score": 84.5,
    "level": "CRITICAL",
    "trajectory": "INCREASING",
    "delta_6h": 16.2
  },
  "confidence": {
    "score": 0.82,
    "data_completeness": 0.88,
    "data_freshness": 0.95,
    "signal_agreement": 0.83
  },
  "uncertainty": {
    "summary": "High confidence in hydrometeorological trigger; primary uncertainty stems from absence of in-situ borehole piezometer and subsurface displacement telemetry.",
    "known_missing_inputs": [
      "In-situ pore water pressure",
      "Subsurface inclinometer displacement",
      "High-resolution InSAR deformation"
    ]
  },
  "data_quality": {
    "matrix": [
      {"parameter": "Rainfall Telemetry", "status": "AVAILABLE"},
      {"parameter": "Soil Moisture", "status": "AVAILABLE"},
      {"parameter": "DEM Terrain", "status": "SIMULATED"},
      {"parameter": "Historical Baseline", "status": "AVAILABLE"},
      {"parameter": "Ground Displacement", "status": "MISSING"},
      {"parameter": "Pore Pressure", "status": "MISSING"},
      {"parameter": "Field Ground Evidence", "status": "AVAILABLE"},
      {"parameter": "Satellite Remote Sensing", "status": "MISSING"}
    ]
  },
  "provenance": {
    "primary_source": "Open-Meteo / Local Simulation Grid",
    "computed_at": "2026-08-29T15:00:00Z"
  }
}
```
