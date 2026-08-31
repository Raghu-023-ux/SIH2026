# Scientific Core Disaster Assessment Engine — Technical Documentation

**Engine Version**: `1.0.0`  
**Application**: Real-Time Landslide Risk Early-Warning System (Himalayan & North Eastern Region)

---

## 1. Architectural Principles & Isolation

The Core Disaster Assessment Engine is a **deterministic, explainable scientific computing pipeline**. It adheres to strict principles:

1. **Deterministic Execution**: Given the same environmental inputs, the engine produces the exact same score, factor contributions, and reasons every time.
2. **Decoupling from External Providers**: External APIs (Open-Meteo, Bhoonidhi) do not know or calculate disaster risk. They supply raw validated observations that are transformed into canonical features.
3. **No AI in Risk Calculations**: Gemini and other LLMs are auxiliary intelligence layers operating downstream on the generated evidence summary. AI never generates scores, fills missing sensor data, or declares disasters.
4. **Decoupling Risk from Confidence**: Risk measures physical hazard likelihood ($0-100$). Confidence measures data completeness, freshness, and signal coherence ($0.0-1.0$).
5. **Separation of Static Susceptibility from Dynamic Triggers**: Steep slopes alone never generate a critical alarm without dynamic meteorological or hydrological triggers.

```
                 DATA SOURCES (LIVE / SIMULATION)
               [Open-Meteo Weather, Soil, Elevation, Bhoonidhi]
                                │
                                ▼
                       DATA VALIDATION
                 (Range checks, bounds, NaN rejection)
                                │
                                ▼
                     DATA NORMALIZATION & PROVENANCE
            (OBSERVED, FORECAST, DERIVED, MODELLED, SATELLITE)
                                │
                                ▼
                    SCIENTIFIC FEATURE ENGINEERING
        (I-D Curves, API Antecedent Loading, Wet Spells, Z-Scores)
                                │
                                ▼
                   DETERMINISTIC FACTOR SCORING
                 (Dynamic Triggers + Static Susceptibility)
                                │
                                ▼
                     LANDSLIDE RISK ASSESSMENT
             (Composite Score, Trajectory, Reason Codes)
                                │
                                ▼
                   CONFIDENCE & DATA QUALITY MATRIX
            (Completeness, Freshness, Signal Coherence)
                                │
                                ▼
                    DEBOUNCED EVENT LIFECYCLE
              (NORMAL → WATCH → ADVISORY → WARNING → CRITICAL)
                                │
                                ▼
                 ALERT POLICY & NOTIFICATION DISPATCH
                 (FCM Mobile Push, Resend Email, SMS)
```

---

## 2. Feature Engineering & Mathematical Formulations

### A. Intensity-Duration (I-D) Empirical Threshold
Landslide triggering is evaluated against empirical power-law rainfall thresholds:

$$I_{\text{crit}} = \alpha \cdot D^{-\beta}$$

- **Parameters**: $\alpha = 25.0$, $\beta = 0.45$ (Calibrated for the North Eastern Region based on GSI / USGS empirical literature).
- **Calculation**: Current storm duration $D$ (hours) and average intensity $I = P_{\text{cum}} / D$ ($mm/h$) are evaluated against $I_{\text{crit}}$.
- **Output**: Threshold status (`BELOW_THRESHOLD`, `APPROACHING_THRESHOLD`, `EXCEEDING_THRESHOLD`) and percentage of critical curve.

### B. Antecedent Precipitation Index (API)
Quantifies antecedent slope wetness and pore-pressure loading:

$$\text{API}_t = \sum_{i=0}^{N} P_{t-i} \cdot k^i$$

- **Decay Factor ($k$)**: $0.85$ per day.
- **Lookback Window ($N$)**: 7 days (168 hours).
- **Classification**: Normal ($< 35$), Elevated ($35 - 75$), Critical Saturation ($> 75$).

### C. Multi-Window Cumulative Rainfall
Calculated continuously over sliding windows:
- $1\text{h}$ burst intensity ($mm/h$)
- $3\text{h}, 6\text{h}, 12\text{h}$ short-duration accumulation ($mm$)
- $24\text{h}$ event rainfall ($mm$)
- $48\text{h}, 72\text{h}$ multi-day saturation loading ($mm$)
- $7\text{-day}$ antecedent accumulation ($mm$)

### D. Multi-Depth Modelled Soil Moisture Saturation
Sourced from ERA5-Land/GFS physical assimilation models:
- Layers: $0-1\text{ cm}$ (surface boundary), $1-3\text{ cm}$ (shallow root), $3-9\text{ cm}$ (mid-soil), $9-27\text{ cm}$ (subsurface shear plane).
- Normalized to volumetric saturation percentage ($0-100\%$).
- Rate of change ($\Delta SM / \Delta t$) indicates rapid vertical wetting front propagation.
- **Threshold**: $>75\%$ indicates near-capacity pore filling.

### E. Standardized Climatological Anomaly ($Z$-Score)

$$Z = \frac{x - \mu}{\sigma}$$

- Evaluated against 10-day local rolling baseline with $\sigma = 0$ division safeguard.
- $Z \ge 2.0$ indicates an unusual event; $Z \ge 3.0$ indicates an extreme outlier.

### F. Wet Spell Persistence
- Continuous counter for consecutive hours with precipitation $> 0.2\text{ mm/h}$.
- Multi-day persistence ($> 18\text{ hours}$) prevents slope drainage and lowers effective normal stress.

---

## 3. Landslide Risk Scoring Architecture

The composite Landslide Risk Score ($0 - 100$) is computed via linear combination of normalized factor scores ($0.0 - 1.0$) with centralized weights:

$$R = 100 \times \sum_{i} (w_i \cdot S_i)$$

| Factor Name | Weight ($w_i$) | Category | Description |
| :--- | :--- | :--- | :--- |
| **Rainfall Intensity** | $0.22$ | Dynamic Trigger | 1h burst and 6h average rate |
| **Rainfall Persistence & Trend** | $0.16$ | Dynamic Trigger | 72h accumulation + continuous wet spell hours |
| **Soil Moisture Saturation** | $0.18$ | Dynamic Hydrology | Volumetric pore space filling percentage |
| **Rainfall Anomaly ($Z$-Score)** | $0.12$ | Statistical Departure | Climatological deviation from baseline |
| **Soil Saturation Rate** | $0.08$ | Dynamic Hydrology | Infiltration slope ($\Delta SM / \Delta t$) |
| **Terrain & Slope Angle** | $0.14$ | Static Susceptibility | Gravitational shear gradient & elevation |
| **Historical Baseline** | $0.10$ | Static Conditioning | Documented historical landslide density & monsoon index |

### Operational Risk Level Thresholds
- **`LOW`**: $0 - 24.9$ (Routine monitoring)
- **`MODERATE`**: $25.0 - 49.9$ (Advisory readiness)
- **`HIGH`**: $50.0 - 74.9$ (Active operational warning)
- **`CRITICAL`**: $75.0 - 100.0$ (Severe emergency alert)

---

## 4. Confidence & Data Completeness Architecture

Confidence is evaluated independently from Risk:

$$\text{Confidence} = 0.35 \cdot C_{\text{comp}} + 0.20 \cdot C_{\text{fresh}} + 0.30 \cdot C_{\text{agree}} + 0.15 \cdot C_{\text{density}}$$

- **Completeness Matrix (8 parameters)**:
  1. Rainfall (1h intensity)
  2. Rainfall (24h accumulation)
  3. Soil Moisture (Modelled)
  4. Topographic Slope & Elevation
  5. Station Historical Baseline
  6. Earth Observation Pass
  7. Atmospheric Pressure
  8. Wind Speed & Direction
- Missing inputs reduce confidence and are recorded in the data completeness matrix without fake substitutions.

---

## 5. Event Lifecycle & Alert Policy

The event lifecycle finite state machine implements hysteresis to eliminate flapping:
- Escalations (`NORMAL` $\rightarrow$ `WATCH` $\rightarrow$ `ADVISORY` $\rightarrow$ `WARNING` $\rightarrow$ `CRITICAL`) occur immediately upon sustained threshold breach.
- De-escalations require multiple consecutive lower assessments.

---

## 6. Provenance Taxonomy

| Type | Definition | Example |
| :--- | :--- | :--- |
| `OBSERVED` | Direct sensor reading / in-situ measurement. | Rain gauge rate, ambient temperature. |
| `FORECAST` | Numerical prediction for future time steps. | 24-hour rainfall forecast. |
| `DERIVED` | Mathematical transformation of observations. | 24h rolling sum, Antecedent Precipitation Index. |
| `MODELLED` | Physical process simulation. | ERA5-Land multi-depth soil moisture. |
| `SATELLITE` | Remote sensing catalogue metadata. | Sentinel-1A SAR pass, NISAR footprint. |
