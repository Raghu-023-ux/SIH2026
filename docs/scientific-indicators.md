# Scientific Indicators & Analytical Methodology

## 1. Indicator Taxonomy

The Disaster Intelligence Engine strictly separates physical indicators into **Dynamic Triggers** and **Conditioning Factors**.

```
┌─────────────────────────────────────────────────────────────┐
│                    SCIENTIFIC INDICATORS                    │
├──────────────────────────────┬──────────────────────────────┤
│       DYNAMIC TRIGGERS       │     CONDITIONING FACTORS     │
├──────────────────────────────┼──────────────────────────────┤
│ • Rainfall Intensity (1h,3h) │ • Volumetric Soil Wetness    │
│ • Multi-Day Persistence      │ • Soil Depth Saturation      │
│ • Antecedent Wetness Index   │ • Slope Angle & Aspect       │
│ • 24h Rainfall Anomaly (Z)   │ • CartoDEM Digital Elevation │
│ • Intensity-Duration Curve   │ • Historical Susceptibility  │
└──────────────────────────────┴──────────────────────────────┘
```

---

## 2. Antecedent Wetness Index ($API$)

Antecedent precipitation loading is calculated using exponential decay weighting:
\[
API(t) = P(t) + \sum_{i=1}^{n} k^i \cdot P(t-i)
\]
Where:
- $P(t)$: Precipitation measured at time interval $t$ (mm).
- $k$: Dimensionless soil moisture retention decay coefficient ($k = 0.85$ prototype baseline).
- $n$: Observation horizon (up to 7 days / 168 hours).

### Operational Classification:
- $API < 35$: NORMAL_BASELINE
- $35 \le API < 65$: MODERATE_LOADING
- $65 \le API < 110$: ELEVATED
- $API \ge 110$: CRITICAL_SATURATION

---

## 3. Short-Duration Rainfall Metrics

- **Max 1h Rainfall ($1h_{max}$)**: Rolling maximum 1-hour accumulation within the assessment window.
- **Max 3h Rainfall ($3h_{max}$)**: Rolling 3-hour storm accumulation.
- **Max 6h Rainfall ($6h_{max}$)**: Rolling 6-hour prolonged burst accumulation.
- **Continuous Wet Spell Duration**: Number of consecutive hours with precipitation $\ge 0.5\text{ mm/h}$.
- **Rainfall Anomaly ($Z$-Score)**: Standardized departure from historical seasonal baseline:
\[
Z = \frac{R_{24h} - \mu_{historical}}{\sigma_{historical}}
\]

---

## 4. Soil Moisture Profile & Response Lag

- **Multi-Depth Modeling**: Evaluated across 4 vertical layers (Surface 0–10cm, Shallow 10–40cm, Medium 40–100cm, Deep 100–200cm).
- **Rainfall-to-Soil Moisture Response Lag**: Temporal interval between peak atmospheric precipitation burst and maximum subsurface pore saturation rise ($\Delta t_{lag}$).

---

## 5. Explicit Scientific Limitations & Guardrails

> [!CAUTION]
> **Prototype System Limitations**:
> 1. The current platform is an experimental early-warning decision-support prototype.
> 2. It does **not** guarantee landslide occurrence or exact slope failure timing.
> 3. It does **not** replace statutory disaster management or meteorological authorities (NDMA/IMD/GSI).
> 4. Physical threshold curves are uncalibrated prototype references unless specifically cited.
> 5. Satellite remote sensing metadata is ingested as contextual physical evidence; raw SAR interferograms are not converted to displacement vectors in this MVP version.
