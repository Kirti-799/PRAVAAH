"""
backend/app/integrations/rainfall/nasa_gpm.py

NASA Global Precipitation Measurement (GPM) IMERG Satellite Rainfall Adapter.
Models the NASA Goddard Earth Sciences Data and Information Services Center (GES DISC)
Integrated Multi-satellitE Retrievals for GPM (IMERG) product suite.

SCIENTIFIC & SOURCING AUDIT (PHASE 3D):
- Provider: NASA Goddard Space Flight Center (GSFC) / GES DISC.
- Product: GPM IMERG (Integrated Multi-satellitE Retrievals for GPM).
- Product Runs:
    1. Early Run: ~4-hour latency, half-hourly, forward morphing (near-real-time flood awareness).
    2. Late Run: ~14-hour latency, half-hourly, forward/backward morphing + climatological gauge calibration.
    3. Final Run: ~3.5-month latency, monthly/half-hourly, fully GPCC gauge-calibrated research benchmark.
- Spatial Resolution: 0.1° x 0.1° (~10 km at equator, ~11 km at 30°N).
- Temporal Resolution: 30 minutes.
- Measurement Units: mm/hr (calibrated precipitation rate).
- Timestamp Convention: UTC half-hour interval start/end.
- Licensing: Open Access / NASA Open Data Policy (Attribution Required).
- Access Blocker: Requires NASA Earthdata Login (URS OAuth2 / .netrc authentication).
  Automated REST access without an Earthdata bearer token returns HTTP 401 Unauthorized.
"""

from typing import Dict, List, Optional, Any
from app.integrations.rainfall.base import (
    BaseSpatialRainfallAdapter,
    ProviderProvenanceMetadata,
    RainfallProviderAvailability,
)
from app.integrations.exceptions import ProviderUnavailableError


class NASAGPMAdapter(BaseSpatialRainfallAdapter):
    """
    Adapter representing NASA GPM IMERG Early/Late satellite precipitation feeds.
    Strictly reports token authentication constraints and never fabricates satellite observations.
    """

    OPENDAP_BASE_URL = "https://gpm1.gesdisc.eosdis.nasa.gov/opendap/GPM_L3/GPM_3IMERGHHE.06"

    def __init__(self, earthdata_token: Optional[str] = None):
        self.earthdata_token = earthdata_token

    @property
    def provider_id(self) -> str:
        return "nasa_gpm_imerg"

    @property
    def provenance(self) -> ProviderProvenanceMetadata:
        return ProviderProvenanceMetadata(
            source_name="NASA GES DISC / GSFC",
            product_name="GPM IMERG Early Run (Half-Hourly 0.1° Satellite Precipitation)",
            product_version="GPM_3IMERGHHE_06",
            data_type="SATELLITE_MERGED",
            spatial_resolution="0.1° x 0.1° (~10 km x 10 km metric grid)",
            temporal_resolution="30 minutes",
            measurement_units="mm/hr",
            timestamp_convention="UTC half-hourly timestamps",
            observation_or_forecast="OBSERVATION",
            publication_latency="~4 hours publication delay for Early Run",
            licensing="NASA Earth Science Open Data Policy",
            availability_status=RainfallProviderAvailability.REQUIRES_AUTHENTICATION if not self.earthdata_token else RainfallProviderAvailability.OPERATIONAL,
            retrieval_method="HTTPS / OPeNDAP HDF5 subsetting via NASA Earthdata URS",
            access_constraints_or_blockers=(
                "Requires registered NASA Earthdata Login (URS) OAuth2 bearer token. "
                "Unauthenticated queries receive 401 Unauthorized redirect from GES DISC."
            ),
        )

    async def get_catchment_spatial_rainfall(
        self,
        sampling_nodes: List[Dict[str, Any]],
        forecast_days: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        NASA GPM is an observational satellite product; it does not produce forward forecasts.
        """
        if not self.earthdata_token:
            raise ProviderUnavailableError(
                self.provider_id,
                "NASA GPM IMERG ingestion requires NASA Earthdata Login credentials (EARTHDATA_TOKEN). "
                "Query blocked to prevent unauthenticated API failure."
            )
        raise ProviderUnavailableError(
            self.provider_id,
            "NASA GPM IMERG real-time streaming pipeline is scheduled for Phase 3E Cryosphere/Satellite integration."
        )

    async def check_health(self) -> Dict[str, Any]:
        """Validates credential configuration."""
        has_token = bool(self.earthdata_token)
        return {
            "provider_id": self.provider_id,
            "is_healthy": has_token,
            "availability_status": self.provenance.availability_status.value,
            "authenticated": has_token,
            "product_run": "IMERG Early Run (Latency ~4h)",
            "access_constraints": self.provenance.access_constraints_or_blockers,
        }

