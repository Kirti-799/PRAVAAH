"""
backend/app/integrations/hydrology/cwc.py

Central Water Commission (CWC) & India-WRIS Adapter (Prepared Interface).
Prepares integration architecture for official Indian river gauge observations,
barrage discharge releases, and flood bulletins along the Yamuna corridor.

STATUS: PREPARED_FOR_FUTURE_INTEGRATION (Phase 3C)
IMPORTANT:
- Official India-WRIS / CWC data does not currently offer an open, unauthenticated REST API.
- Live data requires institutional credentials or automated ingestion of public flood bulletins.
- Never fabricates CWC responses. Missing data remains explicitly missing.
"""

from typing import Optional, List, Dict, Any
from app.integrations.hydrology.base import (
    BaseHydrologyAdapter,
    IntegrationReadiness,
    HydrologicalObservation,
)


class CWCHydrologyAdapter(BaseHydrologyAdapter):
    """
    Prepared adapter for Central Water Commission (CWC) and India-WRIS data.
    """

    CORRIDOR_GAUGES: List[Dict[str, Any]] = [
        {
            "station_id": "CWC_YAM_001",
            "name": "Hathnikund Barrage",
            "agency": "Haryana Irrigation / CWC",
            "latitude": 30.31,
            "longitude": 77.58,
            "variable": "DISCHARGE_CUMECS",
            "status": "AWAITING_INGESTION_PIPELINE",
        },
        {
            "station_id": "CWC_YAM_002",
            "name": "Delhi Old Railway Bridge (ORB)",
            "agency": "CWC",
            "latitude": 28.66,
            "longitude": 77.25,
            "warning_level_m": 204.50,
            "danger_level_m": 205.33,
            "hfl_m": 208.66,  # July 2023 Flood
            "variable": "WATER_LEVEL_M",
            "status": "AWAITING_INGESTION_PIPELINE",
        },
        {
            "station_id": "CWC_YAM_003",
            "name": "Okhla Barrage",
            "agency": "UP Irrigation / CWC",
            "latitude": 28.53,
            "longitude": 77.30,
            "variable": "DISCHARGE_CUMECS",
            "status": "AWAITING_INGESTION_PIPELINE",
        },
    ]

    @property
    def provider_name(self) -> str:
        return "cwc_india_wris"

    @property
    def readiness_status(self) -> IntegrationReadiness:
        return IntegrationReadiness.PREPARED_FOR_FUTURE_INTEGRATION

    async def get_station_observation(
        self,
        station_id: str,
    ) -> Optional[HydrologicalObservation]:
        """
        Prepared contract for CWC gauge observations.
        Raises NotImplementedError to guarantee no synthetic data is injected.
        """
        raise NotImplementedError(
            f"CWC live API integration is prepared for a future phase. "
            f"Institutional API access or official bulletin parser required for station '{station_id}'."
        )

    async def get_study_corridor_stations(self) -> List[Dict[str, Any]]:
        """List official CWC stations mapped along the study corridor."""
        return self.CORRIDOR_GAUGES
