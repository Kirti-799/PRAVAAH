"""
ml/tests/test_event_analysis.py

Automated unit tests for HydrologicalEventAnalyzer.
SAFETY WARNING:
All fixtures created in this test file are EXPLICITLY SYNTHETIC and TEMPORARY.
They exist purely to test gap calculations and threshold exceedance episode clustering.
THEY DO NOT REPRESENT REAL-WORLD FLOOD, HYDROLOGICAL, OR METEOROLOGICAL OBSERVATIONS.
"""

import pytest
from datetime import datetime, timezone, timedelta
from ml.data_processing.event_analysis import HydrologicalEventAnalyzer


@pytest.fixture
def synthetic_hydrograph():
    """Create a temporary synthetic sequence with two distinct breach episodes."""
    base_t = datetime(2023, 7, 1, 8, 0, tzinfo=timezone.utc)
    obs = []

    # Episode 1: Day 1-2 (peak 206.2)
    # Episode 2: Day 6-7 (peak 207.5) separated by > 48h
    for day in range(10):
        t = base_t + timedelta(days=day)
        if day in (1, 2):
            stage = 206.2 if day == 2 else 205.5
        elif day in (6, 7):
            stage = 207.5 if day == 6 else 205.8
        else:
            stage = 203.5
        obs.append({"timestamp_utc": t.isoformat(), "stage_m": stage})

    return obs


def test_event_analyzer_completeness(synthetic_hydrograph):
    """Verify calculation of actual, expected, and gap hours."""
    analyzer = HydrologicalEventAnalyzer(expected_frequency_hours=24)
    summary = analyzer.analyze_completeness(synthetic_hydrograph)

    assert summary["actual_observations"] == 10
    assert summary["expected_observations"] == 10
    assert summary["missing_percentage"] == 0.0
    assert summary["duplicate_timestamps"] == 0
    assert summary["max_continuous_gap_hours"] == 24.0


def test_event_analyzer_groups_episodes(synthetic_hydrograph):
    """Verify that exceedances separated by > 48h are grouped into 2 distinct episodes."""
    analyzer = HydrologicalEventAnalyzer(danger_threshold_m=205.33, min_separation_hours=48)
    episodes = analyzer.group_episodes(synthetic_hydrograph)

    assert len(episodes) == 2

    # Episode 1
    ep1 = episodes[0]
    assert ep1["episode_id"] == 1
    assert ep1["exceedance_observations_count"] == 2
    assert ep1["peak_value"] == 206.2

    # Episode 2
    ep2 = episodes[1]
    assert ep2["episode_id"] == 2
    assert ep2["exceedance_observations_count"] == 2
    assert ep2["peak_value"] == 207.5


def test_event_analyzer_no_exceedance():
    """Verify empty return when all observations remain sub-threshold."""
    base_t = datetime(2023, 7, 1, 8, 0, tzinfo=timezone.utc)
    obs = [{"timestamp_utc": (base_t + timedelta(days=i)).isoformat(), "stage_m": 202.0} for i in range(5)]
    analyzer = HydrologicalEventAnalyzer(danger_threshold_m=205.33)
    episodes = analyzer.group_episodes(obs)
    assert len(episodes) == 0
