"""
backend/app/api/routes/forecasting.py

FastAPI router exposing upstream forecasting readiness, Phase 2B model status,
and validated experimental discharge prediction endpoints:
- GET /api/forecasting/readiness: Upstream 24h dataset readiness & baseline benchmarks (Phase 2A).
- GET /api/forecasting/model-status: Random Forest Regressor status, metrics, and governance (Phase 2B).
- POST /api/forecasting/predict: Validated 24h discharge forecast given 23 operational features (Phase 2B).
- GET /api/forecasting/sample-forecast: Demonstration forecast from latest verified historical observation (Phase 2B).

STRICT SCIENTIFIC SAFEGUARDS:
- Downstream Delhi water level prediction is STRICTLY GATED.
- No synthetic observations or unverified real-time claims.
- Never returns a fabricated forecast when model artifact is missing.
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.forecasting import (
    ForecastingReadinessResponse,
    DischargeModelStatusResponse,
    ExperimentalDischargeForecastRequest,
    ExperimentalDischargeForecastResponse,
    HydrometCouplingStatusResponse,
    LiveCoupledForecastRequest,
    LiveCoupledForecastResponse,
)
from app.services.forecasting import ForecastingService
from ml.models.inference import (
    ModelArtifactNotFoundError,
    InvalidFeatureSchemaError,
)

router = APIRouter(prefix="/forecasting", tags=["forecasting"])
service = ForecastingService()


@router.get(
    "/readiness",
    response_model=ForecastingReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Upstream Discharge Forecasting Readiness & Baselines",
    description=(
        "Returns verified dataset readiness, partition counts, and preliminary non-ML baseline benchmarks "
        "(Persistence, Trailing Mean, Seasonal-Naive, and Linear OLS) for 24-hour ahead Hathnikund downstream discharge."
    ),
)
def get_forecasting_readiness() -> ForecastingReadinessResponse:
    try:
        return service.get_readiness()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Required forecasting data files are unavailable: {str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving forecasting readiness: {str(exc)}",
        )


@router.get(
    "/model-status",
    response_model=DischargeModelStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Hathnikund Discharge Forecast Model Status & Metrics",
    description=(
        "Returns Phase 2B Random Forest Regressor operational status, validation (2022) and held-out test (2023-2024) "
        "evaluation metrics, high-flow subset diagnostics, permutation feature importance, and scientific governance gating. "
        "Strictly clarifies that the model is retained as an experimental benchmark and NOT promoted for autonomous flood warnings."
    ),
)
def get_model_status() -> DischargeModelStatusResponse:
    try:
        return service.get_model_status()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Trained model artifact or metadata unavailable: {str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving model status: {str(exc)}",
        )


@router.post(
    "/predict",
    response_model=ExperimentalDischargeForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Validated 24h Discharge Prediction (Experimental)",
    description=(
        "Generates experimental 24-hour ahead downstream discharge forecast (m³/s) for Hathnikund Barrage. "
        "Requires the exact 23 operational features defined in the feature manifest. Rejects invalid or out-of-domain inputs. "
        "Under no circumstances predicts Delhi water levels or flood breach probabilities."
    ),
)
def predict_discharge(
    request: ExperimentalDischargeForecastRequest,
) -> ExperimentalDischargeForecastResponse:
    try:
        return service.predict_discharge(request)
    except ModelArtifactNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model artifact not loaded or missing: {str(exc)}",
        )
    except InvalidFeatureSchemaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid feature schema: {str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(exc)}",
        )


@router.get(
    "/sample-forecast",
    response_model=ExperimentalDischargeForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Demonstration Forecast from Latest Verified Historical Observation",
    description=(
        "Demonstrates the Phase 2B inference pipeline using the latest complete historical observation from the dataset. "
        "Explicitly labelled as historical data demonstration, NOT live real-time telemetry."
    ),
)
def get_sample_historical_forecast() -> ExperimentalDischargeForecastResponse:
    try:
        return service.get_sample_historical_forecast()
    except ModelArtifactNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model artifact not loaded or missing: {str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating sample historical forecast: {str(exc)}",
        )


@router.get(
    "/hydromet-status",
    response_model=HydrometCouplingStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Hydrometeorological Feature Coupling & Compatibility Status",
    description=(
        "Audits the scientific compatibility of coupling live catchment meteorological feeds with hathnikund_rf_v1. "
        "Reports temporal alignment (08:30 IST window), spatial domain gaps (91 IMD cells vs 20 catchment nodes), "
        "and telemetry readiness."
    ),
)
def get_hydromet_status() -> HydrometCouplingStatusResponse:
    try:
        return service.get_hydromet_status()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving hydromet status: {str(exc)}",
        )


@router.post(
    "/predict-coupled",
    response_model=LiveCoupledForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Coupled Discharge Inference (Research Benchmark Only)",
    description=(
        "Executes 24-hour ahead discharge inference leveraging live Open-Meteo catchment rainfall features "
        "and validated discharge inputs. Explicitly distinguishes historical observations, live meteorological inputs, "
        "and missing telemetry. Strictly prohibited from autonomous flood warning issuance."
    ),
)
async def predict_coupled(
    request: LiveCoupledForecastRequest,
) -> LiveCoupledForecastResponse:
    try:
        return await service.predict_coupled(request)
    except ModelArtifactNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model artifact not loaded or missing: {str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Coupled inference error: {str(exc)}",
        )

