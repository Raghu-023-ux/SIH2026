# SIH26001 Disaster Assessment System — Environmental Data Sources & Provenance

## 1. Architectural Overview & Separation of Concerns

The SIH26001 Disaster Assessment System adheres to strict decoupling between **raw environmental data acquisition** and the **deterministic scientific risk assessment engine**:

```
External APIs / Sensor Telemetry / Satellites
                     ↓
         Domain Provider Adapters
     (Open-Meteo, Bhoonidhi, In-Situ)
                     ↓
        Data Quality & Validation Layer
                     ↓
    Canonical Environmental Observation Model
                     ↓
         Scientific Feature Engineering
 (I-D Curves, Antecedent Loading, Persistence)
                     ↓
        Deterministic Risk Scoring Engine
                     ↓
        Disaster Assessment & Alerts
```

No external API is permitted to directly calculate, dictate, or modify disaster risk scores.

---

## 2. Real Environmental Providers Specification

### A. Open-Meteo Weather Forecast & Hydrology API
- **Provider**: Open-Meteo (`OpenMeteoWeatherProvider`)
- **API Endpoint**: `https://api.open-meteo.com/v1/forecast`
- **Coverage**: Global, high-resolution coverage across India and the North Eastern Region (NER).
- **Spatial Resolution**: ~1km to 11km depending on underlying meteorological model (ECMWF, DWD ICON, GFS, ERA5-Land).
- **Temporal Resolution & Update Frequency**: Hourly time-series, updated every 60 minutes.
- **Authentication**: None required for non-commercial open science.
- **Caching Strategy**: Redis (`weather:live:{location_id}`), TTL: 900 seconds (15 minutes).
- **Variables Provided**:
  - `precipitation` ($mm/h$) — `OBSERVED` ($\le \text{now}$) / `FORECAST` ($> \text{now}$)
  - `rain` ($mm/h$) — `OBSERVED` / `FORECAST`
  - `temperature_2m` ($^\circ C$) — `OBSERVED` / `FORECAST`
  - `relative_humidity_2m` ($\%$) — `OBSERVED` / `FORECAST`
  - `surface_pressure` ($hPa$) — `OBSERVED` / `FORECAST`
  - `wind_speed_10m` ($km/h$) & `wind_direction_10m` ($^\circ$) — `OBSERVED` / `FORECAST`
  - `soil_moisture_0_to_1cm`, `soil_moisture_1_to_3cm`, `soil_moisture_3_to_9cm`, `soil_moisture_9_to_27cm` ($m^3/m^3$) — `MODELLED` (converted to volumetric percentage $0-100\%$)
- **Derived Variables**:
  - `rainfall_6h` ($mm$) — `DERIVED` (Rolling 6-hour accumulation)
  - `rainfall_24h` ($mm$) — `DERIVED` (Rolling 24-hour accumulation)
  - `antecedent_rainfall` ($mm$) — `DERIVED` (Preceding 24h, 48h, 72h, and 7-day pre-event wetness loading)
  - `persistence_spell` ($hours$) — `DERIVED` (Continuous precipitation duration)
- **Fallback Behavior**:
  1. Redis cache lookup.
  2. PostgreSQL historical observation lookup.
  3. Graceful degradation: If Open-Meteo is offline, records data completeness reduction, lowers assessment confidence score, and activates deterministic local simulation fallback without 500 errors.

---

### B. Open-Meteo High-Resolution Elevation API
- **Provider**: Open-Meteo Elevation (`OpenMeteoWeatherProvider.get_elevation`)
- **API Endpoint**: `https://api.open-meteo.com/v1/elevation`
- **Coverage**: Global / India (90m SRTM / 30m Copernicus DEM).
- **Authentication**: None.
- **Caching Strategy**: Redis (`terrain:elevation:{lat}:{lon}`), TTL: 86,400 seconds (24 hours).
- **Variables Provided**:
  - `elevation` ($m$ above sea level) — `MODELLED` / `DERIVED`
- **Fallback Behavior**: Returns surveyed station elevation from `locations` table.

---

### C. ISRO / NRSC Bhoonidhi Open Data Gateway
- **Provider**: ISRO / NRSC Bhoonidhi (`BhoonidhiProvider`)
- **API Endpoint**: `https://bhoonidhi.nrsc.gov.in/api`
- **Coverage**: National / Regional (India & North Eastern Region).
- **Authentication**: OAuth2 Bearer Token (`/auth/token`), cached in Redis (`bhoonidhi:auth_token:{user_id}`, TTL: 3300s).
- **Rate Limits**: 20 authentications/hour, 3 STAC search requests/second.
- **Collections Supported**:
  - `Sentinel-1A_SAR-IW_GRD` (Synthetic Aperture Radar Ground Range Detected)
  - `CartoSat-1_PAN_CartoDEM_30m` (Digital Elevation Model)
  - `NISAR_SSAR_GCOV` (NASA-ISRO SAR Geocoded Covariance)
- **Variables Provided**:
  - Satellite acquisition passes, timestamp, orbit pass (`ASCENDING`/`DESCENDING`), polarization (`VV+VH`), spatial bounding box — `SATELLITE` / `CATALOGUE`
- **Scientific Limitation**: Bhoonidhi catalogue availability represents contextual satellite observation evidence. It is **not** direct rainfall, soil moisture, or disaster confirmation.

---

## 3. Observation Provenance Taxonomy

Every data point in the pipeline is strictly tagged with one of the following five provenance types:

| Observation Type | Description | Examples |
| :--- | :--- | :--- |
| **`OBSERVED`** | Direct physical measurement or assimilated analysis for past/current time windows. | Rain gauge readings, temperature, atmospheric pressure. |
| **`FORECAST`** | Short-to-medium-range numerical weather predictions for future time steps. | 24-hour rainfall forecast, convective storm probability. |
| **`DERIVED`** | Mathematically calculated from raw observational time-series. | Rolling 24h rainfall sums, Antecedent Precipitation Index ($API$), wet spells, $Z$-score anomalies. |
| **`MODELLED`** | Geophysical models and land-surface physical process simulations. | Multi-depth soil moisture ($0-27cm$), terrain slope, DEM elevation. |
| **`SATELLITE`** | Remote sensing catalogue metadata from Earth Observation satellites. | Sentinel-1A SAR passes, NISAR granules, CartoDEM footprints. |

---

## 4. Data Freshness Governance

Data freshness thresholds are enforced automatically by `EnvironmentalDataService`:

- **`FRESH`** ($\le 30$ minutes): High quality, full confidence in trigger factor scoring.
- **`AGING`** ($30$ to $120$ minutes): Usable with slight uncertainty weighting.
- **`STALE`** ($> 120$ minutes): Triggers data aging warning; lowers assessment confidence score.
- **`UNAVAILABLE`**: Missing input; engine flags missing sensor variables in `DataCompletenessMatrix` rather than substituting fake numbers.
