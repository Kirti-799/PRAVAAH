"""
ml/data_processing/historical_events.py

Reproducible Non-ML Historical Hydrological Event and Association Analysis for PRAVAAH.
Identifies distinct multi-day high-discharge episodes from Hathnikund Barrage observations,
calculates multi-window antecedent precipitation accumulations, and computes
empirical associations across seasonal hydroclimatic regimes.

CRITICAL DISTINCTIONS PRESERVED:
- Observed Discharge Event: Statistically/operationally defined high-flow threshold exceedance
  at Hathnikund Barrage (e.g. Q >= 1,500 cumecs / ~53,000 cusecs).
- Documented Historical Flood Event: Multi-agency disaster management records (CWC/DDMA)
  documenting severe overbanking and inundation in Delhi (e.g. Aug 2019, Sep 2022, Jul 2023).
- Confirmed Downstream Threshold-Breach Event: Continuous gauge readings at Delhi ORB
  exceeding 205.33 m MSL. (Currently blocked pending continuous CWC target stage register).
"""

import os
import csv
import json
import math
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union


class HistoricalHydrologyAnalyzer:
    """Performs empirical event extraction and rainfall-discharge association analysis."""

    def __init__(
        self,
        discharge_threshold_cumecs: float = 1500.0,
        event_gap_tolerance_days: int = 2,
    ):
        """
        Args:
            discharge_threshold_cumecs: Threshold defining high discharge at Hathnikund (~53,000 cusecs).
            event_gap_tolerance_days: Exceedances separated by <= tolerance days are merged into 1 episode.
        """
        self.discharge_threshold = discharge_threshold_cumecs
        self.gap_tolerance = event_gap_tolerance_days

    @staticmethod
    def _pearson_and_spearman(x: List[float], y: List[float]) -> Tuple[Optional[float], Optional[float]]:
        n = len(x)
        if n < 3:
            return None, None
        mx = sum(x) / n
        my = sum(y) / n
        cov = sum((x[i] - mx) * (y[i] - my) for i in range(n))
        var_x = sum((x[i] - mx) ** 2 for i in range(n))
        var_y = sum((y[i] - my) ** 2 for i in range(n))
        if var_x == 0 or var_y == 0:
            return None, None
        r = cov / math.sqrt(var_x * var_y)

        # Spearman rank correlation
        sorted_x = sorted((val, idx) for idx, val in enumerate(x))
        sorted_y = sorted((val, idx) for idx, val in enumerate(y))
        rx = [0.0] * n
        ry = [0.0] * n
        for rank, (val, idx) in enumerate(sorted_x):
            rx[idx] = rank + 1
        for rank, (val, idx) in enumerate(sorted_y):
            ry[idx] = rank + 1

        m_rx = (n + 1) / 2
        m_ry = (n + 1) / 2
        cov_r = sum((rx[i] - m_rx) * (ry[i] - m_ry) for i in range(n))
        var_r = sum((rx[i] - m_rx) ** 2 for i in range(n))
        rho = cov_r / var_r if var_r > 0 else 0.0

        return round(r, 4), round(rho, 4)

    def extract_episodes(
        self,
        daily_q_us: Dict[str, float],
        daily_q_ds: Dict[str, float],
        daily_rf: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Identify distinct multi-day high flow episodes from real time-series."""
        # Find all dates exceeding threshold in either upstream inflow or downstream release
        all_dates = sorted(set(daily_q_ds.keys()))
        exceedance_dates: List[date] = []
        for d_str in all_dates:
            q_us = daily_q_us.get(d_str, 0.0)
            q_ds = daily_q_ds.get(d_str, 0.0)
            if max(q_us, q_ds) >= self.discharge_threshold:
                exceedance_dates.append(date.fromisoformat(d_str))

        if not exceedance_dates:
            return []

        # Cluster dates within gap_tolerance days
        clusters: List[List[date]] = [[exceedance_dates[0]]]
        for cur_d in exceedance_dates[1:]:
            prev_d = clusters[-1][-1]
            if (cur_d - prev_d).days <= (self.gap_tolerance + 1):
                clusters[-1].append(cur_d)
            else:
                clusters.append([cur_d])

        episodes: List[Dict[str, Any]] = []
        for ep_idx, cluster in enumerate(clusters, start=1):
            start_d = cluster[0]
            end_d = cluster[-1]
            dur = (end_d - start_d).days + 1

            # Find peak day in cluster
            peak_d = start_d
            max_flow = -1.0
            for d in cluster:
                d_str = d.isoformat()
                flow = max(daily_q_us.get(d_str, 0.0), daily_q_ds.get(d_str, 0.0))
                if flow > max_flow:
                    max_flow = flow
                    peak_d = d

            peak_d_str = peak_d.isoformat()
            peak_us = daily_q_us.get(peak_d_str, 0.0)
            peak_ds = daily_q_ds.get(peak_d_str, 0.0)

            # Compute antecedent rainfall accumulation ending at D-1 (strictly prior to peak reading)
            def get_accum(days_back: int) -> Optional[float]:
                acc = 0.0
                for k in range(1, days_back + 1):
                    past_d_str = (peak_d - timedelta(days=k)).isoformat()
                    if past_d_str not in daily_rf or daily_rf[past_d_str]["mean"] is None:
                        return None
                    acc += daily_rf[past_d_str]["mean"]
                return round(acc, 2)

            rf_1d = get_accum(1)
            rf_3d = get_accum(3)
            rf_5d = get_accum(5)
            rf_7d = get_accum(7)

            peak_rf_info = daily_rf.get((peak_d - timedelta(days=1)).isoformat(), {})
            valid_cells = peak_rf_info.get("valid_cells", None)

            # Documented historical flood flags
            year = start_d.year
            is_documented_flood = False
            notes = "Observed high discharge at Hathnikund Barrage."
            if year == 2019 and start_d.month == 8:
                is_documented_flood = True
                notes = "Major August 2019 Yamuna flood: Hathnikund reached 17,623 cumecs (6.22 lakh cusecs), Delhi ORB crested at 206.60 m MSL."
            elif year == 2022 and start_d.month == 9:
                is_documented_flood = True
                notes = "Late-monsoon September 2022 flood: Hathnikund reached 8,380 cumecs (2.96 lakh cusecs), Delhi ORB crested at 205.99 m MSL."
            elif year == 2023 and start_d.month == 7 and start_d.day <= 20:
                is_documented_flood = True
                notes = "Historic July 2023 Delhi flood catastrophe: Hathnikund sustained >7,000 cumecs for days, Delhi ORB breached all-time HFL at 208.66 m MSL on July 13."

            # Chronological evaluation partition suitability
            if year <= 2021:
                partition = "Training Partition (2018–2021)"
            elif year == 2022:
                partition = "Validation Partition (2022)"
            else:
                partition = "Held-Out Test Partition (2023–2024)"

            episodes.append({
                "episode_id": f"EPISODE_{year}_{ep_idx:02d}",
                "start_date": start_d.isoformat(),
                "end_date": end_d.isoformat(),
                "duration_days": dur,
                "peak_date": peak_d_str,
                "peak_upstream_inflow_cumecs": round(peak_us, 2),
                "peak_downstream_release_cumecs": round(peak_ds, 2),
                "peak_upstream_inflow_cusecs": round(peak_us / 0.0283168, 1),
                "peak_downstream_release_cusecs": round(peak_ds / 0.0283168, 1),
                "rainfall_accum_1d_mm": rf_1d,
                "rainfall_accum_3d_mm": rf_3d,
                "rainfall_accum_5d_mm": rf_5d,
                "rainfall_accum_7d_mm": rf_7d,
                "valid_rainfall_cells_at_d_minus_1": valid_cells,
                "missing_rainfall_flag": any(x is None for x in (rf_1d, rf_3d, rf_5d, rf_7d)),
                "is_documented_historical_flood": is_documented_flood,
                "historical_context": notes,
                "proposed_ml_partition": partition,
            })

        return episodes

    def compute_associations(
        self,
        daily_q_us: Dict[str, float],
        daily_q_ds: Dict[str, float],
        daily_rf: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Compute statistical correlations between multi-window antecedent rainfall and discharge."""
        overlapping_dates = sorted([d for d in daily_rf.keys() if d in daily_q_ds and d in daily_q_us])

        regimes = [
            ("all_days", "All Days (2018–2024)", lambda d: True),
            ("monsoon", "Monsoon Season (June–September)", lambda d: int(d[5:7]) in (6, 7, 8, 9)),
            ("non_monsoon", "Non-Monsoon Season (October–May)", lambda d: int(d[5:7]) not in (6, 7, 8, 9)),
        ]

        windows = [
            ("1d", "Antecedent 1-Day (D-1)", [1]),
            ("3d", "Antecedent 3-Day (D-1 to D-3)", [1, 2, 3]),
            ("5d", "Antecedent 5-Day (D-1 to D-5)", [1, 2, 3, 4, 5]),
            ("7d", "Antecedent 7-Day (D-1 to D-7)", [1, 2, 3, 4, 5, 6, 7]),
        ]

        results: Dict[str, Any] = {
            "total_overlapping_days": len(overlapping_dates),
            "start_date": overlapping_dates[0] if overlapping_dates else None,
            "end_date": overlapping_dates[-1] if overlapping_dates else None,
            "regimes": {},
        }

        for regime_key, regime_title, date_fn in regimes:
            sub_dates = [d for d in overlapping_dates if date_fn(d)]
            regime_dict: Dict[str, Any] = {
                "title": regime_title,
                "sample_size": len(sub_dates),
                "windows": {},
            }

            for win_key, win_title, days_back in windows:
                pairs_us: List[Tuple[float, float]] = []
                pairs_ds: List[Tuple[float, float]] = []

                for d in sub_dates:
                    dt = date.fromisoformat(d)
                    prev_dates = [(dt - timedelta(days=k)).isoformat() for k in days_back]
                    if all(pd in daily_rf and daily_rf[pd]["mean"] is not None for pd in prev_dates):
                        rf_sum = sum(daily_rf[pd]["mean"] for pd in prev_dates)
                        pairs_us.append((rf_sum, daily_q_us[d]))
                        pairs_ds.append((rf_sum, daily_q_ds[d]))

                x_us = [p[0] for p in pairs_us]
                y_us = [p[1] for p in pairs_us]
                x_ds = [p[0] for p in pairs_ds]
                y_ds = [p[1] for p in pairs_ds]

                r_us, rho_us = self._pearson_and_spearman(x_us, y_us)
                r_ds, rho_ds = self._pearson_and_spearman(x_ds, y_ds)

                regime_dict["windows"][win_key] = {
                    "window_label": win_title,
                    "pairs_count": len(pairs_us),
                    "mean_rainfall_mm": round(sum(x_us) / len(x_us), 2) if x_us else None,
                    "inflow_hkb_us": {
                        "pearson_r": r_us,
                        "spearman_rho": rho_us,
                    },
                    "release_hkb_ds": {
                        "pearson_r": r_ds,
                        "spearman_rho": rho_ds,
                    },
                }

            results["regimes"][regime_key] = regime_dict

        return results

    def run_analysis_and_export(
        self,
        discharge_csv_path: Union[str, Path],
        rainfall_summary_csv_path: Union[str, Path],
        output_dir: Union[str, Path],
    ) -> Dict[str, Any]:
        """Run full event extraction and association suite and save reproducible artifacts."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        daily_q_us: Dict[str, float] = {}
        daily_q_ds: Dict[str, float] = {}
        with open(discharge_csv_path, mode="r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                d = row.get("date", "").strip()
                st = row.get("station_name", "").strip()
                q_val = row.get("discharge_cumecs")
                if d and q_val is not None and q_val != "":
                    try:
                        q_f = float(q_val)
                        if st == "HKB U/S":
                            daily_q_us[d] = q_f
                        elif st == "HKB D/S":
                            daily_q_ds[d] = q_f
                    except ValueError:
                        pass

        daily_rf: Dict[str, Dict[str, Any]] = {}
        with open(rainfall_summary_csv_path, mode="r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                d = row.get("date", "").strip()
                mean_rf = row.get("rainfall_spatial_mean_mm")
                max_rf = row.get("rainfall_spatial_max_mm")
                cells = row.get("valid_cells_count")
                if d:
                    daily_rf[d] = {
                        "mean": float(mean_rf) if mean_rf not in (None, "", "None") else None,
                        "max": float(max_rf) if max_rf not in (None, "", "None") else None,
                        "valid_cells": int(cells) if cells not in (None, "", "None") else 0,
                    }

        episodes = self.extract_episodes(daily_q_us, daily_q_ds, daily_rf)
        associations = self.compute_associations(daily_q_us, daily_q_ds, daily_rf)

        # Export episodes CSV
        episodes_csv_path = out_dir / "historical_high_discharge_episodes.csv"
        if episodes:
            fieldnames = list(episodes[0].keys())
            with open(episodes_csv_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(episodes)

        # Export associations JSON
        associations_json_path = out_dir / "rainfall_discharge_association_summary.json"
        with open(associations_json_path, mode="w", encoding="utf-8") as f:
            json.dump(associations, f, indent=2)

        return {
            "total_episodes_extracted": len(episodes),
            "episodes_csv_path": str(episodes_csv_path),
            "associations_json_path": str(associations_json_path),
            "documented_major_floods_captured": sum(1 for e in episodes if e["is_documented_historical_flood"]),
            "episodes": episodes,
            "associations": associations,
        }


def main():
    root = Path(__file__).resolve().parents[2]
    discharge_path = root / "data" / "processed" / "hydrological" / "haryana_hathnikund_discharge_daily_2018_2025.csv"
    rainfall_path = root / "data" / "processed" / "rainfall" / "gridded" / "imd_gridded_daily_regional_summary_2018_2024.csv"
    analysis_dir = root / "data" / "processed" / "analysis"

    analyzer = HistoricalHydrologyAnalyzer(discharge_threshold_cumecs=1500.0, event_gap_tolerance_days=2)
    result = analyzer.run_analysis_and_export(discharge_path, rainfall_path, analysis_dir)

    print("=== Historical Hydrology Analysis Summary ===")
    print(f"Total High-Discharge Episodes Extracted: {result['total_episodes_extracted']}")
    print(f"Documented Historical Flood Surges Captured: {result['documented_major_floods_captured']}")
    print(f"Episodes CSV Exported: {result['episodes_csv_path']}")
    print(f"Associations JSON Exported: {result['associations_json_path']}")


if __name__ == "__main__":
    main()
