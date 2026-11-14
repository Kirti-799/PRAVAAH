"""
backend/tests/test_weather.py

Comprehensive test suite for Phase 3C:
- Weather Provider Adapters (OpenMeteo, BaseWeatherAdapter)
- Error Classification (Timeouts, HTTP 429 Rate Limits, HTTP 500, Malformed Payloads)
- In-Memory TTL Caching & Explicit Invalidation
- Spatial Coordinate Validation against Yamuna Corridor Extent
- Prepared Future Providers (CWC, IMD, NASA GPM)
- FastAPI /api/weather Endpoints
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.integrations.weather.open_meteo import OpenMeteoAdapter
from app.integrations.weather.schemas import (
    NormalizedCurrentWeather,
    NormalizedWeatherForecast,
    QualityStatus,
    ProviderStatus,
)
from app.integrations.exceptions import (
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    ProviderResponseValidationError,
)
from app.services.weather_service import WeatherService
from app.integrations.hydrology.cwc import CWCHydrologyAdapter
from app.integrations.hydrology.imd import IMDWeatherAdapter
from app.integrations.hydrology.nasa_gpm import NASAGPMAdapter
from app.integrations.hydrology.base import IntegrationReadiness

client = TestClient(app)

MOCK_OPEN_METEO_CURRENT_RESPONSE = {
    "latitude": 28.66,
    "longitude": 77.25,
    "generationtime_ms": 0.12,
    "utc_offset_seconds": 19800,
    "timezone": "Asia/Kolkata",
    "timezone_abbreviation": "IST",
    "elevation": 216.0,
    "current": {
        "time": "2026-10-31T05:30",
        "interval": 900,
        "temperature_2m": 24.5,
        "relative_humidity_2m": 68.0,
        "precipitation": 0.0,
        "wind_speed_10m": 8.5,
        "weather_code": 1,
    },
}

MOCK_OPEN_METEO_FORECAST_RESPONSE = {
    "latitude": 28.66,
    "longitude": 77.25,
    "generationtime_ms": 0.25,
    "utc_offset_seconds": 19800,
    "timezone": "Asia/Kolkata",
    "timezone_abbreviation": "IST",
    "elevation": 216.0,
    "hourly": {
        "time": ["2026-10-31T06:00", "2026-10-31T07:00", "2026-10-31T08:00"],
        "temperature_2m": [25.0, 26.2, 27.5],
        "relative_humidity_2m": [65.0, 60.0, 55.0],
        "precipitation": [0.0, 1.2, 3.5],
        "precipitation_probability": [5, 30, 75],
        "wind_speed_10m": [7.0, 8.5, 11.2],
    },
}


# =====================================================================
# 1. OpenMeteoAdapter Unit Tests
# =====================================================================

def test_adapter_initialization():
    adapter = OpenMeteoAdapter(base_url="https://custom.api.test", timeout_seconds=12.0)
    assert adapter.provider_name == "open_meteo"
    assert adapter.base_url == "https://custom.api.test"
    assert adapter._timeout_seconds == 12.0


@pytest.mark.anyio
async def test_adapter_get_current_weather_success():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_OPEN_METEO_CURRENT_RESPONSE
    mock_client.get.return_value = mock_resp

    adapter = OpenMeteoAdapter(client=mock_client)
    res = await adapter.get_current_weather(28.66, 77.25)

    assert isinstance(res, NormalizedCurrentWeather)
    assert res.provider == "open_meteo"
    assert res.latitude == 28.66
    assert res.longitude == 77.25
    assert res.temperature_c == 24.5
    assert res.relative_humidity_pct == 68.0
    assert res.precipitation_mm == 0.0
    assert res.wind_speed_kmh == 8.5
    assert res.quality_status == QualityStatus.PROVISIONAL
    assert res.is_cached is False
    assert "flood warning" in res.scientific_disclaimer.lower()


@pytest.mark.anyio
async def test_adapter_get_forecast_success():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_OPEN_METEO_FORECAST_RESPONSE
    mock_client.get.return_value = mock_resp

    adapter = OpenMeteoAdapter(client=mock_client)
    res = await adapter.get_forecast(28.66, 77.25, forecast_days=3)

    assert isinstance(res, NormalizedWeatherForecast)
    assert res.provider == "open_meteo"
    assert len(res.hourly_series) == 3
    assert res.hourly_series[1].precipitation_mm == 1.2
    assert res.hourly_series[1].precipitation_probability_pct == 30
    assert res.hourly_series[2].temperature_c == 27.5
    assert "basin-wide rainfall" in res.scientific_disclaimer.lower()


@pytest.mark.anyio
async def test_adapter_timeout_handling():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.side_effect = httpx.TimeoutException("Timed out")

    adapter = OpenMeteoAdapter(client=mock_client, timeout_seconds=5.0)
    with pytest.raises(ProviderTimeoutError) as exc_info:
        await adapter.get_current_weather(28.66, 77.25)

    assert exc_info.value.status_code == 504
    assert "5.0s" in str(exc_info.value)


@pytest.mark.anyio
async def test_adapter_rate_limit_429():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 429
    mock_resp.headers = {"Retry-After": "60"}
    mock_client.get.return_value = mock_resp

    adapter = OpenMeteoAdapter(client=mock_client)
    with pytest.raises(ProviderRateLimitError) as exc_info:
        await adapter.get_current_weather(28.66, 77.25)

    assert exc_info.value.status_code == 429
    assert "retry after 60s" in str(exc_info.value)


@pytest.mark.anyio
async def test_adapter_server_error_500():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 503
    mock_client.get.return_value = mock_resp

    adapter = OpenMeteoAdapter(client=mock_client)
    with pytest.raises(ProviderUnavailableError) as exc_info:
        await adapter.get_current_weather(28.66, 77.25)

    assert exc_info.value.status_code == 503


@pytest.mark.anyio
async def test_adapter_malformed_response():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"something_unexpected": 123}  # missing 'current'
    mock_client.get.return_value = mock_resp

    adapter = OpenMeteoAdapter(client=mock_client)
    with pytest.raises(ProviderResponseValidationError) as exc_info:
        await adapter.get_current_weather(28.66, 77.25)

    assert exc_info.value.status_code == 502


# =====================================================================
# 2. WeatherService Caching & Validation Tests
# =====================================================================

@pytest.mark.anyio
async def test_weather_service_caching_and_freshness():
    mock_adapter = AsyncMock(spec=OpenMeteoAdapter)
    mock_adapter.provider_name = "mock_open_meteo"
    mock_adapter.get_current_weather.return_value = NormalizedCurrentWeather(
        provider="mock_open_meteo",
        latitude=28.66,
        longitude=77.25,
        timezone="Asia/Kolkata",
        retrieved_at="2026-10-31T05:30:00Z",
        temperature_c=25.0,
        source_reference="Mock Provider",
    )

    svc = WeatherService(adapter=mock_adapter, ttl_seconds=60.0)

    # First call: fresh retrieval
    res1 = await svc.get_current_weather(28.66, 77.25)
    assert res1.is_cached is False
    assert mock_adapter.get_current_weather.call_count == 1

    # Second call within TTL: served from cache
    res2 = await svc.get_current_weather(28.66, 77.25)
    assert res2.is_cached is True
    assert res2.cache_age_seconds >= 0.0
    assert mock_adapter.get_current_weather.call_count == 1  # No additional API call

    # Force refresh: bypasses cache
    res3 = await svc.get_current_weather(28.66, 77.25, force_refresh=True)
    assert res3.is_cached is False
    assert mock_adapter.get_current_weather.call_count == 2


def test_weather_service_coordinate_validation():
    svc = WeatherService()
    # Within Yamuna Corridor
    valid, err = svc.validate_coordinates(28.66, 77.25)  # Delhi ORB
    assert valid is True
    assert err is None

    valid, err = svc.validate_coordinates(30.31, 77.58)  # Hathnikund
    assert valid is True
    assert err is None

    # Far Outside Corridor
    valid, err = svc.validate_coordinates(12.97, 77.59)  # Bengaluru
    assert valid is False
    assert "outside the PRAVAAH study corridor" in err


# =====================================================================
# 3. Prepared Future Provider Tests
# =====================================================================

def test_prepared_future_adapters():
    cwc = CWCHydrologyAdapter()
    assert cwc.provider_name == "cwc_india_wris"
    assert cwc.readiness_status == IntegrationReadiness.PREPARED_FOR_FUTURE_INTEGRATION

    imd = IMDWeatherAdapter()
    assert imd.provider_name == "imd_india"
    assert imd.readiness_status == IntegrationReadiness.PREPARED_FOR_FUTURE_INTEGRATION

    gpm = NASAGPMAdapter()
    assert gpm.provider_name == "nasa_gpm_imerg"
    assert gpm.readiness_status == IntegrationReadiness.PREPARED_FOR_FUTURE_INTEGRATION
    meta = gpm.get_product_metadata()
    assert "0.1 degree" in meta["spatial_resolution"]


@pytest.mark.anyio
async def test_cwc_non_fabrication_guardrail():
    cwc = CWCHydrologyAdapter()
    with pytest.raises(NotImplementedError) as exc_info:
        await cwc.get_station_observation("CWC_YAM_002")
    assert "prepared for a future phase" in str(exc_info.value)


# =====================================================================
# 4. FastAPI Integration Route Tests
# =====================================================================

def test_get_weather_status_endpoint():
    mock_status_val = ProviderStatus(
        provider_name="open_meteo",
        is_available=True,
        status_code=200,
        latency_ms=45.2,
        last_checked="2026-10-31T05:30:00Z",
        notes=["Open-Meteo operational"],
    )
    with patch("app.services.weather_service.weather_service.check_status", new_callable=AsyncMock, return_value=mock_status_val):
        response = client.get("/api/weather/status")
        assert response.status_code == 200
        data = response.json()
        assert data["provider_name"] == "open_meteo"
        assert data["is_available"] is True


def test_get_corridor_locations_endpoint():
    response = client.get("/api/weather/locations")
    assert response.status_code == 200
    data = response.json()
    assert len(data["locations"]) >= 5
    station_ids = [loc["id"] for loc in data["locations"]]
    assert "HATHNIKUND_BARRAGE" in station_ids
    assert "DELHI_OLD_RAILWAY_BRIDGE" in station_ids


def test_get_basemap_config_endpoint():
    response = client.get("/api/weather/basemap/config")
    assert response.status_code == 200
    data = response.json()
    assert len(data["basemaps"]) >= 2
    assert data["default_basemap_id"] == "osm_standard"
    assert "west" in data["corridor_extent"]


def test_get_current_weather_endpoint_with_mock():
    mock_weather = NormalizedCurrentWeather(
        provider="open_meteo",
        latitude=28.66,
        longitude=77.25,
        timezone="Asia/Kolkata",
        retrieved_at="2026-10-31T05:30:00Z",
        temperature_c=26.4,
        relative_humidity_pct=60.0,
        precipitation_mm=0.0,
        wind_speed_kmh=10.2,
        source_reference="Open-Meteo Mock",
    )
    with patch("app.services.weather_service.weather_service.get_current_weather", new_callable=AsyncMock, return_value=mock_weather):
        response = client.get("/api/weather/current?lat=28.66&lon=77.25")
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "open_meteo"
        assert data["temperature_c"] == 26.4
        assert "flood warning" in data["scientific_disclaimer"].lower()


def test_get_current_weather_out_of_bounds():
    # 27.2 is within Query(ge=27.0, le=32.0) but outside corridor bounds [28.25 - 30.65]
    response = client.get("/api/weather/current?lat=27.2&lon=77.25")
    assert response.status_code == 400
    assert "outside the PRAVAAH study corridor" in response.json()["detail"]


def test_post_weather_refresh_endpoint_with_mock():
    mock_weather = NormalizedCurrentWeather(
        provider="open_meteo",
        latitude=28.66,
        longitude=77.25,
        timezone="Asia/Kolkata",
        retrieved_at="2026-10-31T05:30:00Z",
        temperature_c=25.8,
        source_reference="Open-Meteo Fresh",
    )
    with patch("app.services.weather_service.weather_service.get_current_weather", new_callable=AsyncMock, return_value=mock_weather):
        response = client.post(
            "/api/weather/refresh",
            json={"latitude": 28.66, "longitude": 77.25, "refresh_forecast": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["current"]["temperature_c"] == 25.8
