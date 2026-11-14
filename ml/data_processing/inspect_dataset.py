"""
ml/data_processing/inspect_dataset.py

Reusable Data Inspection and Integrity Utility for PRAVAAH.
Supports automated structural, statistical, geospatial, and quality auditing
for local tabular (CSV), geospatial (GeoJSON), and extensible scientific files.

SAFETY & INTEGRITY RULES:
- Never silently modifies or overwrites raw data files.
- Does not assume hardcoded column names or specific units.
- Fully decoupled from machine-learning model training logic.
"""

import os
import sys
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


def format_bytes(size_bytes: int) -> str:
    """Format bytes into human-readable representation."""
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {units[i]}"


def try_parse_number(val: str) -> Optional[Union[int, float]]:
    """Attempt parsing string as int or float."""
    v = val.strip()
    if not v:
        return None
    try:
        if "." in v or "e" in v.lower():
            f = float(v)
            return f
        return int(v)
    except ValueError:
        return None


def try_parse_date(val: str) -> Optional[datetime]:
    """Attempt parsing string as common ISO/hydrological date formats."""
    v = val.strip()
    if not v:
        return None
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            pass
    return None


class DatasetInspector:
    """Inspects local dataset files and produces a comprehensive audit report."""

    COMMON_NULL_SENTINELS = {
        "",
        "na",
        "n/a",
        "nan",
        "null",
        "none",
        "-999",
        "-999.0",
        "-9999",
        "-9999.0",
    }

    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path).resolve()
        if not self.file_path.exists():
            raise FileNotFoundError(f"Target file does not exist: {self.file_path}")
        self.file_size = self.file_path.stat().st_size
        self.extension = self.file_path.suffix.lower()

    def inspect(self) -> Dict[str, Any]:
        """Execute comprehensive inspection based on file extension."""
        report: Dict[str, Any] = {
            "file_path": str(self.file_path),
            "file_name": self.file_path.name,
            "file_format": self.extension.lstrip("."),
            "file_size_bytes": self.file_size,
            "file_size_human": format_bytes(self.file_size),
            "inspection_timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "warnings": [],
            "errors": [],
        }

        if self.file_size == 0:
            report["status"] = "warning"
            report["warnings"].append("File is empty (0 bytes).")
            return report

        if self.extension == ".csv":
            self._inspect_csv(report)
        elif self.extension in (".geojson", ".json"):
            self._inspect_geojson(report)
        else:
            report["status"] = "partial"
            report["warnings"].append(
                f"File format '{self.extension}' is not natively parsed by the lightweight inspector. "
                "For raster (GeoTIFF) or NetCDF (.nc), specialized libraries (rasterio, xarray) are required."
            )

        return report

    def _inspect_csv(self, report: Dict[str, Any]) -> None:
        """Inspect tabular CSV files without modifying contents."""
        try:
            with open(self.file_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
                # Sample dialect
                sample = f.read(8192)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                    delimiter = dialect.delimiter
                except Exception:
                    delimiter = ","

                reader = csv.reader(f, delimiter=delimiter)
                try:
                    header = next(reader)
                except StopIteration:
                    report["warnings"].append("CSV contains no rows.")
                    return

                column_names = [col.strip() for col in header]
                report["columns"] = column_names
                report["num_columns"] = len(column_names)

                rows: List[List[str]] = []
                row_hashes = set()
                duplicate_count = 0

                for row_idx, row in enumerate(reader, start=2):
                    if not row or (len(row) == 1 and not row[0].strip()):
                        continue  # skip blank lines

                    if len(row) != len(column_names):
                        report["warnings"].append(
                            f"Row {row_idx} length mismatch: expected {len(column_names)} columns, found {len(row)}."
                        )

                    row_tuple = tuple(row)
                    if row_tuple in row_hashes:
                        duplicate_count += 1
                    else:
                        row_hashes.add(row_tuple)

                    rows.append(row)

                report["num_rows"] = len(rows)
                report["duplicate_row_count"] = duplicate_count

                # Column-wise statistical and type analysis
                col_analysis: Dict[str, Any] = {}
                for idx, col_name in enumerate(column_names):
                    col_values = [row[idx] if idx < len(row) else "" for row in rows]
                    col_analysis[col_name] = self._analyze_column(col_name, col_values, report)

                report["column_summary"] = col_analysis

        except Exception as e:
            report["status"] = "error"
            report["errors"].append(f"Failed to parse CSV: {str(e)}")

    def _analyze_column(
        self, col_name: str, values: List[str], report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze missing values, types, numeric distributions, and dates for a column."""
        total = len(values)
        if total == 0:
            return {"total_values": 0, "null_count": 0, "inferred_type": "empty"}

        null_count = 0
        numeric_vals: List[Union[int, float]] = []
        parsed_dates = 0
        date_candidates = 0

        is_potential_date_col = any(
            hint in col_name.lower() for hint in ["date", "time", "timestamp", "year", "day"]
        )

        for v in values:
            cleaned = v.strip()
            if cleaned.lower() in self.COMMON_NULL_SENTINELS:
                null_count += 1
                continue

            num = try_parse_number(cleaned)
            if num is not None:
                numeric_vals.append(num)

            if is_potential_date_col or "-" in cleaned or "/" in cleaned:
                date_candidates += 1
                dt = try_parse_date(cleaned)
                if dt is not None:
                    parsed_dates += 1

        null_percentage = round((null_count / total) * 100, 2)
        summary: Dict[str, Any] = {
            "total_values": total,
            "null_count": null_count,
            "null_percentage": null_percentage,
        }

        # Type inference
        valid_count = total - null_count
        if valid_count == 0:
            summary["inferred_type"] = "all_null"
        elif len(numeric_vals) == valid_count:
            summary["inferred_type"] = "numeric"
            summary["min"] = min(numeric_vals)
            summary["max"] = max(numeric_vals)
            sorted_nums = sorted(numeric_vals)
            summary["median"] = sorted_nums[len(sorted_nums) // 2]
            summary["mean"] = round(sum(numeric_vals) / len(numeric_vals), 4)

            # Heuristic checks for domain anomalies
            col_lower = col_name.lower()
            if "rain" in col_lower or "precip" in col_lower:
                if summary["min"] < 0:
                    report["warnings"].append(
                        f"Column '{col_name}' has negative values (min: {summary['min']}). Rainfall cannot be negative."
                    )
            if "discharge" in col_lower:
                if summary["min"] < 0:
                    report["warnings"].append(
                        f"Column '{col_name}' has negative values (min: {summary['min']}). Discharge cannot be negative."
                    )
            if "stage" in col_lower or "water_level" in col_lower:
                if summary["min"] < 0:
                    report["warnings"].append(
                        f"Column '{col_name}' has negative values (min: {summary['min']}). Elevation above MSL must be positive."
                    )
        elif parsed_dates > 0 and parsed_dates >= (valid_count * 0.8):
            summary["inferred_type"] = "datetime"
            summary["parsed_dates_count"] = parsed_dates
            if parsed_dates < valid_count:
                invalid_dates = valid_count - parsed_dates
                summary["unparseable_date_count"] = invalid_dates
                report["warnings"].append(
                    f"Column '{col_name}' has {invalid_dates} unparseable date values."
                )
        else:
            summary["inferred_type"] = "string"
            distinct_vals = set(v.strip() for v in values if v.strip())
            summary["distinct_count"] = len(distinct_vals)

        return summary

    def _inspect_geojson(self, report: Dict[str, Any]) -> None:
        """Inspect GeoJSON spatial structure, geometry types, and coordinate bounds."""
        try:
            with open(self.file_path, mode="r", encoding="utf-8") as f:
                data = json.load(f)

            geojson_type = data.get("type", "Unknown")
            report["geojson_type"] = geojson_type

            # CRS extraction
            crs = data.get("crs", {}).get("properties", {}).get("name", "EPSG:4326 (Default RFC 7946)")
            report["crs"] = crs

            features = data.get("features", []) if geojson_type == "FeatureCollection" else [data]
            report["num_features"] = len(features)

            geom_types = {}
            min_x, min_y, max_x, max_y = float("inf"), float("inf"), float("-inf"), float("-inf")

            def update_bounds(coords):
                nonlocal min_x, min_y, max_x, max_y
                if isinstance(coords, (list, tuple)):
                    if len(coords) >= 2 and isinstance(coords[0], (int, float)) and isinstance(coords[1], (int, float)):
                        x, y = coords[0], coords[1]
                        min_x = min(min_x, x)
                        min_y = min(min_y, y)
                        max_x = max(max_x, x)
                        max_y = max(max_y, y)
                    else:
                        for c in coords:
                            update_bounds(c)

            for feat in features:
                geom = feat.get("geometry")
                if geom:
                    gtype = geom.get("type", "Unknown")
                    geom_types[gtype] = geom_types.get(gtype, 0) + 1
                    update_bounds(geom.get("coordinates", []))

            report["geometry_type_counts"] = geom_types
            if min_x != float("inf"):
                report["bbox"] = {
                    "min_lon_or_x": min_x,
                    "min_lat_or_y": min_y,
                    "max_lon_or_x": max_x,
                    "max_lat_or_y": max_y,
                }

        except Exception as e:
            report["status"] = "error"
            report["errors"].append(f"Failed to parse GeoJSON: {str(e)}")


def inspect_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Convenience function to inspect a dataset file and return results."""
    inspector = DatasetInspector(file_path)
    return inspector.inspect()


def main():
    if len(sys.argv) < 2:
        print("Usage: python ml/data_processing/inspect_dataset.py <path_to_data_file>")
        sys.exit(1)

    target_path = sys.argv[1]
    inspector = DatasetInspector(target_path)
    report = inspector.inspect()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
