# PRAVAAH Phase 3C — Open-Meteo Weather Integration

## 1. Provider Selection: Open-Meteo

For Phase 3C, **Open-Meteo** ([https://open-meteo.com/en/docs](https://open-meteo.com/en/docs)) was selected as the first working external weather data provider:
- **API Endpoint:** `https://api.open-meteo.com/v1/forecast`
- **Authentication:** Free tier requires no API key (up to 10,000 daily API calls under fair use terms).
- **Spatial Coverage:** Global coverage with high-resolution numerical weather prediction models (seamlessly covers India and the Yamuna corridor).
- **Temporal Resolution:** Hourly forecast intervals up to 7 days ahead, plus current atmospheric condition snapshots.

---

## 2. Supported Meteorological Parameters

PRAVAAH queries and normalizes the following variables:

| Variable | Provider Parameter | Normalized Internal Name | Unit | Type |
| :--- | :--- | :--- | :--- | :--- |
| **Temperature** | `temperature_2m` | `temperature_c` | °C | Current / Forecast |
| **Relative Humidity** | `relative_humidity_2m` | `relative_humidity_pct` | % | Current / Forecast |
| **Precipitation Rate** | `precipitation` | `precipitation_mm` | mm | Current / Forecast |
| **Precipitation Probability** | `precipitation_probability` | `precipitation_probability_pct` | % | Forecast |
| **Wind Speed** | `wind_speed_10m` | `wind_speed_kmh` | km/h | Current / Forecast |
| **Weather Condition Code** | `weather_code` | `weather_code` | WMO Code | Current |

---

## 3. Normalized Weather Data Schema

```json
{
  "provider": "open_meteo",
  "latitude": 28.66,
  "longitude": 77.25,
  "elevation_m": 216.0,
  "timezone": "Asia/Kolkata",
  "retrieved_at": "2026-10-31T05:30:12.451Z",
  "is_cached": false,
  "cache_age_seconds": 0.0,
  "temperature_c": 26.4,
  "relative_humidity_pct": 62.0,
  "precipitation_mm": 0.0,
  "wind_speed_kmh": 9.5,
  "weather_code": 1,
  "quality_status": "PROVISIONAL",
  "source_reference": "Open-Meteo Free API (https://api.open-meteo.com/v1/forecast)",
  "scientific_disclaimer": "Current meteorological condition reported by provider. Does NOT constitute an official flood warning or river discharge estimate."
}
```

---

## 4. Backend API Endpoints

### `GET /api/weather/status`
Returns connectivity, response latency, and operational health of Open-Meteo.
```json
{
  "provider_name": "open_meteo",
  "is_available": true,
  "status_code": 200,
  "latency_ms": 320.4,
  "last_checked": "2026-10-31T05:40:00Z",
  "notes": [
    "Open-Meteo public forecast endpoint reachable.",
    "No API key required; rate-limited under fair use terms (10k daily calls)."
  ]
}
```

### `GET /api/weather/current?lat=28.66&lon=77.25&force_refresh=false`
Retrieves normalized current atmospheric conditions at the target coordinate within the corridor.
- Defaults to Delhi Old Railway Bridge ($28.66^\circ\text{ N}, 77.25^\circ\text{ E}$).
- Rejects coordinates outside the study corridor bounding box with HTTP 400.

### `GET /api/weather/forecast?lat=28.66&lon=77.25&days=3&force_refresh=false`
Retrieves hourly meteorological forecast series for up to 7 days.
- Distinguishes point rainfall forecasts from ground rainfall observations.

### `GET /api/weather/locations`
Returns the 7 primary monitoring stations along the Yamuna corridor (Hathnikund, Yamunanagar, Karnal, Panipat, Sonipat, Delhi ORB, Okhla).

### `POST /api/weather/refresh`
Body: `{"latitude": 28.66, "longitude": 77.25, "refresh_forecast": true}`
Forces in-memory cache eviction and queries Open-Meteo directly.

### `GET /api/weather/basemap/config`
Returns configured basemap providers and Yamuna corridor extent.

---

## 5. Scientific & Data Quality Guardrails

1. **Forecast vs Observation Distinction:** Forecasts are labeled `METEOROLOGICAL HOURLY FORECAST (ESTIMATED)`, while current conditions are labeled `CURRENT REPORTED`. Forecasts are never labeled as observed rainfall.
2. **Point Forecast Spatial Limitation:** A weather forecast at Delhi ORB or Hathnikund represents a point grid cell ($\sim 0.1^\circ$), NOT basin-wide catchment rainfall. Basin-wide runoff requires hydrologic routing models.
3. **Precipitation $\neq$ Flood Depth:** Low precipitation probability does NOT imply absence of flood risk (upstream release from Hathnikund Barrage may cause flooding in Delhi during clear, dry weather).
4. **No Direct Coupling to ML Discharge Model:** Open-Meteo rainfall forecasts are NOT directly piped into the `hathnikund_rf_v1` discharge model until temporal lag alignment, feature compatibility, and spatial aggregation are validated in Phase 3D.
