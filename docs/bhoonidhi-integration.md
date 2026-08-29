# Bhoonidhi (ISRO / NRSC) Earth Observation Integration Guide

## 1. Overview & Architectural Role

Bhoonidhi is the National Remote Sensing Centre (NRSC) / Indian Space Research Organisation (ISRO) open data dissemination gateway. In the SIH26001 Disaster Intelligence Engine, Earth Observation satellite data serves as **contextual physical evidence** alongside hydrometeorological telemetry, geotechnical parameters, historical baselines, and ground patrol reports.

```
                    DATA SOURCES
                         │
       ┌─────────────────┼──────────────────┐
       │                 │                  │
   Weather          Earth Observation   Field Reports
(Open-Meteo)         (Bhoonidhi)        (SDRF/Patrol)
       │                 │                  │
       └─────────────────┼──────────────────┘
                         ▼
                DATA INGESTION
                         ▼
                VALIDATION / QC
                         ▼
              ENVIRONMENTAL STATE
                         ▼
              SCIENTIFIC INDICATORS
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
    Rainfall          Soil/Wetness      Terrain
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                 SIGNAL FUSION
                         ▼
              LANDSLIDE ASSESSMENT
                         ▼
              CONFIDENCE / UNCERTAINTY
                         ▼
                  EVENT ENGINE
```

> [!IMPORTANT]
> **Scientific Guardrail**: In this MVP version, satellite observations provide metadata indexing and contextual scene coverage. Raw SAR interferograms / InSAR deformation are NOT converted into automatic hazard triggers without validated in-situ ground-truth calibration.

---

## 2. Supported Collections

The integration interfaces with the following open remote sensing collections catalogued on Bhoonidhi:

| Collection ID | Sensor / Instrument | Spatial Resolution | Repeat Orbit | Primary Role in EWDS |
| :--- | :--- | :--- | :--- | :--- |
| `Sentinel-1A_SAR-IW_GRD` | C-band SAR (IW Mode) | 10 m | 12 days | Cloud-penetrating backscatter moisture & surface roughness proxy |
| `Sentinel-1A_SAR-IW_SLC` | C-band SAR (Single Look Complex) | 5 m × 20 m | 12 days | Phase interferometry / future InSAR line-of-sight displacement |
| `CartoSat-1_PAN_CartoDEM_30m` | Panchromatic Stereo | 30 m DEM | Static Baseline | Geotechnical slope angle, aspect, and digital elevation modeling |
| `NISAR_SSAR_GCOV` | L-band / S-band Polarimetric SAR | 6 m | 12 days | Geocoded backscatter & soil saturation estimation |
| `NISAR_SSAR_GUNW` | L-band InSAR Interferograms | 100 m | 12 days | Geocoded unwrapped phase surface deformation mapping |

---

## 3. Provider Architecture & Authentication

The backend implements the `EarthObservationProvider` abstraction:

```
          ┌───────────────────────────────────┐
          │     EarthObservationProvider      │
          └─────────────────┬─────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
  ┌───────────────────────┐   ┌───────────────────────────┐
  │   BhoonidhiProvider   │   │ MockEarthObservationProvider│
  │   (Live OAuth2 + STAC)│   │ (Deterministic Simulation)│
  └───────────────────────┘   └───────────────────────────┘
```

### Authentication & Token Reuse
- **Endpoint**: `POST /auth/token`
- **Rate Limit Policy**: Maximum 20 authentication requests per hour per IP.
- **Token Reuse**: Access tokens are cached in-memory and reused across multiple station queries until 5 minutes before expiry.
- **Search Rate Limit**: Throttled to a maximum of 3 requests per second per IP with in-memory TTL caching (30 minutes).

### Unconfigured State Safety
If `BHOONIDHI_USER_ID` or `BHOONIDHI_PASSWORD` are not configured in the environment, the provider explicitly reports:
```json
{
  "status": "NOT_CONFIGURED",
  "configured": false,
  "note": "Bhoonidhi credentials (BHOONIDHI_USER_ID, BHOONIDHI_PASSWORD) not provided in environment."
}
```
The application **never fakes a green status**.

---

## 4. API Endpoints

- `GET /api/v1/earth-observation/status`: Returns gateway health, rate limits, token validity, and archive collections.
- `POST /api/v1/earth-observation/search`: STAC catalogue query supporting collection, bounding box, date range, and location filtering.
- `GET /api/v1/earth-observation/location/{location_id}/acquisitions`: Returns recent satellite scenes intersecting a monitored station's geographic sector.
