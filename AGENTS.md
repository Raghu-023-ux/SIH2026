# AGENTS.md — Developer & AI Assistant Guide
## SIH26001 Disaster Intelligence Command Center

This is the authoritative developer guide for the **SIH26001 North Eastern Region Landslide Decision Support System**.

---

### 1. PROJECT PURPOSE
- **System**: SIH26001 Disaster Intelligence Command Center.
- **Mission**: Deterministic scientific disaster risk assessment, telemetry aggregation, and emergency command decision support for the North Eastern Region of India.
- **Primary Focus**: Deterministic scientific risk formulas (physical landslide susceptibility, rainfall intensity-duration thresholds, soil saturation profiles, and historical hazard calibration).
- **Core Requirement**: This application is a deterministic decision-support engine. **It is NOT a chatbot.**

---

### 2. ARCHITECTURE

```
External Data Sources (Open-Meteo, Bhoonidhi ISRO/NRSC, Static Terrain)
        ↓
Provider Adapters (OpenMeteoProvider, BhoonidhiProvider, TerrainSource)
        ↓
Validation / Data Quality Layer (DataValidator, FreshnessEvaluator)
        ↓
Canonical Environmental Data (EnvironmentalStatePackage)
        ↓
Scientific Feature Engineering (RainfallIndicators, SoilMoistureTrend, SlopeNormalization)
        ↓
Deterministic Risk Engine (LandslideRiskAnalyzer, FactorScorer, HysteresisManager)
        ↓
Confidence & Data Completeness (ConfidenceCalculator)
        ↓
Event Lifecycle & Alerting (EventManager, MultichannelAlertService)
        ↓
Frontend (Next.js 15 Command Center Dashboard, GIS Map, Station 360)
        ↓
Optional Downstream LLM (Gemini Explanation Agent)
```

#### LLM / Gemini Boundaries
Downstream AI (Google Gemini) provides natural language summary explanations of already-computed assessments.
**Gemini MUST NOT:**
- Calculate or alter risk scores.
- Modify deterministic factor contributions.
- Invent missing sensor measurements.
- Declare a disaster or issue warnings independently.
- Override deterministic engine output.

---

### 3. LIVE VS SIMULATION

The application operational mode is set via `DATA_MODE`:
- `DATA_MODE=LIVE`: Connects to live environmental data providers (Open-Meteo, Bhoonidhi).
  - Never silently substitute fake sensor values.
  - Missing external data must be represented as unavailable/aging.
  - Confidence score must be reduced appropriately.
- `DATA_MODE=SIMULATION`: Runs deterministic synthetic multi-signal hazard scenarios for training, calibration, and offline testing.

---

### 4. PROVIDERS

| Provider | Env Variables | Required Credentials | Purpose | Failure Behavior | Criticality |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Open-Meteo** | `OPEN_METEO_API_URL` | None (Free Public API) | Live weather, rainfall & soil moisture | Retries with backoff, degrades confidence | **Critical** |
| **Bhoonidhi** | `BHOONIDHI_USER_ID`, `BHOONIDHI_PASSWORD`, `BHOONIDHI_API_URL` | Optional (`BHOONIDHI_USER_ID`, `BHOONIDHI_PASSWORD`) | ISRO / NRSC Earth Observation satellite STAC metadata | Falls back to cached metadata or mock mode | **Optional** |
| **Supabase** | `DATABASE_URL` | Required in Production | Production PostgreSQL storage | Engine logs error, `/health` reports degraded | **Critical** |
| **Upstash Redis** | `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` | Required in Production | Distributed lock, cache & rate-limiting | Falls back to in-memory TTL cache | **Critical** |
| **Gemini** | `GEMINI_API_KEY`, `GEMINI_MODEL` | Optional | Downstream AI explanations | Falls back to template-based explanations | **Optional** |
| **Resend** | `RESEND_API_KEY`, `RESEND_FROM_EMAIL` | Optional | Emergency broadcast emails | Logs failure, preserves assessment | **Optional** |

---

### 5. DATABASE RULES

- **Production Database**: Supabase PostgreSQL (`DATABASE_URL`).
- **PgBouncer Compatibility**: `DATABASE_URL` connects through Supabase Transaction Pooler (port 6543) with `statement_cache_size=0`.
- **Never**:
  - Hardcode database passwords or credentials in source code.
  - Commit `.env` files or connection strings.
  - Reset or execute destructive migrations on production.
  - Use SQLite as the production database.

---

### 6. REDIS RULES

- **Production Cache**: Upstash Redis REST API (`UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`).
- **Distributed Locking**: Background engine scheduler uses Upstash Redis lock (`engine:execution_lock`) to prevent concurrent execution across multi-worker deployments.
- **Resilience**: Redis connection failure must **NOT** crash the application; it silently degrades to local in-memory TTL caching.

---

### 7. API CREDENTIAL RULES

- All API keys, tokens, and credentials must be injected via environment variables.
- **Never**:
  - Print API keys or passwords in stdout/stderr.
  - Log Authorization headers or access tokens.
  - Expose secrets through `/health`, `/ready`, or API responses.
  - Commit `.env` files.
  - Include API credentials in frontend client bundles.

---

### 8. CHANGE SAFETY

Every modification to this codebase must follow the strict lifecycle:
```text
Inspect → Understand → Modify minimally → Test → Build → Review git diff → Commit
```
Do not perform large architectural rewrites when a targeted change is sufficient.

---

### 9. TESTING

- **Unit Tests (`pytest backend/tests -m "not integration"`)**:
  - 100% deterministic and offline-safe.
  - No external network or live API dependencies.
- **Integration Tests (`pytest backend/tests -m integration`)**:
  - Isolated under `backend/tests/integration/`.
  - Use real environment credentials when available.
  - Gracefully skip (`..._INTEGRATION=SKIPPED`) when credentials are absent.
  - Never print or leak secrets.

---

### 10. FRONTEND / BACKEND CONTRACT

- Backend REST response schemas must remain backward compatible.
- If modifying an API endpoint:
  1. Update Pydantic schemas in `backend/app/schemas/`.
  2. Update TypeScript interfaces in `frontend/src/types/`.
  3. Update frontend consumer components.
  4. Run `pytest` and `npm run build` to verify zero type mismatches.

---

### 11. DEPLOYMENT

- **Frontend Target**: Vercel (`npm run build`).
- **Backend Target**: Render Container (`docker build -f Dockerfile.backend .`).
- **Health Probes**:
  - `GET /health` (Aggregated health probe)
  - `GET /ready` (Kubernetes / Render readiness probe)
  - `GET /api/v1/engine/status` (Engine scheduler heartbeat & metrics)

---

### 12. COMMIT GUIDELINES

Follow conventional commit standards:
- `feat:` New feature or capability
- `fix:` Bug fix or connection issue
- `test:` Unit or integration test additions
- `docs:` Documentation updates
- `chore:` Configuration or build tool updates
- `ci:` CI/CD pipeline changes

Keep commits small, focused, and verified.

---

### 13. PRE-COMMIT CHECKLIST

Before pushing any commit:
1. **Backend Tests**: `python -m pytest backend/tests -v` (126+ passing)
2. **Frontend Build**: `npm run build` inside `frontend/` (12/12 passing)
3. **Environment Check**: `python -m backend.app.core.env_check`
4. **Secret Audit**: Verify `git status` contains no `.env` or secret files.
5. **Production Checks**: Ensure no hardcoded `localhost` URLs remain in production code paths.
