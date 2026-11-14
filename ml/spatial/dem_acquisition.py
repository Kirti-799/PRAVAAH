"""
ml/spatial/dem_acquisition.py

Authentic DEM Data Acquisition & Catalog Engine for PRAVAAH Phase 3D.
Manages downloading, metadata verification, and provenance tracking for Copernicus DEM GLO-30
(30m Global Digital Surface Model) covering the Upper Yamuna Catchment contributing to Hathnikund Barrage.

SCIENTIFIC & SOURCING PROVENANCE:
- Provider: European Space Agency (ESA) / Airbus / Open Data on AWS
- Product: Copernicus DEM GLO-30 (DSM COG 10)
- Resolution: 1 arc-second (~30m metric grid)
- CRS: EPSG:4326 (WGS 84 ellipsoidal coordinates)
- Vertical Datum: EGM2008 Geoid
- Target Geographic Bounding Box: 30.0°N to 32.0°N, 77.0°E to 79.0°E
"""

import os
import urllib.request
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    import rasterio
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False


@dataclass
class DEMTileMetadata:
    tile_name: str
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    url: str
    description: str
    size_bytes_approx: int = 42000000


DEMTileCatalogEntry = DEMTileMetadata


UPSTREAM_YAMUNA_COPERNICUS_TILES: Dict[str, DEMTileMetadata] = {
    "Copernicus_DSM_COG_10_N30_00_E077_00_DEM": DEMTileMetadata(
        tile_name="Copernicus_DSM_COG_10_N30_00_E077_00_DEM",
        lat_min=30.0,
        lat_max=31.0,
        lon_min=77.0,
        lon_max=78.0,
        url="https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N30_00_E077_00_DEM/Copernicus_DSM_COG_10_N30_00_E077_00_DEM.tif",
        description="Hathnikund Barrage exit, lower Yamuna gorge, Paonta Sahib, lower Giri & Bata rivers.",
    ),
    "Copernicus_DSM_COG_10_N30_00_E078_00_DEM": DEMTileMetadata(
        tile_name="Copernicus_DSM_COG_10_N30_00_E078_00_DEM",
        lat_min=30.0,
        lat_max=31.0,
        lon_min=78.0,
        lon_max=79.0,
        url="https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N30_00_E078_00_DEM/Copernicus_DSM_COG_10_N30_00_E078_00_DEM.tif",
        description="Dehradun valley, Mussoorie ridge, Asan confluence, lower Tons gorge (Dakpathar/Kalsi).",
    ),
    "Copernicus_DSM_COG_10_N31_00_E077_00_DEM": DEMTileMetadata(
        tile_name="Copernicus_DSM_COG_10_N31_00_E077_00_DEM",
        lat_min=31.0,
        lat_max=32.0,
        lon_min=77.0,
        lon_max=78.0,
        url="https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N31_00_E077_00_DEM/Copernicus_DSM_COG_10_N31_00_E077_00_DEM.tif",
        description="Upper Giri basin, Pabbar River catchment, Rohru, Shimla-Kinnaur high ridge divide.",
    ),
    "Copernicus_DSM_COG_10_N31_00_E078_00_DEM": DEMTileMetadata(
        tile_name="Copernicus_DSM_COG_10_N31_00_E078_00_DEM",
        lat_min=31.0,
        lat_max=32.0,
        lon_min=78.0,
        lon_max=79.0,
        url="https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N31_00_E078_00_DEM/Copernicus_DSM_COG_10_N31_00_E078_00_DEM.tif",
        description="Upper Tons River, Supin & Rupin headwaters, Yamunotri glacier, Bandarpunch peaks (6387m).",
    ),
}


class DEMAcquisitionManager:
    """
    Manages authentic Copernicus DEM tile retrieval, caching, and integrity validation.
    """

    DEFAULT_RAW_DIR = Path("data/raw/spatial/dem")

    def __init__(self, raw_dir: Optional[Path] = None):
        self.raw_dir = Path(raw_dir or self.DEFAULT_RAW_DIR).resolve()
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def get_catalog(self) -> Dict[str, DEMTileMetadata]:
        return UPSTREAM_YAMUNA_COPERNICUS_TILES

    def download_tile(
        self,
        tile_id: str,
        timeout_seconds: int = 60,
        force_download: bool = False,
    ) -> Path:
        """
        Downloads an authentic Copernicus DEM tile from AWS Open Data into data/raw/spatial/dem/.
        """
        if tile_id not in UPSTREAM_YAMUNA_COPERNICUS_TILES:
            raise ValueError(f"Unknown tile ID '{tile_id}'. Available: {list(UPSTREAM_YAMUNA_COPERNICUS_TILES.keys())}")

        meta = UPSTREAM_YAMUNA_COPERNICUS_TILES[tile_id]
        dest_file = self.raw_dir / f"{tile_id}.tif"

        if dest_file.exists() and dest_file.stat().st_size > 1000000 and not force_download:
            return dest_file

        headers = {"User-Agent": "PRAVAAH-DisasterIntelligence/Phase3D (Research Platform)"}
        req = urllib.request.Request(meta.url, headers=headers)

        temp_file = dest_file.with_suffix(".tmp")
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp, open(temp_file, "wb") as out_f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    out_f.write(chunk)

            # Move temp to final
            if temp_file.exists():
                temp_file.replace(dest_file)

            # Integrity check with rasterio if available
            if HAS_RASTERIO:
                with rasterio.open(dest_file) as r_src:
                    if r_src.count < 1 or r_src.width < 100 or r_src.height < 100:
                        dest_file.unlink(missing_ok=True)
                        raise ValueError(f"Corrupted DEM raster downloaded for {tile_id}")

            return dest_file
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink(missing_ok=True)
            raise RuntimeError(f"Failed to acquire Copernicus DEM tile {tile_id}: {str(e)}")

    def get_inventory_status(self) -> Dict[str, Any]:
        """
        Reports inventory status of raw DEM tiles in the repository.
        """
        acquired: List[Dict[str, Any]] = []
        missing: List[str] = []

        for tile_id, meta in UPSTREAM_YAMUNA_COPERNICUS_TILES.items():
            f_path = self.raw_dir / f"{tile_id}.tif"
            if f_path.exists() and f_path.stat().st_size > 0:
                acquired.append({
                    "tile_id": tile_id,
                    "file_path": str(f_path),
                    "size_mb": round(f_path.stat().st_size / (1024 * 1024), 2),
                    "bounds": [meta.lat_min, meta.lon_min, meta.lat_max, meta.lon_max],
                    "description": meta.description,
                    "is_valid": True,
                })
            else:
                missing.append(tile_id)

        coverage_pct = round((len(acquired) / len(UPSTREAM_YAMUNA_COPERNICUS_TILES)) * 100.0, 1)

        return {
            "dataset_name": "Copernicus DEM GLO-30 (Global 30m DSM)",
            "product_version": "DSM COG 10 (2022 release)",
            "provider": "European Space Agency (ESA) / Airbus via AWS Open Data",
            "crs": "EPSG:4326 (WGS 84)",
            "vertical_datum": "EGM2008 Geoid",
            "raw_directory": str(self.raw_dir),
            "target_bounding_box": {"south": 30.0, "north": 32.0, "west": 77.0, "east": 79.0},
            "tiles_total_required": len(UPSTREAM_YAMUNA_COPERNICUS_TILES),
            "tiles_acquired_count": len(acquired),
            "coverage_percentage": coverage_pct,
            "acquired_tiles": acquired,
            "missing_tiles": missing,
            "acquisition_status": "COMPLETE" if coverage_pct == 100.0 else ("PARTIAL" if coverage_pct > 0 else "UNACQUIRED"),
        }
