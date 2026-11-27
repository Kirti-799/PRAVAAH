"""
backend/app/services/catchment_service.py

Domain service managing Hathnikund upstream catchment delineation,
morphometric terrain metrics, drainage networks, and raw DEM inventory status.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from app.schemas.catchment import (
    CatchmentStatusResponse,
    CatchmentSummaryResponse,
    PourPointInfo,
)


_repo_root = Path(__file__).resolve().parents[3]


class CatchmentService:
    """Service providing catchment boundaries, drainage topology, and DEM inventory."""

    def __init__(self, catchment_dir: Optional[Path] = None):
        self._delineator = None
        self._dem_manager = None
        self.catchment_dir = catchment_dir or (_repo_root / "data" / "processed" / "spatial" / "catchment")

    @property
    def delineator(self):
        if self._delineator is None:
            from ml.spatial.catchment import CatchmentDelineator
            self._delineator = CatchmentDelineator()
        return self._delineator

    @property
    def dem_manager(self):
        if self._dem_manager is None:
            from ml.spatial.dem_acquisition import DEMAcquisitionManager
            self._dem_manager = DEMAcquisitionManager()
        return self._dem_manager

    def _ensure_artifacts(self) -> None:
        """Ensures GeoJSON and metadata artifacts exist; generates them if missing."""
        c_path = self.catchment_dir / "hathnikund_upstream_catchment.geojson"
        if not c_path.exists():
            self.delineator.delineate_hathnikund_catchment()

    def get_catchment_status(self) -> CatchmentStatusResponse:
        """Returns operational readiness and inventory status of catchment infrastructure."""
        self._ensure_artifacts()
        inv = self.dem_manager.get_inventory_status()
        summary = self.get_catchment_summary()

        return CatchmentStatusResponse(
            service="PRAVAAH Catchment Delineation Infrastructure",
            delineation_status="DELINEATED",
            area_sq_km=summary.area_sq_km,
            pour_point_name=summary.pour_point.name,
            pour_point_lat=summary.pour_point.nominal_coordinates[0],
            pour_point_lon=summary.pour_point.nominal_coordinates[1],
            raw_dem_tiles_acquired=inv["tiles_acquired_count"],
            raw_dem_tiles_required=inv["tiles_total_required"],
            has_drainage_network=True,
            scientific_integrity_note=(
                "Topographic catchment contributing to Hathnikund Barrage. "
                "Covers 11,112 km² across Upper Yamuna, Tons, Giri, and Pabbar sub-basins. "
                "Does NOT represent downstream river corridor flood boundaries."
            ),
        )

    def get_catchment_summary(self) -> CatchmentSummaryResponse:
        """Returns morphometric statistics and hypsometry for the upstream watershed."""
        self._ensure_artifacts()
        m_path = self.catchment_dir / "catchment_metadata.json"
        with open(m_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return CatchmentSummaryResponse(
            catchment_id=data["catchment_id"],
            catchment_name=data["catchment_name"],
            pour_point=PourPointInfo(**data["pour_point"]),
            area_sq_km=data["area_sq_km"],
            perimeter_km=data["perimeter_km"],
            elevation_min_m=data["elevation_min_m"],
            elevation_max_m=data["elevation_max_m"],
            elevation_mean_m=data["elevation_mean_m"],
            elevation_median_m=data["elevation_median_m"],
            elevation_std_m=data["elevation_std_m"],
            hypsometry_percentiles=data["hypsometry_percentiles"],
            bounding_box=data["bounding_box"],
            contributing_cells_count=data["contributing_cells_count"],
            stream_length_total_km=data["stream_length_total_km"],
            drainage_density_km_per_sq_km=data["drainage_density_km_per_sq_km"],
            major_tributaries=data["major_tributaries"],
            scientific_caveats=data["scientific_caveats"],
        )

    def get_catchment_geometry(self) -> Dict[str, Any]:
        """Returns the GeoJSON FeatureCollection of the delineated catchment boundary."""
        self._ensure_artifacts()
        c_path = self.catchment_dir / "hathnikund_upstream_catchment.geojson"
        with open(c_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_catchment_drainage(self) -> Dict[str, Any]:
        """Returns the GeoJSON FeatureCollection of the extracted drainage stream network."""
        self._ensure_artifacts()
        d_path = self.catchment_dir / "hathnikund_drainage_network.geojson"
        with open(d_path, "r", encoding="utf-8") as f:
            return json.load(f)


catchment_service = CatchmentService()
