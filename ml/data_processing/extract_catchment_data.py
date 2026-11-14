"""
ml/data_processing/extract_catchment_data.py

Extracts and normalizes catchment-specific hydrological and meteorological
time-series from raw official government downloads.

TARGET DOMAINS:
1. Hathnikund Barrage (HKB U/S and HKB D/S) daily discharge (2018–2025)
   Source: data/raw/hydrological/riverdischarge_manual_daily_irrigation-water-resources-department-haryana_hr_2001_2025.csv
2. Yamuna Catchment Districts daily rainfall (Yamunanagar, Karnal, Panipat, Sonipat, Delhi)
   Source: data/raw/rainfall/rainfall_districtwise_daily_imd.csv
"""

import os
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


def extract_hathnikund_discharge(
    raw_csv_path: Path,
    output_csv_path: Path
) -> Dict[str, Any]:
    """Extract Hathnikund upstream and downstream discharge records."""
    if not raw_csv_path.exists():
        raise FileNotFoundError(f"Raw file not found: {raw_csv_path}")

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    records = []
    with open(raw_csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            station = row.get("Station", "").strip()
            if station in ("HKB U/S", "HKB D/S"):
                raw_time = row.get("Data Acquisition Time", "").strip()
                # Parse format: DD-MM-YYYY HH:MM
                try:
                    dt = datetime.strptime(raw_time, "%d-%m-%Y %H:%M")
                    iso_time = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                    date_str = dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue

                q_str = row.get("Manual Daily River Water Discharge (m3/sec)", "").strip()
                try:
                    q_cumecs = float(q_str)
                    q_cusecs = round(q_cumecs / 0.0283168, 2)
                except ValueError:
                    q_cumecs = None
                    q_cusecs = None

                records.append({
                    "timestamp_utc": iso_time,
                    "date": date_str,
                    "station_name": station,
                    "role": "upstream_inflow" if station == "HKB U/S" else "downstream_release",
                    "latitude": row.get("Latitude", "").strip(),
                    "longitude": row.get("Longitude", "").strip(),
                    "discharge_cumecs": q_cumecs,
                    "discharge_cusecs": q_cusecs,
                    "agency": row.get("Agency", "").strip(),
                    "district": row.get("District", "").strip(),
                })

    # Sort chronologically
    records.sort(key=lambda r: (r["timestamp_utc"], r["station_name"]))

    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "timestamp_utc",
            "date",
            "station_name",
            "role",
            "latitude",
            "longitude",
            "discharge_cumecs",
            "discharge_cusecs",
            "agency",
            "district"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    return {
        "output_path": str(output_csv_path),
        "total_extracted_records": len(records),
        "start_date": records[0]["date"] if records else None,
        "end_date": records[-1]["date"] if records else None,
    }


def extract_yamuna_rainfall(
    raw_csv_path: Path,
    output_csv_path: Path
) -> Dict[str, Any]:
    """Extract IMD daily rainfall for upper-middle Yamuna corridor districts."""
    if not raw_csv_path.exists():
        raise FileNotFoundError(f"Raw file not found: {raw_csv_path}")

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    TARGET_DISTRICTS = {
        "YAMUNANAGAR",
        "KARNAL",
        "PANIPAT",
        "SONIPAT",
        "DELHI",
        "NORTH DELHI",
        "CENTRAL DELHI",
        "EAST DELHI",
    }

    records = []
    with open(raw_csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            district = row.get("District", "").strip().upper()
            state = row.get("State", "").strip().upper()
            
            # Match target corridor districts
            if district in TARGET_DISTRICTS or (state == "DELHI"):
                raw_date = row.get("Date", "").strip()
                try:
                    dt = datetime.strptime(raw_date, "%Y-%m-%d")
                    iso_date = dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue

                actual_str = row.get("Daily Actual", "").strip()
                normal_str = row.get("Daily Normal", "").strip()
                try:
                    actual_mm = float(actual_str)
                except ValueError:
                    actual_mm = None
                try:
                    normal_mm = float(normal_str)
                except ValueError:
                    normal_mm = None

                records.append({
                    "date": iso_date,
                    "state": state,
                    "district": district,
                    "rainfall_actual_mm": actual_mm,
                    "rainfall_normal_mm": normal_mm,
                    "category": row.get("Daily Category", "").strip(),
                })

    records.sort(key=lambda r: (r["date"], r["state"], r["district"]))

    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "date",
            "state",
            "district",
            "rainfall_actual_mm",
            "rainfall_normal_mm",
            "category"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    return {
        "output_path": str(output_csv_path),
        "total_extracted_records": len(records),
        "start_date": records[0]["date"] if records else None,
        "end_date": records[-1]["date"] if records else None,
    }


def main():
    root = Path(__file__).resolve().parents[2]
    
    # 1. Hathnikund extraction
    haryana_raw = root / "data" / "raw" / "hydrological" / "riverdischarge_manual_daily_irrigation-water-resources-department-haryana_hr_2001_2025.csv"
    hkb_processed = root / "data" / "processed" / "hydrological" / "haryana_hathnikund_discharge_daily_2018_2025.csv"
    if haryana_raw.exists():
        res_hkb = extract_hathnikund_discharge(haryana_raw, hkb_processed)
        print("Hathnikund extraction complete:", res_hkb)
    
    # 2. Rainfall extraction
    rainfall_raw = root / "data" / "raw" / "rainfall" / "rainfall_districtwise_daily_imd.csv"
    rainfall_processed = root / "data" / "processed" / "rainfall" / "imd_yamuna_catchment_daily_rainfall.csv"
    if rainfall_raw.exists():
        res_rain = extract_yamuna_rainfall(rainfall_raw, rainfall_processed)
        print("Yamuna catchment rainfall extraction complete:", res_rain)


if __name__ == "__main__":
    main()
