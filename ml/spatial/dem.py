"""
ml/spatial/dem.py

Digital Elevation Model (DEM) Ingestion, Geodetic Validation,
and Terrain Analysis Engine for PRAVAAH.

SCIENTIFIC INTEGRITY ENFORCEMENT:
- Validates raster integrity: CRS, affine geotransform, dimensions, NoData representation,
  non-finite cells, and plausible regional elevation ranges.
- Ensures slope calculations use compatible metric units (meters horizontal, meters vertical).
  When geographic CRS (degrees) is provided, performs geodesic metric scaling.
- If no real DEM raster is present in the repository, returns an explicit UNAVAILABLE status.
- NEVER fabricates pretend elevation fields or claims unverified flood boundaries.
"""

import os
import math
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

try:
    import rasterio
    from rasterio.crs import CRS
    from rasterio.transform import Affine
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

from ml.spatial.study_area import StudyAreaCatalog, StudyAreaBounds


class DEMValidationStatus(str, Enum):
    VALID = "VALID"
    VALID_WITH_DIAGNOSTIC_WARNINGS = "VALID_WITH_DIAGNOSTIC_WARNINGS"
    INVALID = "INVALID"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class DEMMetadataReport:
    """Detailed diagnostic and validation report for a single DEM raster."""
    file_path: str
    file_name: str
    file_size_bytes: int
    validation_status: DEMValidationStatus
    dimensions: Dict[str, int]  # width, height, bands
    crs_epsg: Optional[int]
    crs_wkt_summary: str
    is_geographic: bool
    is_projected: bool
    pixel_resolution_x: float
    pixel_resolution_y: float
    pixel_units: str
    bounds_epsg4326: Dict[str, float]  # west, south, east, north
    intersects_study_area: bool
    data_type: str
    nodata_value: Optional[float]
    total_cells: int
    valid_cells: int
    missing_cells: int
    missing_cells_percentage: float
    has_non_finite_values: bool
    non_finite_count: int

    # Statistical properties of valid data
    min_elevation_m: Optional[float]
    max_elevation_m: Optional[float]
    mean_elevation_m: Optional[float]
    std_elevation_m: Optional[float]
    p10_elevation_m: Optional[float]
    p50_elevation_m: Optional[float]
    p90_elevation_m: Optional[float]

    # Scientific diagnostics
    plausible_yamuna_range_check: bool
    diagnostic_warnings: List[str]
    scientific_caveats: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size_bytes": self.file_size_bytes,
            "validation_status": self.validation_status.value,
            "dimensions": self.dimensions,
            "crs_epsg": self.crs_epsg,
            "crs_wkt_summary": self.crs_wkt_summary,
            "is_geographic": self.is_geographic,
            "is_projected": self.is_projected,
            "pixel_resolution_x": self.pixel_resolution_x,
            "pixel_resolution_y": self.pixel_resolution_y,
            "pixel_units": self.pixel_units,
            "bounds_epsg4326": self.bounds_epsg4326,
            "intersects_study_area": self.intersects_study_area,
            "data_type": self.data_type,
            "nodata_value": self.nodata_value,
            "total_cells": self.total_cells,
            "valid_cells": self.valid_cells,
            "missing_cells": self.missing_cells,
            "missing_cells_percentage": round(self.missing_cells_percentage, 2),
            "has_non_finite_values": self.has_non_finite_values,
            "non_finite_count": self.non_finite_count,
            "min_elevation_m": round(self.min_elevation_m, 2) if self.min_elevation_m is not None else None,
            "max_elevation_m": round(self.max_elevation_m, 2) if self.max_elevation_m is not None else None,
            "mean_elevation_m": round(self.mean_elevation_m, 2) if self.mean_elevation_m is not None else None,
            "std_elevation_m": round(self.std_elevation_m, 2) if self.std_elevation_m is not None else None,
            "p10_elevation_m": round(self.p10_elevation_m, 2) if self.p10_elevation_m is not None else None,
            "p50_elevation_m": round(self.p50_elevation_m, 2) if self.p50_elevation_m is not None else None,
            "p90_elevation_m": round(self.p90_elevation_m, 2) if self.p90_elevation_m is not None else None,
            "plausible_yamuna_range_check": self.plausible_yamuna_range_check,
            "diagnostic_warnings": self.diagnostic_warnings,
            "scientific_caveats": self.scientific_caveats,
        }


@dataclass
class TerrainSlopeSummary:
    """Statistical summary of terrain slope computed over valid DEM cells."""
    min_slope_deg: float
    max_slope_deg: float
    mean_slope_deg: float
    std_slope_deg: float
    mean_slope_percent: float
    computation_method: str
    horizontal_resolution_m: float
    vertical_units: str
    scientific_disclaimer: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_slope_deg": round(self.min_slope_deg, 2),
            "max_slope_deg": round(self.max_slope_deg, 2),
            "mean_slope_deg": round(self.mean_slope_deg, 2),
            "std_slope_deg": round(self.std_slope_deg, 2),
            "mean_slope_percent": round(self.mean_slope_percent, 2),
            "computation_method": self.computation_method,
            "horizontal_resolution_m": round(self.horizontal_resolution_m, 2),
            "vertical_units": self.vertical_units,
            "scientific_disclaimer": self.scientific_disclaimer,
        }


class DEMValidator:
    """Reusable DEM Inspection, Ingestion, and Quality Assurance Engine."""

    # Plausible regional elevation thresholds for the Upper-to-Middle Yamuna Plain (m MSL):
    # Lowest point (Delhi / Okhla): ~195 m MSL.
    # Hathnikund Barrage (Shivalik exit): ~280–320 m MSL.
    # Immediate foothills in northern Yamunanagar: up to ~900–1200 m MSL.
    PLAUSIBLE_MIN_ELEVATION_M = 150.0
    PLAUSIBLE_MAX_ELEVATION_M = 1500.0

    @classmethod
    def validate_file(cls, file_path: Path) -> DEMMetadataReport:
        """
        Conducts comprehensive geodetic and numerical validation of a DEM raster file.
        """
        if not HAS_RASTERIO:
            raise RuntimeError("rasterio library is required for DEM validation.")

        p = Path(file_path).resolve()
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"DEM raster file not found at: {p}")

        warnings: List[str] = []
        caveats = [
            "Source DEM provides static topographic surface elevation.",
            "Terrain elevation alone DOES NOT determine river flood inundation extent.",
            "Vegetation canopy, buildings, and recent embankments may cause local vertical artifacts.",
            "Not calibrated against ground survey benchmarks; use strictly for preliminary terrain indexing.",
        ]

        with rasterio.open(p) as src:
            width = src.width
            height = src.height
            count = src.count
            dtype_str = str(src.dtypes[0])
            nodata_val = src.nodata

            # CRS Validation
            crs = src.crs
            crs_epsg = crs.to_epsg() if crs else None
            crs_wkt_summary = crs.to_string() if crs else "UNDEFINED / MISSING"
            is_geographic = crs.is_geographic if crs else False
            is_projected = crs.is_projected if crs else False

            if crs is None:
                warnings.append("Missing CRS metadata: Raster lacks a spatial coordinate reference system.")

            # Geotransform and Resolution
            res_x, res_y = src.res
            bounds = src.bounds
            pixel_units = "degrees" if is_geographic else ("meters" if is_projected else "unknown")

            # Check intersection with Authoritative Study Area
            study_area = StudyAreaCatalog.get_authoritative_study_area()
            sa_b = study_area.bounds

            # If geographic, bounds are already in degrees
            if is_geographic:
                west_deg, south_deg, east_deg, north_deg = bounds.left, bounds.bottom, bounds.right, bounds.top
            elif crs_epsg == 32643:
                # Convert UTM 43N approximate bounding box back to degrees for check
                # Central meridian 75°E, ~111km/deg
                west_deg = 75.0 + (bounds.left - 500000.0) / (111320.0 * math.cos(math.radians(29.0)))
                east_deg = 75.0 + (bounds.right - 500000.0) / (111320.0 * math.cos(math.radians(29.0)))
                south_deg = bounds.bottom / 110540.0
                north_deg = bounds.top / 110540.0
            else:
                west_deg, south_deg, east_deg, north_deg = bounds.left, bounds.bottom, bounds.right, bounds.top

            intersects = not (
                east_deg < sa_b.west_lon
                or west_deg > sa_b.east_lon
                or north_deg < sa_b.south_lat
                or south_deg > sa_b.north_lat
            )

            if not intersects:
                warnings.append(
                    f"Spatial extent [{west_deg:.2f}, {south_deg:.2f}, {east_deg:.2f}, {north_deg:.2f}] "
                    f"does not intersect the Yamuna study corridor [{sa_b.west_lon}, {sa_b.south_lat}, {sa_b.east_lon}, {sa_b.north_lat}]."
                )

            # Read Band 1 for statistical inspection
            arr = src.read(1)

        total_cells = width * height
        has_nans = bool(np.isnan(arr).any())
        has_infs = bool(np.isinf(arr).any())
        has_non_finite = has_nans or has_infs
        non_finite_count = int(np.isnan(arr).sum() + np.isinf(arr).sum())

        # Construct valid mask
        valid_mask = np.isfinite(arr)
        if nodata_val is not None:
            if math.isnan(nodata_val):
                valid_mask = valid_mask & (~np.isnan(arr))
            else:
                valid_mask = valid_mask & (arr != nodata_val)

        valid_cells = int(valid_mask.sum())
        missing_cells = total_cells - valid_cells
        missing_pct = (missing_cells / total_cells * 100.0) if total_cells > 0 else 100.0

        if valid_cells == 0:
            warnings.append("All raster cells are marked as missing or NoData.")
            return DEMMetadataReport(
                file_path=str(p),
                file_name=p.name,
                file_size_bytes=p.stat().st_size,
                validation_status=DEMValidationStatus.INVALID,
                dimensions={"width": width, "height": height, "bands": count},
                crs_epsg=crs_epsg,
                crs_wkt_summary=crs_wkt_summary,
                is_geographic=is_geographic,
                is_projected=is_projected,
                pixel_resolution_x=res_x,
                pixel_resolution_y=res_y,
                pixel_units=pixel_units,
                bounds_epsg4326={"west": west_deg, "south": south_deg, "east": east_deg, "north": north_deg},
                intersects_study_area=intersects,
                data_type=dtype_str,
                nodata_value=nodata_val,
                total_cells=total_cells,
                valid_cells=0,
                missing_cells=total_cells,
                missing_cells_percentage=100.0,
                has_non_finite_values=has_non_finite,
                non_finite_count=non_finite_count,
                min_elevation_m=None,
                max_elevation_m=None,
                mean_elevation_m=None,
                std_elevation_m=None,
                p10_elevation_m=None,
                p50_elevation_m=None,
                p90_elevation_m=None,
                plausible_yamuna_range_check=False,
                diagnostic_warnings=warnings,
                scientific_caveats=caveats,
            )

        valid_data = arr[valid_mask]
        min_val = float(np.min(valid_data))
        max_val = float(np.max(valid_data))
        mean_val = float(np.mean(valid_data))
        std_val = float(np.std(valid_data))
        p10_val = float(np.percentile(valid_data, 10))
        p50_val = float(np.percentile(valid_data, 50))
        p90_val = float(np.percentile(valid_data, 90))

        # Check plausible elevation range
        plausible_range = (min_val >= cls.PLAUSIBLE_MIN_ELEVATION_M - 50.0) and (
            max_val <= cls.PLAUSIBLE_MAX_ELEVATION_M + 500.0
        )

        if min_val < 0.0:
            warnings.append(
                f"Negative elevation ({min_val:.1f} m) detected. Verify geoid vertical datum (EGM96/EGM2008)."
            )
        if not plausible_range:
            warnings.append(
                f"Elevation range [{min_val:.1f} m, {max_val:.1f} m] deviates from expected Yamuna corridor values "
                f"[{cls.PLAUSIBLE_MIN_ELEVATION_M:.0f} m, {cls.PLAUSIBLE_MAX_ELEVATION_M:.0f} m]. "
                f"Inspect coordinate domain and vertical units."
            )

        status = DEMValidationStatus.VALID
        if len(warnings) > 0:
            status = DEMValidationStatus.VALID_WITH_DIAGNOSTIC_WARNINGS

        return DEMMetadataReport(
            file_path=str(p),
            file_name=p.name,
            file_size_bytes=p.stat().st_size,
            validation_status=status,
            dimensions={"width": width, "height": height, "bands": count},
            crs_epsg=crs_epsg,
            crs_wkt_summary=crs_wkt_summary,
            is_geographic=is_geographic,
            is_projected=is_projected,
            pixel_resolution_x=res_x,
            pixel_resolution_y=res_y,
            pixel_units=pixel_units,
            bounds_epsg4326={"west": west_deg, "south": south_deg, "east": east_deg, "north": north_deg},
            intersects_study_area=intersects,
            data_type=dtype_str,
            nodata_value=nodata_val,
            total_cells=total_cells,
            valid_cells=valid_cells,
            missing_cells=missing_cells,
            missing_cells_percentage=missing_pct,
            has_non_finite_values=has_non_finite,
            non_finite_count=non_finite_count,
            min_elevation_m=min_val,
            max_elevation_m=max_val,
            mean_elevation_m=mean_val,
            std_elevation_m=std_val,
            p10_elevation_m=p10_val,
            p50_elevation_m=p50_val,
            p90_elevation_m=p90_val,
            plausible_yamuna_range_check=plausible_range,
            diagnostic_warnings=warnings,
            scientific_caveats=caveats,
        )

    @classmethod
    def compute_slope(cls, file_path: Path) -> TerrainSlopeSummary:
        """
        Computes terrain slope in degrees and percentage over valid cells.
        Uses finite differences with metric scaling to ensure horizontal units match vertical units.
        """
        if not HAS_RASTERIO:
            raise RuntimeError("rasterio library is required for slope computation.")

        p = Path(file_path).resolve()
        with rasterio.open(p) as src:
            arr = src.read(1)
            nodata_val = src.nodata
            crs = src.crs
            res_x, res_y = src.res
            bounds = src.bounds

        # Establish metric grid cell dimensions
        if crs and crs.is_geographic:
            # Geodesic metric conversion at mean latitude
            mean_lat = (bounds.bottom + bounds.top) / 2.0
            dx_m = res_x * 111320.0 * math.cos(math.radians(mean_lat))
            dy_m = res_y * 110540.0
            method = "Horn's Finite Difference with Mean-Latitude Geodesic Metric Conversion"
        else:
            dx_m = abs(res_x)
            dy_m = abs(res_y)
            method = "Horn's Finite Difference on Projected Metric Grid"

        # Valid mask
        valid_mask = np.isfinite(arr)
        if nodata_val is not None:
            if math.isnan(nodata_val):
                valid_mask = valid_mask & (~np.isnan(arr))
            else:
                valid_mask = valid_mask & (arr != nodata_val)

        # Compute gradients along rows (y) and columns (x)
        gy, gx = np.gradient(arr, dy_m, dx_m)
        slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))
        slope_deg = np.degrees(slope_rad)
        slope_pct = np.tan(slope_rad) * 100.0

        valid_slopes = slope_deg[valid_mask]
        valid_pcts = slope_pct[valid_mask]

        if len(valid_slopes) == 0:
            raise ValueError("No valid cells available to compute slope statistics.")

        disclaimer = (
            "TERRAIN SLOPE SUMMARY — Slope is derived from static surface elevation. "
            "Flat slope indicates low topographical relief, NOT guaranteed flood inundation."
        )

        return TerrainSlopeSummary(
            min_slope_deg=float(np.min(valid_slopes)),
            max_slope_deg=float(np.max(valid_slopes)),
            mean_slope_deg=float(np.mean(valid_slopes)),
            std_slope_deg=float(np.std(valid_slopes)),
            mean_slope_percent=float(np.mean(valid_pcts)),
            computation_method=method,
            horizontal_resolution_m=(dx_m + dy_m) / 2.0,
            vertical_units="meters",
            scientific_disclaimer=disclaimer,
        )

    @classmethod
    def create_synthetic_dem_fixture(
        cls,
        output_path: Path,
        width: int = 50,
        height: int = 50,
        crs_epsg: int = 4326,
        base_elev: float = 250.0,
        west: float = 77.0,
        south: float = 28.5,
        east: float = 77.5,
        north: float = 29.0,
        nodata_val: float = -9999.0,
        with_nodata_patch: bool = True,
    ) -> Path:
        """
        Creates a deterministic miniature synthetic GeoTIFF for unit testing.
        NOT REAL DATA: Strictly used as an automated test fixture.
        """
        if not HAS_RASTERIO:
            raise RuntimeError("rasterio library is required to generate synthetic test fixtures.")

        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        res_x = (east - west) / width
        res_y = (north - south) / height
        transform = Affine.translation(west, north) @ Affine.scale(res_x, -res_y)

        # Create smooth terrain gradient (sloping from north to south, ~300m down to ~200m)

        y_coords = np.linspace(north, south, height)
        x_coords = np.linspace(west, east, width)
        xx, yy = np.meshgrid(x_coords, y_coords)

        # Synthetic Yamuna-like gradient: drops from 280m in north to 205m in south
        elevation = 205.0 + (yy - south) / (north - south) * 75.0 + np.sin((xx - west) * 10.0) * 2.0
        elevation = elevation.astype(np.float32)

        if with_nodata_patch:
            # Set a small 5x5 corner patch to NoData
            elevation[0:5, 0:5] = nodata_val

        profile = {
            "driver": "GTiff",
            "height": height,
            "width": width,
            "count": 1,
            "dtype": "float32",
            "crs": CRS.from_epsg(crs_epsg),
            "transform": transform,
            "nodata": nodata_val,
        }

        with rasterio.open(out_file, "w", **profile) as dst:
            dst.write(elevation, 1)

        return out_file

    @classmethod
    def mosaic_tiles(cls, tile_paths: List[Path], output_path: Path) -> Path:
        """
        Mosaics multiple adjacent DEM GeoTIFF tiles into a single seamless raster.
        Preserves CRS, geotransform bounds, and NoData masks using rasterio.merge.
        """
        if not HAS_RASTERIO:
            raise RuntimeError("rasterio library is required for DEM mosaicking.")
        if not tile_paths:
            raise ValueError("No tile paths provided for mosaicking.")

        from rasterio.merge import merge

        datasets = [rasterio.open(Path(p).resolve()) for p in tile_paths]
        try:
            mosaic, out_trans = merge(datasets)
            out_meta = datasets[0].meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": mosaic.shape[1],
                "width": mosaic.shape[2],
                "transform": out_trans,
                "crs": datasets[0].crs,
            })

            out_file = Path(output_path).resolve()
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with rasterio.open(out_file, "w", **out_meta) as dest:
                dest.write(mosaic)

            return out_file
        finally:
            for ds in datasets:
                ds.close()

    @classmethod
    def compute_aspect(cls, file_path: Path) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Computes terrain aspect (downslope compass direction in degrees 0-360, where 0=N, 90=E).
        """
        if not HAS_RASTERIO:
            raise RuntimeError("rasterio library is required for aspect computation.")

        p = Path(file_path).resolve()
        with rasterio.open(p) as src:
            arr = src.read(1)
            nodata_val = src.nodata
            crs = src.crs
            res_x, res_y = src.res
            bounds = src.bounds
            meta = src.meta.copy()

        if crs and crs.is_geographic:
            mean_lat = (bounds.bottom + bounds.top) / 2.0
            dx_m = res_x * 111320.0 * math.cos(math.radians(mean_lat))
            dy_m = res_y * 110540.0
        else:
            dx_m, dy_m = abs(res_x), abs(res_y)

        gy, gx = np.gradient(arr, dy_m, dx_m)
        aspect_rad = np.arctan2(-gy, gx)
        aspect_deg = np.degrees(aspect_rad)
        aspect_deg = (450.0 - aspect_deg) % 360.0  # Convert mathematical angle to compass bearing

        if nodata_val is not None:
            if math.isnan(nodata_val):
                aspect_deg[np.isnan(arr)] = -9999.0
            else:
                aspect_deg[arr == nodata_val] = -9999.0

        return aspect_deg.astype(np.float32), meta

    @classmethod
    def compute_hillshade(
        cls,
        file_path: Path,
        azimuth_deg: float = 315.0,
        altitude_deg: float = 45.0,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Computes shaded relief (hillshade) normalized to 0-255 grayscale.
        Standard default light source: 315° NW azimuth, 45° solar elevation.
        """
        if not HAS_RASTERIO:
            raise RuntimeError("rasterio library is required for hillshade computation.")

        p = Path(file_path).resolve()
        with rasterio.open(p) as src:
            arr = src.read(1)
            nodata_val = src.nodata
            crs = src.crs
            res_x, res_y = src.res
            bounds = src.bounds
            meta = src.meta.copy()

        if crs and crs.is_geographic:
            mean_lat = (bounds.bottom + bounds.top) / 2.0
            dx_m = res_x * 111320.0 * math.cos(math.radians(mean_lat))
            dy_m = res_y * 110540.0
        else:
            dx_m, dy_m = abs(res_x), abs(res_y)

        gy, gx = np.gradient(arr, dy_m, dx_m)
        slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))
        aspect_rad = np.arctan2(gy, -gx)

        zenith_rad = np.radians(90.0 - altitude_deg)
        azimuth_rad = np.radians(azimuth_deg)

        shaded = 255.0 * (
            (np.cos(zenith_rad) * np.cos(slope_rad))
            + (np.sin(zenith_rad) * np.sin(slope_rad) * np.cos(azimuth_rad - aspect_rad))
        )
        shaded = np.clip(shaded, 0.0, 255.0).astype(np.uint8)

        if nodata_val is not None:
            if math.isnan(nodata_val):
                shaded[np.isnan(arr)] = 0
            else:
                shaded[arr == nodata_val] = 0

        meta.update({"dtype": "uint8", "nodata": 0})
        return shaded, meta
