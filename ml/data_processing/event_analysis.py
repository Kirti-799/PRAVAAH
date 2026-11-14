"""
ml/data_processing/event_analysis.py

Hydrological Event Grouping and Missing-Data Analysis Utility for PRAVAAH.
Evaluates time-series completeness, calculates observational gaps, and
identifies independent flood threshold-breach episodes.

EPISODE GROUPING LOGIC:
Consecutive observations above the flood danger mark (e.g. 205.33 m) belong
to the same event episode. Separate breaches occurring within a minimum
separation window (e.g. 48 hours) are merged into a single multi-peak episode
rather than counted as independent statistical events.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple


class HydrologicalEventAnalyzer:
    """Analyzes observational completeness and groups flood threshold-breach episodes."""

    def __init__(
        self,
        danger_threshold_m: float = 205.33,
        min_separation_hours: int = 48,
        expected_frequency_hours: int = 24,
    ):
        self.danger_threshold_m = danger_threshold_m
        self.min_separation_hours = min_separation_hours
        self.expected_frequency_hours = expected_frequency_hours

    def analyze_completeness(
        self,
        observations: List[Dict[str, Any]],
        timestamp_key: str = "timestamp_utc",
        value_key: str = "stage_m",
    ) -> Dict[str, Any]:
        """Calculate missingness, expected vs actual observations, and max continuous gaps."""
        if not observations:
            return {"total_observations": 0, "status": "empty"}

        valid_points: List[Tuple[datetime, float]] = []
        duplicate_count = 0
        seen_timestamps = set()

        for r in observations:
            raw_ts = r.get(timestamp_key) or r.get("date")
            val = r.get(value_key)
            if raw_ts is None or val is None:
                continue

            # Parse datetime
            dt = raw_ts if isinstance(raw_ts, datetime) else self._parse_dt(str(raw_ts))
            if dt is None:
                continue

            try:
                f_val = float(val)
            except ValueError:
                continue

            if dt in seen_timestamps:
                duplicate_count += 1
            else:
                seen_timestamps.add(dt)
                valid_points.append((dt, f_val))

        valid_points.sort(key=lambda x: x[0])
        if not valid_points:
            return {"total_observations": 0, "status": "no_valid_observations"}

        start_time = valid_points[0][0]
        end_time = valid_points[-1][0]
        total_duration_hours = (end_time - start_time).total_seconds() / 3600.0

        expected_count = int(total_duration_hours / self.expected_frequency_hours) + 1
        actual_count = len(valid_points)
        missing_count = max(0, expected_count - actual_count)
        missing_percentage = round((missing_count / expected_count) * 100, 2) if expected_count > 0 else 0.0

        # Compute continuous gaps
        max_gap_hours = 0.0
        monsoon_obs = 0
        monsoon_expected = 0

        # Track gaps between consecutive points
        for i in range(1, len(valid_points)):
            gap = (valid_points[i][0] - valid_points[i - 1][0]).total_seconds() / 3600.0
            if gap > max_gap_hours:
                max_gap_hours = gap

        # Monthly breakdown
        monthly_counts: Dict[str, int] = {}
        for dt, _ in valid_points:
            month_key = dt.strftime("%Y-%m")
            monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
            if dt.month in (6, 7, 8, 9, 10):
                monsoon_obs += 1

        return {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_days": round(total_duration_hours / 24.0, 1),
            "actual_observations": actual_count,
            "expected_observations": expected_count,
            "missing_observations": missing_count,
            "missing_percentage": missing_percentage,
            "duplicate_timestamps": duplicate_count,
            "max_continuous_gap_hours": round(max_gap_hours, 1),
            "monsoon_observations_count": monsoon_obs,
            "monthly_counts": monthly_counts,
        }

    def group_episodes(
        self,
        observations: List[Dict[str, Any]],
        timestamp_key: str = "timestamp_utc",
        value_key: str = "stage_m",
    ) -> List[Dict[str, Any]]:
        """Group consecutive threshold exceedances into distinct multi-day flood episodes."""
        valid_points: List[Tuple[datetime, float]] = []
        for r in observations:
            raw_ts = r.get(timestamp_key) or r.get("date")
            val = r.get(value_key)
            if raw_ts is None or val is None:
                continue
            dt = raw_ts if isinstance(raw_ts, datetime) else self._parse_dt(str(raw_ts))
            if dt is None:
                continue
            try:
                f_val = float(val)
                valid_points.append((dt, f_val))
            except ValueError:
                continue

        valid_points.sort(key=lambda x: x[0])
        if not valid_points:
            return []

        # Find points above threshold
        exceedances = [(t, val) for t, val in valid_points if val >= self.danger_threshold_m]
        if not exceedances:
            return []

        episodes: List[Dict[str, Any]] = []
        current_cluster: List[Tuple[datetime, float]] = [exceedances[0]]

        for i in range(1, len(exceedances)):
            prev_t, _ = current_cluster[-1]
            curr_t, _ = exceedances[i]
            gap_hours = (curr_t - prev_t).total_seconds() / 3600.0

            if gap_hours <= self.min_separation_hours:
                current_cluster.append(exceedances[i])
            else:
                episodes.append(self._create_episode_summary(len(episodes) + 1, current_cluster))
                current_cluster = [exceedances[i]]

        if current_cluster:
            episodes.append(self._create_episode_summary(len(episodes) + 1, current_cluster))

        return episodes

    def _create_episode_summary(
        self, episode_id: int, cluster: List[Tuple[datetime, float]]
    ) -> Dict[str, Any]:
        """Summarize start, peak, end, and duration of an exceedance cluster."""
        start_t = cluster[0][0]
        end_t = cluster[-1][0]
        peak_t, peak_val = max(cluster, key=lambda x: x[1])
        duration_hours = (end_t - start_t).total_seconds() / 3600.0

        return {
            "episode_id": episode_id,
            "start_time": start_t.isoformat(),
            "end_time": end_t.isoformat(),
            "peak_time": peak_t.isoformat(),
            "peak_value": round(peak_val, 2),
            "danger_threshold_m": self.danger_threshold_m,
            "exceedance_observations_count": len(cluster),
            "duration_hours": round(duration_hours, 1),
            "duration_days": round(duration_hours / 24.0, 2),
        }

    @staticmethod
    def _parse_dt(s: str) -> Optional[datetime]:
        """Parse datetime string to timezone-aware UTC datetime."""
        clean = s.strip()
        try:
            dt = datetime.fromisoformat(clean.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            pass

        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d-%m-%Y %H:%M",
            "%d/%m/%Y %H:%M",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(clean, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        return None
