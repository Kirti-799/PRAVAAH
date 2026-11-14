"""
backend/app/integrations/rainfall/imd.py

India Meteorological Department (IMD) Gridded Rainfall Adapter.
Models the official IMD National Climate Centre (NCC) 0.25° x 0.25° Daily Gridded Rainfall product.

SCIENTIFIC & SOURCING AUDIT (PHASE 3D):
- Provider: India Meteorological Department (IMD), Ministry of Earth Sciences, Govt. of India.
- Product: 0.25° x 0.25° Daily Gridded Rainfall (Rainfall_0.25_year.GRD) and 1.0° x 1.0° legacy.
- Spatial Resolution: 0.25° (~27.5 km at Yamuna latitudes; 135 x 129 grid points for India).
- Temporal Resolution: Daily (24-hour accumulation ending at 08:30 IST / 03:00 UTC).
- Latency: Published with T+24h to T+48h operational delay; annual consolidated archives.
- Licensing: IMD Data Policy (Academic/Research registration required; commercial use fee-based).
- Access Blocker: No unauthenticated real-time public REST API exists.
  Data is released as binary float32 .GRD files via CDAC/IMD data portal requiring registered credentials.
"""

from typing import Dict, List, Optional, Any
from app.integrations.rainfall.base import (
    BaseSpatialRainfallAdapter,
    ProviderProvenanceMetadata,
    RainfallProviderAvailability,
)
from app.integrations.exceptions import ProviderUnavailableError


class IMDRainfallAdapter(BaseSpatialRainfallAdapter):
    """
    Adapter representing IMD Gridded Rainfall products.
    Preserves native 0.25° spatial and 24h temporal resolution contracts.
    Explicitly reports OFFLINE_ARCHIVE_ONLY status when no local archive files exist.
    """

    def __init__(self, archive_dir: Optional[str] = None):
        self.archive_dir = archive_dir or "data/raw/spatial/rainfall/imd"

    @property
    def provider_id(self) -> str:
        return "imd_gridded_rainfall"

    @property
    def provenance(self) -> ProviderProvenanceMetadata:
        return ProviderProvenanceMetadata(
            source_name="India Meteorological Department (IMD)",
            product_name="IMD 0.25° Daily Gridded Rainfall (Pai et al., 2014)",
            product_version="v2.0 (High Resolution Daily Gridded)",
            data_type="GAUGE_INTERPOLATED",
            spatial_resolution="0.25° x 0.25° (~27.5 km x 27.5 km)",
            temporal_resolution="Daily (08:30 IST to 08:30 IST accumulation)",
            measurement_units="mm/day",
            timestamp_convention="IST (UTC+05:30) 24h window ending 08:30",
            observation_or_forecast="OBSERVATION",
            publication_latency="T+24h to T+48h post observation",
            licensing="Government of India Open Data / IMD Data Supply Agreement",
            availability_status=RainfallProviderAvailability.OFFLINE_ARCHIVE_ONLY,
            retrieval_method="Binary float32 raster (.GRD) direct file ingestion",
            access_constraints_or_blockers=(
                "IMD does not offer an open real-time streaming REST API for gridded rainfall. "
                "Operational deployment requires periodic batch ingestion of .GRD files via IMD portal."
            ),
        )

    async def get_catchment_spatial_rainfall(
        self,
        sampling_nodes: List[Dict[str, Any]],
        forecast_days: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        IMD gridded rainfall is an observational archive; it does not produce forward forecasts.
        """
        raise ProviderUnavailableError(
            self.provider_id,
            "IMD 0.25° Gridded Rainfall is an observational archive product. "
            "Real-time REST querying is unavailable without local .GRD archive synchronization."
        )

    async def check_health(self) -> Dict[str, Any]:
        """Reports offline archive availability."""
        from pathlib import Path
        p = Path(self.archive_dir)
        has_files = p.exists() and any(p.glob("*.GRD"))
        return {
            "provider_id": self.provider_id,
            "is_healthy": has_files,
            "availability_status": self.provenance.availability_status.value,
            "archive_dir": str(p),
            "files_found": len(list(p.glob("*.GRD"))) if p.exists() else 0,
            "access_constraints": self.provenance.access_constraints_or_blockers,
        }

