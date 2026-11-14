"""
ml/data_processing/import_target_gauge.py

Robust, Reusable Target-Data Importer and Validator for Downstream CWC Gauges.
Designed for official telemetry and register exports (e.g., Delhi Old Railway Bridge,
CWC Station 028-MDD).

CORE INTEGRITY INVARIANTS:
1. Validates required schema elements and rejects unparseable or malformed structures.
2. Parses timestamps consistently to ISO 8601 UTC strings.
3. Preserves original raw data without in-place modification.
4. Detects and reports duplicate observation timestamps.
5. Preserves missing observations as None (null) with is_missing=True.
   NEVER converts missing observations into zero or assumes no flood!
6. Validates physical units and plausible bounds (190.0m to 215.0m MSL for Delhi ORB)
   without silent unit transformations.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union


class SchemaValidationError(Exception):
    """Raised when an input target dataset fails fundamental schema verification."""
    pass


class TargetGaugeImporter:
    """Importer and validator for official downstream river gauge observation exports."""

    NULL_SENTINELS = {"", "na", "n/a", "nan", "null", "none", "-999", "-999.0", "-9999", "-9999.0"}

    # Candidate column names across CWC, India-WRIS, NWIC, and Delhi I&FC exports
    DEFAULT_TIMESTAMP_CANDIDATES = [
        "timestamp_utc",
        "timestamp",
        "date_time",
        "datetime",
        "data acquisition time",
        "data_acquisition_time",
        "observation_time",
        "reading_time",
        "date",
    ]

    DEFAULT_STAGE_CANDIDATES = [
        "water_level_m",
        "water_level",
        "river_water_level",
        "river water level",
        "stage_m",
        "gauge_level_m",
        "gauge_reading_m",
        "level_m",
        "river_stage_orb",
    ]

    DEFAULT_STATION_ID_CANDIDATES = [
        "station_id",
        "station_code",
        "site_id",
        "site_code",
        "cwc_station_id",
    ]

    DEFAULT_STATION_NAME_CANDIDATES = [
        "station_name",
        "station",
        "site_name",
        "location",
    ]

    DEFAULT_UNIT_CANDIDATES = [
        "unit",
        "units",
        "measurement_unit",
    ]

    def __init__(
        self,
        min_plausible_stage_m: float = 190.0,
        max_plausible_stage_m: float = 215.0,
        default_danger_level_m: float = 205.33,
        default_warning_level_m: float = 204.50,
        column_mapping: Optional[Dict[str, str]] = None,
    ):
        """
        Args:
            min_plausible_stage_m: Lower physical plausibility bound in metres MSL.
            max_plausible_stage_m: Upper physical plausibility bound in metres MSL.
            default_danger_level_m: Official danger mark if not present in row.
            default_warning_level_m: Official warning mark if not present in row.
            column_mapping: Explicit dict overriding column lookups (e.g. {'timestamp': 'time_col', 'stage': 'wl'}).
        """
        self.min_plausible_stage_m = min_plausible_stage_m
        self.max_plausible_stage_m = max_plausible_stage_m
        self.default_danger_level_m = default_danger_level_m
        self.default_warning_level_m = default_warning_level_m
        self.column_mapping = column_mapping or {}

    @classmethod
    def parse_timestamp_utc(cls, ts_str: Any) -> Optional[datetime]:
        """Convert varied date/time representations to timezone-aware UTC datetime."""
        if ts_str is None:
            return None
        clean = str(ts_str).strip()
        if not clean or clean.lower() in cls.NULL_SENTINELS:
            return None

        # Try ISO 8601
        try:
            dt = datetime.fromisoformat(clean.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            pass

        # Try common Indian government and telemetry datetime formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y %H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(clean, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        return None

    def _resolve_column(self, available_cols: List[str], target_key: str, candidates: List[str]) -> Optional[str]:
        """Resolve column header using explicit mapping or heuristic candidate list."""
        if target_key in self.column_mapping:
            explicit = self.column_mapping[target_key]
            if explicit in available_cols:
                return explicit
            raise SchemaValidationError(
                f"Configured column '{explicit}' for '{target_key}' not found in file columns: {available_cols}"
            )

        avail_lower_map = {c.strip().lower(): c for c in available_cols}
        for cand in candidates:
            if cand.lower() in avail_lower_map:
                return avail_lower_map[cand.lower()]
        return None

    def import_from_csv(
        self,
        file_path: Union[str, Path],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Import and validate downstream gauge observations from a CSV file.

        Returns:
            Tuple of (standardized_records, audit_summary).
        Raises:
            FileNotFoundError: If input file does not exist.
            SchemaValidationError: If required columns cannot be found or file is empty.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Target gauge file does not exist: {path}")

        records: List[Dict[str, Any]] = []
        raw_rows: List[Dict[str, str]] = []

        with open(path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise SchemaValidationError(f"Target file {path.name} contains no header or is empty.")
            fieldnames = list(reader.fieldnames)
            for row in reader:
                raw_rows.append(row)

        if not raw_rows:
            raise SchemaValidationError(f"Target file {path.name} contains zero data rows.")

        # Identify required and optional columns
        ts_col = self._resolve_column(fieldnames, "timestamp", self.DEFAULT_TIMESTAMP_CANDIDATES)
        if not ts_col:
            raise SchemaValidationError(
                f"Missing required timestamp column in {path.name}. "
                f"Available columns: {fieldnames}. Expected one of: {self.DEFAULT_TIMESTAMP_CANDIDATES}"
            )

        stage_col = self._resolve_column(fieldnames, "stage", self.DEFAULT_STAGE_CANDIDATES)
        if not stage_col:
            raise SchemaValidationError(
                f"Missing required stage/water level column in {path.name}. "
                f"Available columns: {fieldnames}. Expected one of: {self.DEFAULT_STAGE_CANDIDATES}"
            )

        st_id_col = self._resolve_column(fieldnames, "station_id", self.DEFAULT_STATION_ID_CANDIDATES)
        st_name_col = self._resolve_column(fieldnames, "station_name", self.DEFAULT_STATION_NAME_CANDIDATES)
        unit_col = self._resolve_column(fieldnames, "unit", self.DEFAULT_UNIT_CANDIDATES)

        # Audit counters
        seen_timestamps: Dict[str, int] = {}
        missing_stage_count = 0
        duplicate_count = 0
        out_of_bounds_count = 0
        unparseable_timestamp_count = 0
        danger_breaches = 0
        warning_breaches = 0
        valid_stages: List[float] = []

        warnings: List[str] = []
        errors: List[str] = []

        for row_idx, row in enumerate(raw_rows):
            raw_ts = row.get(ts_col, "")
            dt = self.parse_timestamp_utc(raw_ts)

            if dt is None:
                unparseable_timestamp_count += 1
                errors.append(f"Row {row_idx}: Unparseable timestamp value: '{raw_ts}'")
                continue

            iso_ts = dt.strftime("%Y-%m-%dT%H:%M:%SZ")

            # Duplicate detection
            if iso_ts in seen_timestamps:
                seen_timestamps[iso_ts] += 1
                duplicate_count += 1
                warnings.append(f"Duplicate timestamp encountered at row {row_idx}: '{iso_ts}'")
            else:
                seen_timestamps[iso_ts] = 1

            # Unit verification check
            if unit_col and row.get(unit_col):
                u_val = str(row.get(unit_col)).strip().lower()
                if u_val not in ("m", "meter", "metre", "meters", "metres", "m msl", "m_msl"):
                    warnings.append(
                        f"Row {row_idx}: Unexpected unit '{row.get(unit_col)}'. "
                        f"Expected metres (m MSL). Values not converted silently."
                    )

            # Stage value parsing & missing sentinel check
            raw_stage = row.get(stage_col, "")
            stage_f: Optional[float] = None
            is_missing: bool = False

            if raw_stage is None or str(raw_stage).strip().lower() in self.NULL_SENTINELS:
                is_missing = True
                missing_stage_count += 1
            else:
                try:
                    stage_f = float(str(raw_stage).strip())
                except ValueError:
                    is_missing = True
                    missing_stage_count += 1
                    errors.append(f"Row {row_idx}: Non-numeric stage value '{raw_stage}'")

            # Plausibility check
            if stage_f is not None:
                if stage_f < self.min_plausible_stage_m or stage_f > self.max_plausible_stage_m:
                    out_of_bounds_count += 1
                    warnings.append(
                        f"Row {row_idx}: Stage {stage_f}m MSL is outside plausible bounds "
                        f"[{self.min_plausible_stage_m}, {self.max_plausible_stage_m}]"
                    )
                valid_stages.append(stage_f)

                if stage_f >= self.default_danger_level_m:
                    danger_breaches += 1
                if stage_f >= self.default_warning_level_m:
                    warning_breaches += 1

            station_id = row.get(st_id_col, "028-MDD") if st_id_col else "028-MDD"
            station_name = row.get(st_name_col, "Delhi Old Railway Bridge") if st_name_col else "Delhi Old Railway Bridge"

            records.append({
                "timestamp_utc": iso_ts,
                "station_id": str(station_id).strip(),
                "station_name": str(station_name).strip(),
                "water_level_m": stage_f,
                "is_missing": is_missing,
                "danger_threshold_m": self.default_danger_level_m,
                "warning_threshold_m": self.default_warning_level_m,
                "is_danger_breached": (stage_f >= self.default_danger_level_m) if stage_f is not None else None,
                "raw_stage_string": raw_stage,
            })

        # Sort chronologically
        records.sort(key=lambda r: r["timestamp_utc"])

        summary = {
            "source_file": str(path),
            "total_raw_rows": len(raw_rows),
            "successfully_parsed_records": len(records),
            "valid_observed_stages": len(valid_stages),
            "missing_observations_count": missing_stage_count,
            "missingness_percentage": round((missing_stage_count / len(records) * 100), 2) if records else 0.0,
            "duplicate_timestamps_count": duplicate_count,
            "unparseable_timestamps_count": unparseable_timestamp_count,
            "out_of_bounds_count": out_of_bounds_count,
            "min_observed_stage_m": min(valid_stages) if valid_stages else None,
            "max_observed_stage_m": max(valid_stages) if valid_stages else None,
            "danger_breach_count": danger_breaches,
            "warning_breach_count": warning_breaches,
            "start_timestamp_utc": records[0]["timestamp_utc"] if records else None,
            "end_timestamp_utc": records[-1]["timestamp_utc"] if records else None,
            "errors": errors[:50],
            "warnings": warnings[:50],
            "is_usable_for_target_construction": (len(valid_stages) > 0 and unparseable_timestamp_count == 0),
        }

        return records, summary

    def export_standardized_csv(
        self,
        records: List[Dict[str, Any]],
        output_csv_path: Union[str, Path]
    ) -> Path:
        """Export standardized, validated records to processed CSV destination."""
        out_path = Path(output_csv_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if not records:
            raise ValueError("No records to export.")

        fieldnames = [
            "timestamp_utc",
            "station_id",
            "station_name",
            "water_level_m",
            "is_missing",
            "danger_threshold_m",
            "warning_threshold_m",
            "is_danger_breached",
            "raw_stage_string"
        ]

        with open(out_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

        return out_path
