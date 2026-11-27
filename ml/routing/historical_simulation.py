"""
ml/routing/historical_simulation.py

Reproducible Historical Flood Episode Routing Simulation for PRAVAAH.
Applies the non-ML Muskingum routing prototype to the 10 verified historical
high-discharge episodes (2018–2024), clearly distinguishing:
1. Observed Hathnikund upstream inflow (HKB U/S).
2. Observed Hathnikund downstream release (HKB D/S).
3. Simulated downstream routed discharge (NOT observed water level).
4. Independently documented historical Delhi ORB flood peak stage.
5. Confirmed stage-threshold breaches.
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from ml.routing.parameters import MuskingumParameters
from ml.routing.muskingum import MuskingumRouter, RoutingSimulationResult


def get_default_data_dir() -> Path:
    # ml/routing/historical_simulation.py -> parents[2] is repo root
    return Path(__file__).resolve().parents[2] / "data"


class HistoricalEpisodeRouter:
    """Executes Muskingum routing simulations across historical high-discharge episodes."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or get_default_data_dir()
        self.discharge_csv = self.data_dir / "processed" / "hydrological" / "haryana_hathnikund_discharge_daily_2018_2025.csv"
        self.episodes_csv = self.data_dir / "processed" / "analysis" / "historical_high_discharge_episodes.csv"

    def load_episode_records(self) -> List[Dict[str, Any]]:
        """Load verified episodes extracted during Phase 1E."""
        if not self.episodes_csv.exists():
            raise FileNotFoundError(f"Episodes file not found: {self.episodes_csv}")
        episodes = []
        with open(self.episodes_csv, mode="r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                episodes.append(row)
        return episodes

    def load_discharge_series(self) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Load full historical Hathnikund inflow and release time series."""
        if not self.discharge_csv.exists():
            raise FileNotFoundError(f"Discharge dataset not found: {self.discharge_csv}")

        us_series: Dict[str, float] = {}
        ds_series: Dict[str, float] = {}

        with open(self.discharge_csv, mode="r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                d = row["date"].strip()
                st = row["station_name"].strip()
                q = float(row["discharge_cumecs"])
                if st == "HKB U/S":
                    us_series[d] = q
                elif st == "HKB D/S":
                    ds_series[d] = q

        return us_series, ds_series

    def simulate_episode(
        self,
        episode_id: str,
        buffer_days_before: int = 3,
        buffer_days_after: int = 5,
        K_hours: float = 36.0,
        x: float = 0.20,
        dt_hours: float = 24.0,
        subreaches: int = 1,
    ) -> Dict[str, Any]:
        """
        Run routing simulation for a specific historical episode, expanding the window
        with pre- and post-buffers to observe hydrograph rising and recession limbs.
        """
        episodes = {ep["episode_id"]: ep for ep in self.load_episode_records()}
        if episode_id not in episodes:
            raise KeyError(f"Episode ID '{episode_id}' not found in verified registry.")

        ep = episodes[episode_id]
        start_dt = ep["start_date"]
        end_dt = ep["end_date"]

        us_all, ds_all = self.load_discharge_series()
        all_dates = sorted(list(ds_all.keys()))

        start_idx = all_dates.index(start_dt) if start_dt in all_dates else 0
        end_idx = all_dates.index(end_dt) if end_dt in all_dates else len(all_dates) - 1

        window_start_idx = max(0, start_idx - buffer_days_before)
        window_end_idx = min(len(all_dates) - 1, end_idx + buffer_days_after)

        window_dates = all_dates[window_start_idx : window_end_idx + 1]
        window_inflows = [ds_all[d] for d in window_dates]  # Upstream release HKB D/S is the inflow to reach!

        router = MuskingumRouter.create(
            K_hours=K_hours,
            x=x,
            dt_hours=dt_hours,
            subreaches=subreaches,
        )
        sim_result = router.route(window_dates, window_inflows)

        # Merge upstream inflow (HKB U/S) for comparison
        series_with_inflow = []
        for pt in sim_result.time_series:
            d = pt.date
            series_with_inflow.append({
                "date": d,
                "observed_upstream_inflow_cumecs": us_all.get(d),
                "observed_upstream_release_cumecs": pt.observed_inflow_cumecs,
                "simulated_downstream_discharge_cumecs": pt.simulated_outflow_cumecs,
                "observed_downstream_stage_m": None,  # Strictly None
            })

        # Known documented historical Delhi stage peaks (from official bulletins)
        documented_delhi_peaks = {
            "EPISODE_2019_04": {"crest_stage_m": 206.60, "crest_date": "2019-08-21", "threshold_breached": "Danger Mark (205.33 m)"},
            "EPISODE_2022_07": {"crest_stage_m": 205.99, "crest_date": "2022-09-28", "threshold_breached": "Danger Mark (205.33 m)"},
            "EPISODE_2023_08": {"crest_stage_m": 208.66, "crest_date": "2023-07-13", "threshold_breached": "Highest Flood Level (HFL breached)"},
        }

        doc_info = documented_delhi_peaks.get(episode_id, {
            "crest_stage_m": None,
            "crest_date": None,
            "threshold_breached": "Unrecorded in major bulletins / within banks",
        })

        return {
            "episode_id": episode_id,
            "episode_name": ep.get("historical_context", ""),
            "simulation_window_start": window_dates[0],
            "simulation_window_end": window_dates[-1],
            "observed_hathnikund_peak_inflow_cumecs": float(ep["peak_upstream_inflow_cumecs"]),
            "observed_hathnikund_peak_release_cumecs": float(ep["peak_downstream_release_cumecs"]),
            "observed_hathnikund_peak_date": ep["peak_date"],
            "simulated_peak_downstream_discharge_cumecs": sim_result.peak_simulated_outflow_cumecs,
            "simulated_peak_downstream_date": sim_result.peak_simulated_outflow_date,
            "simulated_attenuation_cumecs": sim_result.simulated_attenuation_cumecs,
            "simulated_attenuation_percent": sim_result.simulated_attenuation_percent,
            "simulated_lag_hours": sim_result.simulated_lag_hours,
            "mass_balance_error_percent": sim_result.mass_balance_error_percent,
            "documented_delhi_crest_stage_m": doc_info["crest_stage_m"],
            "documented_delhi_crest_date": doc_info["crest_date"],
            "documented_delhi_breach_status": doc_info["threshold_breached"],
            "routing_parameters": sim_result.parameters,
            "routing_coefficients": sim_result.routing_coefficients,
            "time_series": series_with_inflow,
            "scientific_disclaimer": sim_result.scientific_disclaimer,
            "scientific_caveats": sim_result.scientific_caveats,
        }

    def simulate_all_episodes(
        self,
        K_hours: float = 36.0,
        x: float = 0.20,
    ) -> List[Dict[str, Any]]:
        """Run routing simulation on all 10 verified historical episodes."""
        episodes = self.load_episode_records()
        summaries = []
        for ep in episodes:
            res = self.simulate_episode(ep["episode_id"], K_hours=K_hours, x=x)
            summaries.append({
                "episode_id": res["episode_id"],
                "start_date": res["simulation_window_start"],
                "end_date": res["simulation_window_end"],
                "observed_hathnikund_inflow_peak_cumecs": res["observed_hathnikund_peak_inflow_cumecs"],
                "observed_hathnikund_release_peak_cumecs": res["observed_hathnikund_peak_release_cumecs"],
                "simulated_downstream_discharge_peak_cumecs": res["simulated_peak_downstream_discharge_cumecs"],
                "simulated_peak_date": res["simulated_peak_downstream_date"],
                "simulated_attenuation_percent": res["simulated_attenuation_percent"],
                "simulated_lag_hours": res["simulated_lag_hours"],
                "mass_balance_error_percent": res["mass_balance_error_percent"],
                "documented_delhi_crest_stage_m": res["documented_delhi_crest_stage_m"],
                "documented_delhi_breach_status": res["documented_delhi_breach_status"],
            })
        return summaries
