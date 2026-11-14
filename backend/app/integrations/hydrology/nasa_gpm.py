"""
backend/app/integrations/hydrology/nasa_gpm.py

NASA Global Precipitation Measurement (GPM) Adapter (Prepared Interface).
Prepares integration architecture for satellite-based gridded precipitation products
(IMERG: Integrated Multi-satellitE Retrievals for GPM) over the Upper Yamuna catchment.

STATUS: PREPARED_FOR_FUTURE_INTEGRATION (Phase 3C)
IMPORTANT:
- NASA GPM IMERG offers 0.1° (~10 km) half-hourly and daily precipitation estimates.
- Access requires Earthdata login credentials and HDF5/NetCDF/GeoTIFF raster processing pipelines.
- Never fabricates GPM rainfall values. Missing data remains explicitly missing.
"""

from typing import Optional, List, Dict, Any
from app.integrations.hydrology.base import (
    IntegrationReadiness,
)


class NASAGPMAdapter:
    """
    Prepared adapter for NASA GPM IMERG precipitation datasets.
    """

    EARTHDATA_GES_DISC_URL = "https://gpm1.gesdisc.eosdis.nasa.gov/opendap/GPM_L3"

    @property
    def provider_name(self) -> str:
        return "nasa_gpm_imerg"

    @property
    def readiness_status(self) -> IntegrationReadiness:
        return IntegrationReadiness.PREPARED_FOR_FUTURE_INTEGRATION

    async def get_catchment_precipitation(
        self,
        bounding_box: Dict[str, float],
        date_iso: str,
    ) -> Dict[str, Any]:
        """
        Prepared contract for querying GPM IMERG raster grids.
        """
        raise NotImplementedError(
            "NASA GPM IMERG integration is prepared for a future phase. "
            "Requires Earthdata OAuth2 authentication and xarray/rasterio HDF5 processing pipeline."
        )

    def get_product_metadata(self) -> Dict[str, Any]:
        """Returns scientific and spatial metadata for GPM IMERG."""
        return {
            "product": "GPM_3IMERGHHL (Early/Late)",
            "spatial_resolution": "0.1 degree (~10 km x 10 km)",
            "temporal_resolution": "30 minutes / daily aggregation",
            "coverage": "60°N - 60°S (Includes full Yamuna basin)",
            "latency": "IMERG Early: ~4 hours; IMERG Late: ~14 hours; Final: ~3.5 months",
            "access_method": "OPeNDAP / Earthdata HTTPS",
            "readiness": self.readiness_status.value,
        }
