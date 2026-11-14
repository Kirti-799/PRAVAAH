# PRAVAAH Phase 3C — External Data Integration Architecture

## 1. Architectural Philosophy

External meteorological, hydrological, and geospatial data sources exhibit significant variability in API stability, data formats (REST JSON, netCDF, GeoTIFF, HTML flood bulletins), rate limits, and latency.

To ensure long-term stability and scientific integrity:
1. **Frontend Isolation:** React components NEVER make direct outbound HTTP requests to external third-party APIs (Open-Meteo, IMD, NASA). All ingestion is proxied and validated by the FastAPI backend.
2. **ML Decoupling:** ML inference engines and routing pipelines NEVER call external APIs directly. Features must pass through data ingestion, validation, and schema normalization before entering any model.
3. **No Secret Leakage:** Provider API tokens (when required for future providers) remain strictly in backend environment variables.
4. **Standardized Error Classification:** Network timeouts, HTTP 429 rate limits, and upstream 5xx errors are caught and classified into domain exceptions.

---

## 2. Ingestion Pipeline & Data Flow

The external data integration architecture follows a unidirectional tiered pipeline:

```
[EXTERNAL PROVIDERS] (Open-Meteo, IMD, CWC, NASA GPM)
        |
        v
[PROVIDER ADAPTERS] (app/integrations/weather/, app/integrations/hydrology/)
        |   - HTTP request handling with httpx.AsyncClient
        |   - Configurable timeouts (default: 8.0s)
        |   - Rate-limit & HTTP status code classification
        v
[VALIDATION & NORMALIZATION] (app/integrations/weather/schemas.py)
        |   - Converts provider-specific JSON to NormalizedCurrentWeather & Forecast
        |   - Enforces units (°C, mm, km/h, %)
        |   - Preserves timestamps & timezone (Asia/Kolkata)
        |   - Tags data quality (PROVISIONAL, VERIFIED)
        v
[IN-MEMORY TTL CACHE] (app/services/weather_service.py)
        |   - 15-minute TTL per coordinate (rounded to 2 decimal places ~1.1km)
        |   - Tags cached entries with is_cached=True and cache_age_seconds
        |   - Supports explicit cache eviction via POST /api/weather/refresh
        v
[FASTAPI ROUTE HANDLERS] (app/api/routes/weather.py)
        |   - GET /api/weather/status
        |   - GET /api/weather/locations
        |   - GET /api/weather/current
        |   - GET /api/weather/forecast
        |   - POST /api/weather/refresh
        v
[REACT FRONTEND / ML PIPELINES]
```

---

## 3. Directory Layout & Module Responsibilities

```
backend/app/
├── integrations/
│   ├── __init__.py               # Top-level integration exports
│   ├── exceptions.py             # ProviderTimeoutError, ProviderRateLimitError, etc.
│   ├── weather/
│   │   ├── __init__.py
│   │   ├── base.py               # BaseWeatherAdapter (ABC contract)
│   │   ├── open_meteo.py         # OpenMeteoAdapter implementation
│   │   └── schemas.py            # Normalized data models
│   ├── maps/
│   │   ├── __init__.py
│   │   └── map_config.py         # Basemap options & study corridor coordinates
│   └── hydrology/
│       ├── __init__.py
│       ├── base.py               # BaseHydrologyAdapter (ABC contract)
│       ├── cwc.py                # CWCHydrologyAdapter (Prepared Interface)
│       ├── imd.py                # IMDWeatherAdapter (Prepared Interface)
│       └── nasa_gpm.py           # NASAGPMAdapter (Prepared Interface)
├── services/
│   └── weather_service.py        # WeatherService with TTL cache & corridor validation
├── schemas/
│   └── weather.py                # API Request / Response schemas
└── api/
    └── routes/
        └── weather.py            # FastAPI endpoints under /api/weather
```

---

## 4. Error Handling & Resilience Strategy

| Failure Scenario | Upstream Indicator | Adapter Behavior | Internal Exception | API Response |
| :--- | :--- | :--- | :--- | :--- |
| **Request Timeout** | `httpx.TimeoutException` | Aborts after 8.0s timeout | `ProviderTimeoutError` | HTTP 504 Gateway Timeout |
| **Rate Limit** | HTTP 429 | Extracts `Retry-After` header | `ProviderRateLimitError` | HTTP 429 Too Many Requests |
| **Provider Server Error** | HTTP 500, 502, 503 | Logs error details | `ProviderUnavailableError` | HTTP 502/503 Bad Gateway |
| **Malformed Response** | Missing JSON keys | Validates schema structure | `ProviderResponseValidationError` | HTTP 502 Bad Gateway |
| **Out-of-Corridor Query** | Lat/Lon outside bounds | Validates against corridor bbox | Evaluated in Service | HTTP 400 Bad Request |

---

## 5. In-Memory TTL Caching Mechanism

To prevent rate-limit exhaustion and reduce latency, `WeatherService` employs an in-memory cache:
- **Cache Key Formulation:** `(round(latitude, 2), round(longitude, 2), horizon_days)`
  - Rounding coordinates to 2 decimal places clusters queries within $\sim 1.1\text{ km}$, matching standard meteorological forecast grid resolutions.
- **Cache TTL:** 900 seconds (15 minutes).
- **Cache Transparency:**
  - Fresh queries return: `is_cached: false`, `cache_age_seconds: 0.0`.
  - Cached queries return: `is_cached: true`, `cache_age_seconds: <elapsed_seconds>`.
- **Force Refresh:**
  - `GET /api/weather/current?force_refresh=true` or `POST /api/weather/refresh` explicitly bypasses and updates the cache.
