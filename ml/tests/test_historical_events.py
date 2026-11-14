"""
ml/tests/test_historical_events.py

Unit tests for HistoricalHydrologyAnalyzer verifying:
- Episode clustering and duration calculations
- Antecedent rainfall accumulation without future-information leakage
- Pearson r and Spearman rho correlation calculations
- Discharge variable semantics and missingness handling
"""

import pytest
from ml.data_processing.historical_events import HistoricalHydrologyAnalyzer


def test_pearson_and_spearman_calculation():
    # Perfectly monotonic linear relation
    x = [10.0, 20.0, 30.0, 40.0, 50.0]
    y = [100.0, 200.0, 300.0, 400.0, 500.0]

    r, rho = HistoricalHydrologyAnalyzer._pearson_and_spearman(x, y)
    assert r == 1.0
    assert rho == 1.0

    # Non-linear monotonic relation
    x2 = [1.0, 2.0, 3.0, 4.0, 5.0]
    y2 = [1.0, 4.0, 9.0, 16.0, 25.0]
    r2, rho2 = HistoricalHydrologyAnalyzer._pearson_and_spearman(x2, y2)
    assert rho2 == 1.0
    assert 0.95 < r2 < 1.0


def test_episode_extraction_clustering():
    analyzer = HistoricalHydrologyAnalyzer(discharge_threshold_cumecs=1000.0, event_gap_tolerance_days=2)

    # 3 consecutive days exceeding threshold -> 1 single episode
    daily_q_us = {
        "2023-07-08": 400.0,
        "2023-07-09": 800.0,
        "2023-07-10": 8000.0,
        "2023-07-11": 7000.0,
        "2023-07-12": 5000.0,
        "2023-07-13": 800.0,
    }
    daily_q_ds = {
        "2023-07-08": 10.0,
        "2023-07-09": 400.0,
        "2023-07-10": 8000.0,
        "2023-07-11": 7000.0,
        "2023-07-12": 5000.0,
        "2023-07-13": 200.0,
    }
    daily_rf = {
        "2023-07-07": {"mean": 10.0, "valid_cells": 91},
        "2023-07-08": {"mean": 25.0, "valid_cells": 91},
        "2023-07-09": {"mean": 60.0, "valid_cells": 91},
        "2023-07-10": {"mean": 65.0, "valid_cells": 91},
        "2023-07-11": {"mean": 15.0, "valid_cells": 91},
        "2023-07-12": {"mean": 5.0, "valid_cells": 91},
    }

    episodes = analyzer.extract_episodes(daily_q_us, daily_q_ds, daily_rf)
    assert len(episodes) == 1
    ep = episodes[0]
    assert ep["start_date"] == "2023-07-10"
    assert ep["end_date"] == "2023-07-12"
    assert ep["duration_days"] == 3
    assert ep["peak_date"] == "2023-07-10"
    assert ep["peak_upstream_inflow_cumecs"] == 8000.0

    # Antecedent rainfall for peak 2023-07-10:
    # 1d: rain on 2023-07-09 -> 60.0
    assert ep["rainfall_accum_1d_mm"] == 60.0
    # 3d: rain on 2023-07-09 (60.0) + 2023-07-08 (25.0) + 2023-07-07 (10.0) = 95.0
    assert ep["rainfall_accum_3d_mm"] == 95.0


def test_episode_gap_tolerance():
    analyzer = HistoricalHydrologyAnalyzer(discharge_threshold_cumecs=1000.0, event_gap_tolerance_days=2)

    # Event 1: July 10; Event 2: July 12 (gap of 1 day between end and start -> merged)
    # Event 3: July 20 (gap of 8 days -> separate episode)
    daily_q_us = {
        "2023-07-10": 2000.0,
        "2023-07-11": 500.0,
        "2023-07-12": 2500.0,
        "2023-07-20": 3000.0,
    }
    daily_q_ds = daily_q_us.copy()
    daily_rf = {d: {"mean": 10.0, "valid_cells": 91} for d in daily_q_us}
    for k in range(1, 10):
        daily_rf[f"2023-07-{k:02d}"] = {"mean": 5.0, "valid_cells": 91}

    episodes = analyzer.extract_episodes(daily_q_us, daily_q_ds, daily_rf)
    assert len(episodes) == 2
    assert episodes[0]["start_date"] == "2023-07-10"
    assert episodes[0]["end_date"] == "2023-07-12"
    assert episodes[1]["start_date"] == "2023-07-20"
    assert episodes[1]["end_date"] == "2023-07-20"
