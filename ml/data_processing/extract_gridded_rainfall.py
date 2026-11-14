"""
ml/data_processing/extract_gridded_rainfall.py

Extracts and summarizes IMD 0.25-degree gridded daily rainfall records for the
provisional Upper-to-Middle Yamuna bounding box (28.0N - 31.0N, 76.5E - 78.0E).

GEOSPATIAL SPECIFICATION & LIMITATIONS:
1. IMD 0.25-degree grid layout:
   - Latitude: 6.5N to 38.5N (129 points, spacing 0.25 deg, indexed south-to-north)
   - Longitude: 66.5E to 100.0E (135 points, spacing 0.25 deg, indexed west-to-east)
   - Daily slice: 129 * 135 = 17,415 32-bit single-precision floats (69,660 bytes/day)
   - Missing-value sentinel: -999.0 (oceanic or external non-reporting pixels)
2. Provisional Bounding Box:
   - Latitude: 28.0N (index 86) to 31.0N (index 98) -> 13 latitude steps
   - Longitude: 76.5E (index 40) to 78.0E (index 46) -> 7 longitude steps
   - Total grid cells: 13 * 7 = 91 cells covering ~27.5 km x 27.5 km each
3. Scientific & Hydrological Caveats:
   - This rectangular bounding box is a PROVISIONAL GEOMETRIC APPROXIMATION.
   - It DOES NOT represent a verified hydrological watershed boundary or DEM-delineated catchment polygon.
   - The regional mean is calculated as an unweighted spatial arithmetic mean over valid land pixels
     within the bounding box. It must not be cited as a true hypsometric watershed-average rainfall.
   - Missing values (-999.0) are preserved as None/null and are NEVER silently replaced with 0.0.
"""

import os
import csv
import struct
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union


class IMDGriddedRainfallExtractor:
    """Extractor for official IMD Pune 0.25-degree daily binary gridded rainfall files."""

    # IMD National Grid Constants
    NLAT = 129
    NLON = 135
    LAT_ORIGIN = 6.5
    LON_ORIGIN = 66.5
    GRID_STEP = 0.25
    MISSING_SENTINEL = -999.0
    FLOATS_PER_DAY = NLAT * NLON
    BYTES_PER_DAY = FLOATS_PER_DAY * 4

    def __init__(
        self,
        min_lat: float = 28.0,
        max_lat: float = 31.0,
        min_lon: float = 76.5,
        max_lon: float = 78.0,
    ):
        """
        Args:
            min_lat: Lower latitude bound (degrees N).
            max_lat: Upper latitude bound (degrees N).
            min_lon: Western longitude bound (degrees E).
            max_lon: Eastern longitude bound (degrees E).
        """
        self.min_lat = min_lat
        self.max_lat = max_lat
        self.min_lon = min_lon
        self.max_lon = max_lon

        # Compute integer index bounds
        self.lat_start_idx = round((self.min_lat - self.LAT_ORIGIN) / self.GRID_STEP)
        self.lat_end_idx = round((self.max_lat - self.LAT_ORIGIN) / self.GRID_STEP)
        self.lon_start_idx = round((self.min_lon - self.LON_ORIGIN) / self.GRID_STEP)
        self.lon_end_idx = round((self.max_lon - self.LON_ORIGIN) / self.GRID_STEP)

        # Precompute cell coordinates
        self.cell_metadata: List[Dict[str, Any]] = []
        for lat_i in range(self.lat_start_idx, self.lat_end_idx + 1):
            lat_val = round(self.LAT_ORIGIN + lat_i * self.GRID_STEP, 4)
            for lon_j in range(self.lon_start_idx, self.lon_end_idx + 1):
                lon_val = round(self.LON_ORIGIN + lon_j * self.GRID_STEP, 4)
                self.cell_metadata.append({
                    "lat_idx": lat_i,
                    "lon_idx": lon_j,
                    "latitude": lat_val,
                    "longitude": lon_val,
                    "cell_id": f"GRID_{lat_val:.2f}N_{lon_val:.2f}E",
                })

        self.total_bbox_cells = len(self.cell_metadata)

    @staticmethod
    def is_leap_year(year: int) -> bool:
        """Determine whether calendar year is a leap year."""
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    def extract_year(
        self,
        grd_file_path: Union[str, Path],
        year: int
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extract daily cell values and regional summaries for a single calendar year.

        Returns:
            Tuple of (cell_level_records, daily_summary_records).
        """
        path = Path(grd_file_path)
        if not path.exists():
            raise FileNotFoundError(f"IMD gridded file not found: {path}")

        expected_days = 366 if self.is_leap_year(year) else 365
        expected_bytes = expected_days * self.BYTES_PER_DAY
        actual_bytes = path.stat().st_size

        if actual_bytes != expected_bytes:
            raise ValueError(
                f"File size mismatch for {path.name}: expected {expected_bytes} bytes "
                f"for {expected_days} days, found {actual_bytes} bytes."
            )

        with open(path, "rb") as f:
            raw_bytes = f.read()

        start_date = date(year, 1, 1)
        cell_records: List[Dict[str, Any]] = []
        summary_records: List[Dict[str, Any]] = []

        for day_offset in range(expected_days):
            current_date = start_date + timedelta(days=day_offset)
            date_str = current_date.isoformat()

            byte_offset = day_offset * self.BYTES_PER_DAY
            day_floats = struct.unpack(
                f"<{self.FLOATS_PER_DAY}f",
                raw_bytes[byte_offset : byte_offset + self.BYTES_PER_DAY]
            )

            valid_precip_values: List[float] = []
            missing_cells_for_day = 0

            for cell in self.cell_metadata:
                idx = cell["lat_idx"] * self.NLON + cell["lon_idx"]
                raw_val = day_floats[idx]

                if raw_val <= self.MISSING_SENTINEL or raw_val < 0.0:
                    val_clean: Optional[float] = None
                    is_missing = True
                    missing_cells_for_day += 1
                else:
                    val_clean = round(raw_val, 2)
                    is_missing = False
                    valid_precip_values.append(val_clean)

                cell_records.append({
                    "date": date_str,
                    "year": year,
                    "day_of_year": day_offset + 1,
                    "cell_id": cell["cell_id"],
                    "latitude": cell["latitude"],
                    "longitude": cell["longitude"],
                    "grid_lat_idx": cell["lat_idx"],
                    "grid_lon_idx": cell["lon_idx"],
                    "rainfall_actual_mm": val_clean,
                    "is_missing": is_missing,
                    "unit": "mm/day",
                    "spatial_domain": "upper_yamuna_provisional_bbox",
                })

            valid_count = len(valid_precip_values)
            if valid_count > 0:
                mean_precip = round(sum(valid_precip_values) / valid_count, 2)
                max_precip = max(valid_precip_values)
                min_precip = min(valid_precip_values)
            else:
                mean_precip = None
                max_precip = None
                min_precip = None

            summary_records.append({
                "date": date_str,
                "year": year,
                "day_of_year": day_offset + 1,
                "total_bbox_cells": self.total_bbox_cells,
                "valid_cells_count": valid_count,
                "missing_cells_count": missing_cells_for_day,
                "rainfall_spatial_mean_mm": mean_precip,
                "rainfall_spatial_max_mm": max_precip,
                "rainfall_spatial_min_mm": min_precip,
                "unit": "mm/day",
                "spatial_aggregation_method": "unweighted_provisional_bbox_mean",
                "bounding_box_wgs84": f"[{self.min_lat}N, {self.max_lat}N, {self.min_lon}E, {self.max_lon}E]",
            })

        return cell_records, summary_records

    def extract_and_export_all(
        self,
        raw_gridded_dir: Union[str, Path],
        output_processed_dir: Union[str, Path],
        years: List[int],
    ) -> Dict[str, Any]:
        """Process all available historical yearly files and export merged CSVs."""
        raw_dir = Path(raw_gridded_dir)
        out_dir = Path(output_processed_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        all_cell_records: List[Dict[str, Any]] = []
        all_summary_records: List[Dict[str, Any]] = []
        processed_years: List[int] = []
        missing_years: List[int] = []

        for y in sorted(years):
            filename = f"ind{y}_rfp25.grd"
            file_path = raw_dir / filename
            if not file_path.exists():
                missing_years.append(y)
                continue

            cells, summaries = self.extract_year(file_path, y)
            all_cell_records.extend(cells)
            all_summary_records.extend(summaries)
            processed_years.append(y)

        if not all_summary_records:
            raise ValueError(f"No gridded files found for specified years: {years} in {raw_dir}")

        # Export regional daily summary CSV
        summary_csv_path = out_dir / "imd_gridded_daily_regional_summary_2018_2024.csv"
        with open(summary_csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_summary_records[0].keys()))
            writer.writeheader()
            writer.writerows(all_summary_records)

        # Export cell-level CSV
        cells_csv_path = out_dir / "imd_gridded_daily_cell_rainfall_2018_2024.csv"
        with open(cells_csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_cell_records[0].keys()))
            writer.writeheader()
            writer.writerows(all_cell_records)

        # Compute audit metrics
        valid_days = [r for r in all_summary_records if r["rainfall_spatial_mean_mm"] is not None]
        max_day = max(valid_days, key=lambda r: r["rainfall_spatial_mean_mm"]) if valid_days else None
        max_cell_record = max(
            [c for c in all_cell_records if c["rainfall_actual_mm"] is not None],
            key=lambda c: c["rainfall_actual_mm"],
            default=None
        )

        audit_report = {
            "processed_years": processed_years,
            "missing_years": missing_years,
            "total_days_extracted": len(all_summary_records),
            "total_cell_observations": len(all_cell_records),
            "bounding_box_cells_count": self.total_bbox_cells,
            "summary_csv_path": str(summary_csv_path),
            "cells_csv_path": str(cells_csv_path),
            "start_date": all_summary_records[0]["date"],
            "end_date": all_summary_records[-1]["date"],
            "peak_regional_mean_mm": max_day["rainfall_spatial_mean_mm"] if max_day else None,
            "peak_regional_date": max_day["date"] if max_day else None,
            "peak_single_cell_mm": max_cell_record["rainfall_actual_mm"] if max_cell_record else None,
            "peak_single_cell_coords": (max_cell_record["latitude"], max_cell_record["longitude"]) if max_cell_record else None,
            "peak_single_cell_date": max_cell_record["date"] if max_cell_record else None,
        }

        return audit_report


def main():
    root = Path(__file__).resolve().parents[2]
    raw_dir = root / "data" / "raw" / "rainfall" / "gridded"
    out_dir = root / "data" / "processed" / "rainfall" / "gridded"

    extractor = IMDGriddedRainfallExtractor()
    years = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
    report = extractor.extract_and_export_all(raw_dir, out_dir, years)

    print("=== IMD 0.25 Gridded Rainfall Extraction Report ===")
    for k, v in report.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
