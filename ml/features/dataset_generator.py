"""
ml/features/dataset_generator.py

Deterministic Dataset Assembly Engine for PRAVAAH Phase 2A.
Generates the authoritative 24-hour ahead Hathnikund discharge forecasting dataset:
    data/processed/modelling/hathnikund_discharge_forecasting_24h.csv
and associated metadata:
    data/processed/modelling/forecasting_metadata.json

EXCLUSION AUDITING & INTEGRITY PRINCIPLES:
1. Strictly 24h Target: Pairs date D with D + 1 day. If D + 1 is missing, target is null;
   it is never paired with multi-day future gaps.
2. No Data Leakage: All predictors use only observations available at issue time t.
3. Deterministic: Outputs identical records across repeated runs.
4. Preserves Raw & Processed Observations: Writes only to data/processed/modelling/.
"""

import os
import csv
import json
import hashlib
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from ml.features.feature_pipeline import DischargeFeaturePipeline
from ml.features.feature_manifest import FEATURE_MANIFEST, get_feature_metadata_dict


def get_default_repo_root() -> Path:
    # ml/features/dataset_generator.py -> parents[2] is repo root
    return Path(__file__).resolve().parents[2]


class ForecastingDatasetGenerator:
    """Loads validated sources, computes features, and writes contract-compliant modelling files."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.root = repo_root or get_default_repo_root()
        self.discharge_csv = self.root / "data" / "processed" / "hydrological" / "haryana_hathnikund_discharge_daily_2018_2025.csv"
        self.rainfall_csv = self.root / "data" / "processed" / "rainfall" / "gridded" / "imd_gridded_daily_regional_summary_2018_2024.csv"
        self.output_dir = self.root / "data" / "processed" / "modelling"
        self.output_csv = self.output_dir / "hathnikund_discharge_forecasting_24h.csv"
        self.metadata_json = self.output_dir / "forecasting_metadata.json"
        self.pipeline = DischargeFeaturePipeline()

    @staticmethod
    def _compute_sha256(filepath: Path) -> str:
        """Calculate SHA256 checksum of an input file for provenance tracking."""
        if not filepath.exists():
            return "FILE_NOT_FOUND"
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def load_sources(self) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, Dict[str, Any]], Dict[str, Any]]:
        """Load and audit raw/processed input records."""
        if not self.discharge_csv.exists():
            raise FileNotFoundError(f"Discharge dataset missing at: {self.discharge_csv}")
        if not self.rainfall_csv.exists():
            raise FileNotFoundError(f"Rainfall dataset missing at: {self.rainfall_csv}")

        ds_records: Dict[str, float] = {}
        us_records: Dict[str, float] = {}
        duplicate_discharge_count = 0

        with open(self.discharge_csv, mode="r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                d = row["date"].strip()
                st = row["station_name"].strip()
                q = float(row["discharge_cumecs"])
                if st == "HKB D/S":
                    if d in ds_records:
                        duplicate_discharge_count += 1
                    ds_records[d] = q
                elif st == "HKB U/S":
                    us_records[d] = q

        rf_records: Dict[str, Dict[str, Any]] = {}
        duplicate_rf_count = 0

        with open(self.rainfall_csv, mode="r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                d = row["date"].strip()
                if d in rf_records:
                    duplicate_rf_count += 1
                rf_records[d] = {
                    "mean": float(row["rainfall_spatial_mean_mm"]),
                    "max": float(row["rainfall_spatial_max_mm"]),
                    "valid_cells": int(row["valid_cells_count"]),
                }

        audit = {
            "discharge_sha256": self._compute_sha256(self.discharge_csv),
            "rainfall_sha256": self._compute_sha256(self.rainfall_csv),
            "hkb_ds_total_records": len(ds_records),
            "hkb_us_total_records": len(us_records),
            "rainfall_total_records": len(rf_records),
            "duplicate_discharge_timestamps": duplicate_discharge_count,
            "duplicate_rainfall_timestamps": duplicate_rf_count,
        }

        return ds_records, us_records, rf_records, audit

    def generate(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Run the end-to-end dataset generation pipeline."""
        ds_records, us_records, rf_records, source_audit = self.load_sources()

        # Isolate the coupled analysis period: 2018-01-01 to 2024-12-31
        # (Both discharge and IMD gridded rainfall are verified across this 7-year range)
        modelling_dates = sorted([d for d in ds_records.keys() if "2018-01-01" <= d <= "2024-12-31"])

        feature_rows, pipeline_audit = self.pipeline.process_time_series(
            dates=modelling_dates,
            ds_records=ds_records,
            us_records=us_records,
            rf_records=rf_records,
        )

        # Partition breakdown
        partition_counts = {"TRAIN": 0, "VAL": 0, "TEST": 0}
        complete_by_partition = {"TRAIN": 0, "VAL": 0, "TEST": 0}

        for r in feature_rows:
            p = r["partition"]
            partition_counts[p] += 1
            if r["is_complete_operational_row"]:
                complete_by_partition[p] += 1

        generation_metadata = {
            "dataset_name": "Hathnikund Downstream Discharge 24h Forecasting Dataset",
            "version": "1.0.0",
            "milestone": "Phase 2A — Feature Engineering and Baseline Feasibility",
            "generation_timestamp_utc": datetime.utcnow().isoformat() + "Z",
            "source_provenance": source_audit,
            "modelling_period_start": modelling_dates[0],
            "modelling_period_end": modelling_dates[-1],
            "total_calendar_days_in_period": (date.fromisoformat(modelling_dates[-1]) - date.fromisoformat(modelling_dates[0])).days + 1,
            "total_observed_hkb_ds_days": len(modelling_dates),
            "missing_calendar_days_in_hkb_ds": ((date.fromisoformat(modelling_dates[-1]) - date.fromisoformat(modelling_dates[0])).days + 1) - len(modelling_dates),
            "total_generated_rows": len(feature_rows),
            "valid_24h_target_rows": pipeline_audit["valid_target_rows"],
            "broken_target_rows": pipeline_audit["broken_target_rows"],
            "complete_operational_rows": pipeline_audit["complete_operational_rows"],
            "incomplete_rows": pipeline_audit["incomplete_rows"],
            "partition_counts_all": partition_counts,
            "partition_counts_complete": complete_by_partition,
            "features_manifest": get_feature_metadata_dict(),
        }

        # Write CSV
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if feature_rows:
            fieldnames = list(feature_rows[0].keys())
            with open(self.output_csv, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(feature_rows)

        # Write Metadata JSON
        with open(self.metadata_json, mode="w", encoding="utf-8") as f:
            json.dump(generation_metadata, f, indent=2)

        return feature_rows, generation_metadata
