# SIH26001 — AI-Based Early Warning & Landslide Risk Monitoring System (NER)

> **Multi-Signal Disaster Intelligence Engine & Command Center (MVP v0.3 — Engine Version `prototype-v0.2`)**
>
> Smart India Hackathon (SIH 2026) | Problem Statement: **SIH26001**

---

## 1. Project Purpose & Operational Scope

Landslides pose an existential threat across the **North Eastern Region (NER)** of India (Sikkim, Meghalaya, Mizoram, Nagaland, Arunachal Pradesh, Assam, Tripura, Manipur) due to intense precipitation, active tectonic zones, and steep hill slope gradients.

The **Disaster Intelligence Engine** provides an explainable, modular, multi-signal assessment pipeline combining:
1. **Data Validation & Quality Layer**: Field boundary sanitization, sensor staleness, missing field tracking, quality statuses (`VALID`, `PARTIAL`, `STALE`, `INVALID`), and 72h accumulation curves.
2. **Normalized Environmental State**: Decoupled intermediate domain representation (`EnvironmentalState`).
3. **Statistical Anomaly Detection**: Rolling Z-scores on precipitation bursts, soil moisture surge, and barometric drops.
4. **Temporal Trend & Persistence**: OLS linear slope analysis, multi-interval rainfall persistence, and pore saturation velocity.
5. **Terrain & Historical Context**: Topographic slope angle, elevation, aspect, and multi-year historical baseline susceptibility.
6. **Factor Normalization & Centralized Weights**: Standardized $0.0 - 1.0$ factor scoring with centralized configurable weights.
7. **Signal Agreement & Assessment Confidence**: Multi-signal coherence metric quantifying consistency across atmospheric triggers and subsurface pore saturation.
8. **Standardized Reason Codes & Trajectory**: Machine-readable reason codes (`HEAVY_RAINFALL`, `RAINFALL_ANOMALY`, `PERSISTENT_RAINFALL`, `SOIL_MOISTURE_ELEVATED`, `MULTI_SIGNAL_AGREEMENT`, etc.) and trajectory tracking (`STABLE`, `INCREASING`, `DECREASING`, `VOLATILE`).
9. **Debounced Event State Machine with Hysteresis**: Debounced state transitions (`MONITORING`, `WATCH`, `ELEVATED`, `HIGH`, `CRITICAL`, `RESOLVING`, `RESOLVED`) and evolution metrics (`initial_risk`, `peak_risk`, `peak_severity`).
10. **Audit History Persistence & Versioning**: `RiskAssessmentHistory` persistence and `engine_version="prototype-v0.2"`.

> [!NOTE]
> **Decision Support Notice**: The analytical risk models, weights, and thresholds in this prototype provide decision support telemetry for simulation and demonstration. They do not constitute official government disaster bulletins.

---

## 2. Multi-Signal Engine Pipeline Architecture

```text
                                RAW TELEMETRY
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │ 1. Data Validation & Quality   │
                      │    (VALID, PARTIAL, STALE)     │
                      └───────────────┬────────────────┘
                                      ▼
                      ┌────────────────────────────────┐
                      │ 2. Normalized Env State        │
                      │    (1h, 6h, 24h, 72h, Soil, P) │
                      └───────────────┬────────────────┘
                                      ▼
             ┌────────────────────────┼────────────────────────┐
             ▼                        ▼                        ▼
     ┌───────────────┐        ┌───────────────┐        ┌───────────────┐
     │ 3. Anomaly    │        │ 4. Trend &    │        │ 5. Terrain &  │
     │    Detection  │        │    Persistence│        │    History    │
     │    (Z-scores) │        │    (OLS Slope)│        │    Sources    │
     └───────┬───────┘        └───────┬───────┘        └───────┬───────┘
             └────────────────────────┼────────────────────────┘
                                      ▼
                      ┌────────────────────────────────┐
                      │ 6. Normalized Factor Scorer    │
                      │    (0.0 to 1.0 + Central Wts)  │
                      └───────────────┬────────────────┘
                                      ▼
                      ┌────────────────────────────────┐
                      │ 7. Signal Agreement & Conf.    │
                      │    (Multi-signal Coherence)    │
                      └───────────────┬────────────────┘
                                      ▼
                      ┌────────────────────────────────┐
                      │ 8. Reason Code & Trajectory    │
                      │    (STABLE, INCREASING, etc.)  │
                      └───────────────┬────────────────┘
                                      ▼
                      ┌────────────────────────────────┐
                      │ 9. Event State Machine         │
                      │    (Hysteresis & Evolution)    │
                      └───────────────┬────────────────┘
                                      ▼
                      ┌────────────────────────────────┐
                      │ 10. Audit History Persistence  │
                      │     (RiskAssessmentHistory)    │
                      └────────────────────────────────┘
```

---

## 3. How to Run and Test

### 1. Run Complete Automated Test Suite (32 Tests)
```bash
python -m pytest backend/tests/ -v
```

### 2. Start Backend API Server
```bash
uvicorn backend.app.main:app --reload --port 8000
```
Interactive Swagger API documentation: `http://localhost:8000/docs`

### 3. Start Frontend Command Center
```bash
cd frontend
npm install
npm run dev
```
Dashboard: `http://localhost:3000`

---

## 4. API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health, version, and disclaimer |
| `GET` | `/api/v1/dashboard/summary` | Consolidated KPI counters, peak risk, and telemetry health |
| `GET` | `/api/v1/locations/map` | GIS map stations with current risk score, levels, and weather readings |
| `GET` | `/api/v1/locations` | List monitored NER stations |
| `GET` | `/api/v1/locations/{id}/assessment` | Evaluate or fetch latest structured assessment |
| `GET` | `/api/v1/locations/{id}/assessment/history` | Chronological assessment history for station |
| `GET` | `/api/v1/locations/{id}/environment` | Sensor observation time-series |
| `GET` | `/api/v1/locations/{id}/investigate` | 360° investigation package with history, charts & timeline |
| `GET` | `/api/v1/events` | List active/past disaster events (`?status=active`) |
| `GET` | `/api/v1/events/{id}/timeline` | Chronological audit milestones for hazard event |
| `GET` | `/api/v1/events/{id}/assessments` | Historical assessments linked to event incident |
| `POST` | `/api/v1/events/{id}/acknowledge` | Mark an event as acknowledged by monitoring officer |
| `POST` | `/api/v1/engine/run` | Execute engine evaluation on all stations or target station |
| `POST` | `/api/v1/simulation/scenario` | Inject multi-signal simulated scenarios (`normal`, `critical`, `recovery`, etc.) |
