# Telemetry & Earth Observation Data Sources

## 1. Multi-Source Ingestion Pipeline

The platform aggregates heterogeneous environmental, topographical, space-borne, and ground patrol inputs:

| Stream Name | Primary Source Provider | Temporal Resolution | Spatial Extent | Processing Level |
| :--- | :--- | :--- | :--- | :--- |
| **Atmospheric Precipitation** | Open-Meteo API / Simulation Grid | Hourly (60 min) | Station coordinates ($\pm 0.01^\circ$) | Validated / Normalized |
| **Volumetric Soil Moisture** | Land-Surface Hydrological Model | 3-Hourly (180 min) | 0–200 cm profile | Derived |
| **Topography & Elevation** | CartoSat-1 / CartoDEM 30m | Static Baseline | 30 m grid | Geotechnical |
| **Earth Observation** | ISRO / NRSC Bhoonidhi Portal | 12-day repeat | NER Corridor | Scene Metadata / STAC |
| **Field Ground Truth** | SDRF / Field Patrol Units | Event-driven | GPS Waypoint ($\pm 5\text{m}$) | Validated Images + Telemetry |

---

## 2. Bhoonidhi Gateway Integration

- **Provider**: `BhoonidhiProvider` with `OAuth2` bearer token caching (respects 20 auth/hr limit).
- **Search Catalog**: STAC-compatible query interface throttled to 3 requests/sec with in-memory TTL caching (30 minutes).
- **Supported Collections**:
  - `Sentinel-1A_SAR-IW_GRD`
  - `Sentinel-1A_SAR-IW_SLC`
  - `CartoSat-1_PAN_CartoDEM_30m`
  - `NISAR_SSAR_GCOV`
  - `NISAR_SSAR_GUNW`

---

## 3. Data Quality & Completeness Governance

Every telemetry feed is evaluated for:
1. **Freshness Status**: `FRESH` ($\le 60\text{ min}$), `AGING` ($60\text{--}180\text{ min}$), `STALE` ($> 180\text{ min}$).
2. **Completeness Ratio**: Ratio of valid non-null numerical telemetry signals received.
3. **Plausibility & Bounds Check**: Out-of-range sensor readings are clamped and flagged as degraded.
