# SIH26001 — AI-Based Early Warning & Landslide Risk Monitoring System (NER)

> **Disaster Intelligence Command Center & Analytical Engine (MVP v0.2)**
>
> Smart India Hackathon (SIH 2026) | Problem Statement: **SIH26001**

---

## 1. Project Purpose & Operational Scope

Landslides pose an existential threat across the **North Eastern Region (NER)** of India (Sikkim, Meghalaya, Mizoram, Nagaland, Arunachal Pradesh, Assam, Tripura, Manipur) due to intense precipitation, active tectonic zones, and steep hill slope gradients.

The **Disaster Intelligence Command Center** serves as the central operational interface for disaster monitoring officers:
1. **Continuous Telemetry Ingestion**: Ingests multi-station meteorological and soil sensor time-series.
2. **Statistical Anomaly Detection**: Detects rolling Z-score departures in rainfall bursts, soil moisture surge, and pressure drops.
3. **Temporal Trend Analysis**: Distinguishes isolated heavy rainfall from persistent, compounding precipitation.
4. **Explainable Risk Attribution**: Calculates 0–100 composite landslide hazard scores with mathematical factor breakdowns.
5. **Event State Management**: State machine tracking `WATCH` $\rightarrow$ `ELEVATED` $\rightarrow$ `HIGH_RISK` $\rightarrow$ `CRITICAL` $\rightarrow$ `RESOLVED`.
6. **Tactical GIS Command Interface**: Leaflet-based spatial risk map, sortable event queues, Recharts time-series curves, audit timelines, and live scenario simulation.

> [!NOTE]
> **Decision Support Notice**: The analytical risk models, weights, and thresholds in this prototype provide decision support telemetry for simulation and demonstration. They do not constitute official government disaster bulletins.

---

## 2. System Architecture

```text
                    ENVIRONMENTAL TELEMETRY / SIMULATOR
                                  │
                                  ▼
                    +────────────────────────────+
                    |    Data Ingestion Layer    |
                    |  (MockWeatherDataSource)   |
                    +─────────────┬──────────────+
                                  │
                                  ▼
                    +────────────────────────────+
                    |     Data Normalization     |
                    +─────────────┬──────────────+
                                  │
                                  ▼
                    +────────────────────────────+
                    | Disaster Intelligence Engine|
                    |  • Anomaly Detector (Z)    |
                    |  • Trend Analyzer (Slope)  |
                    |  • Landslide Risk Analyzer |
                    |  • Event State Machine     |
                    +─────────────┬──────────────+
                                  │
                                  ▼
                    +────────────────────────────+
                    | Disaster Event / Risk State |
                    +─────────────┬──────────────+
                                  │
                    +─────────────┴──────────────+
                    │                            │
                    ▼                            ▼
            REST APIs (FastAPI)           Future AI Agents
                    │
                    ▼
          Command Center Interface
          (Next.js + Leaflet + Recharts)
```

---

## 3. Project Structure

```text
SIH2026/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── dashboard.py     # KPI summary endpoint
│   │   │   │   │   ├── locations.py     # Stations, GIS map & investigation
│   │   │   │   │   ├── weather.py       # Sensor telemetry time-series
│   │   │   │   │   ├── risk.py          # Risk evaluations & factor breakdown
│   │   │   │   │   ├── events.py        # Disaster events & audit timelines
│   │   │   │   │   ├── engine.py        # Pipeline execution trigger
│   │   │   │   │   └── simulation.py    # Scenario injection
│   │   │   │   └── router.py
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── logging.py
│   │   ├── data/
│   │   │   └── initial_locations.json   # Seed NER monitoring stations
│   │   ├── engine/
│   │   │   ├── base.py
│   │   │   ├── anomaly_detector.py
│   │   │   ├── trend_analyzer.py
│   │   │   ├── landslide_risk_analyzer.py
│   │   │   ├── risk_aggregator.py
│   │   │   ├── event_manager.py
│   │   │   └── pipeline.py
│   │   ├── models/                      # SQLAlchemy ORM Models
│   │   ├── schemas/                     # Pydantic Schemas
│   │   ├── services/
│   │   │   ├── ingestion.py
│   │   │   ├── location_service.py
│   │   │   └── simulation_service.py
│   │   └── main.py
│   ├── tests/                           # 21 Pytest unit/integration tests
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx                 # Command Center layout
│   │   │   └── globals.css
│   │   └── components/
│   │       └── dashboard/
│   │           ├── CommandHeader.tsx    # Header & refresh controls
│   │           ├── KPICards.tsx         # Active, critical, high-risk counters
│   │           ├── RiskMap.tsx          # Dynamic SSR-safe Leaflet map
│   │           ├── RiskMapInner.tsx     # NER GIS risk markers & popups
│   │           ├── ActiveEventsList.tsx # Sortable/filterable event queue
│   │           ├── EventDetailPanel.tsx # Factor attribution & "Why active"
│   │           ├── TrendCharts.tsx      # Recharts rainfall & soil curves
│   │           ├── EventTimeline.tsx    # Chronological hazard audit log
│   │           ├── LocationInvestigateModal.tsx # 360° station modal
│   │           ├── SimulationPanel.tsx  # Scenario injection console
│   │           └── types.ts             # TypeScript interfaces
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── docs/
│   └── architecture.md
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 4. How to Run the Application

### Option A: Local Development

#### 1. Backend Setup
```bash
# In project root
python -m pip install -r backend/requirements.txt

# Run backend test suite (21 tests)
python -m pytest backend/tests/ -v

# Start backend server (FastAPI at http://localhost:8000)
uvicorn backend.app.main:app --reload --port 8000
```
Interactive API docs: `http://localhost:8000/docs`

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Command Center will be live at `http://localhost:3000`.

---

### Option B: Docker Compose
```bash
docker compose up --build
```
Services:
- **Command Center UI**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`

---

## 5. API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health, version, and disclaimer |
| `GET` | `/api/v1/dashboard/summary` | Consolidated KPI counters, peak risk, and telemetry health |
| `GET` | `/api/v1/locations/map` | GIS map stations with current risk score, levels, and weather readings |
| `GET` | `/api/v1/locations` | List monitored NER stations |
| `GET` | `/api/v1/locations/{id}/investigate` | 360° investigation package with history, charts & timeline |
| `GET` | `/api/v1/weather/{location_id}` | Recent meteorological observations time-series |
| `GET` | `/api/v1/risk/{location_id}` | Latest risk assessment with factor contribution breakdown |
| `GET` | `/api/v1/events` | List active/past disaster events (`?status=active`) |
| `GET` | `/api/v1/events/{id}/timeline` | Chronological audit milestones for hazard event |
| `POST` | `/api/v1/events/{id}/acknowledge` | Mark an event as acknowledged by monitoring officer |
| `POST` | `/api/v1/engine/run` | Execute engine evaluation on all stations or target station |
| `POST` | `/api/v1/simulation/scenario` | Inject simulated scenarios (`normal`, `critical`, `recovery`, etc.) |

---

## 6. How to Demonstrate the Command Center

1. Open `http://localhost:3000` in your browser.
2. Observe the North Eastern Region map with green pins (`LOW` risk baseline) and `● ENGINE ONLINE`.
3. In the **Simulation Console** (bottom right), select **"3. Persistent Rain 48h (High Risk)"** on *Aizawl Chite Valley* $\rightarrow$ Click **Run Scenario Simulation**.
4. Observe the live update:
   - Active Events increments to `1 [HIGH_RISK]`.
   - Map marker turns orange.
   - **Why This Event Was Detected** reveals factor contributions (`Rainfall Persistence: +15.0 pts`, `Soil Saturation: +16.2 pts`, `Rainfall Anomaly: +14.8 pts`).
   - Time-series charts display rising rainfall and soil moisture curves.
5. In the Simulation Console, select **"5. Critical Emergency (>75 Score)"** on *Gangtok Ridge* $\rightarrow$ Click **Run Scenario Simulation**.
6. Observe the critical escalation:
   - Critical Alerts increments to `1`, Peak Regional Risk reaches `79.0/100 (CRITICAL)`.
   - Gangtok map marker pulses red.
   - Click **Acknowledge Event** $\rightarrow$ Officer acknowledgement badge appears.
7. Select **"6. Recovery"** in the Simulation Console $\rightarrow$ Risk subsides below 25 and event transitions to `RESOLVED`.
