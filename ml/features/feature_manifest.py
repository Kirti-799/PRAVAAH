"""
ml/features/feature_manifest.py

Formal Feature Manifest and Schema Registry for PRAVAAH Phase 2A.
Documents every feature, mathematical formula, engineering unit, data provenance,
lookback window, operational availability, missingness behavior, and data leakage risk.

SCIENTIFIC PRINCIPLES:
1. Operational Predictors: Derived strictly from observations available at or before issue time t.
2. Retrospective Features: Explicitly segregated and forbidden from real-time operational inference.
3. No Lookahead Leakage: Rolling windows are strictly trailing (never centered, never forward-looking).
4. No Target Leakage: Target statistics, future flows, and future rainfalls are strictly isolated.
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureMetadata:
    name: str
    formula: str
    unit: str
    source: str
    lookback_window: str
    availability_time: str
    missing_value_behavior: str
    leakage_risk: str
    classification: str  # OPERATIONAL, RETROSPECTIVE_ANALYSIS_ONLY, TARGET, METADATA

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "formula": self.formula,
            "unit": self.unit,
            "source": self.source,
            "lookback_window": self.lookback_window,
            "availability_time": self.availability_time,
            "missing_value_behavior": self.missing_value_behavior,
            "leakage_risk": self.leakage_risk,
            "classification": self.classification,
        }


FEATURE_MANIFEST: List[FeatureMetadata] = [
    # --------------------------------------------------------------------------
    # TARGET VARIABLE
    # --------------------------------------------------------------------------
    FeatureMetadata(
        name="target_discharge_24h_cumecs",
        formula="Q_ds(t + 24h) = Q_ds(date + 1 day)",
        unit="m³/s (cumecs)",
        source="Haryana I&WRD Hathnikund Barrage Downstream Release (HKB D/S)",
        lookback_window="Lead time = +24 hours (+1 calendar day)",
        availability_time="Time t + 24h (08:00 IST of date + 1 day)",
        missing_value_behavior="Null (NaN) if date + 1 day is missing in source; excluded from supervised training",
        leakage_risk="TARGET VARIABLE: Strictly excluded from all predictor matrices",
        classification="TARGET",
    ),

    # --------------------------------------------------------------------------
    # DISCHARGE PREDICTORS (OPERATIONAL)
    # --------------------------------------------------------------------------
    FeatureMetadata(
        name="discharge_current_cumecs",
        formula="Q_ds(t)",
        unit="m³/s (cumecs)",
        source="Haryana I&WRD Hathnikund Barrage Downstream Release (HKB D/S)",
        lookback_window="Current observation (t)",
        availability_time="Available at forecast issue time t (08:00 IST morning gauge)",
        missing_value_behavior="If missing, forecast cannot be issued",
        leakage_risk="None: Measured at time t",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="discharge_lag_1d_cumecs",
        formula="Q_ds(date - 1 day)",
        unit="m³/s (cumecs)",
        source="Haryana I&WRD Hathnikund Barrage Downstream Release (HKB D/S)",
        lookback_window="Trailing 1 day (t - 24h)",
        availability_time="Known 24 hours prior to forecast issue time t",
        missing_value_behavior="Null if date - 1 day was unobserved; no silent zero-filling",
        leakage_risk="None: Strictly antecedent",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="discharge_lag_2d_cumecs",
        formula="Q_ds(date - 2 days)",
        unit="m³/s (cumecs)",
        source="Haryana I&WRD Hathnikund Barrage Downstream Release (HKB D/S)",
        lookback_window="Trailing 2 days (t - 48h)",
        availability_time="Known 48 hours prior to forecast issue time t",
        missing_value_behavior="Null if date - 2 days was unobserved",
        leakage_risk="None: Strictly antecedent",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="discharge_lag_3d_cumecs",
        formula="Q_ds(date - 3 days)",
        unit="m³/s (cumecs)",
        source="Haryana I&WRD Hathnikund Barrage Downstream Release (HKB D/S)",
        lookback_window="Trailing 3 days (t - 72h)",
        availability_time="Known 72 hours prior to forecast issue time t",
        missing_value_behavior="Null if date - 3 days was unobserved",
        leakage_risk="None: Strictly antecedent",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="discharge_lag_7d_cumecs",
        formula="Q_ds(date - 7 days)",
        unit="m³/s (cumecs)",
        source="Haryana I&WRD Hathnikund Barrage Downstream Release (HKB D/S)",
        lookback_window="Trailing 7 days (t - 168h)",
        availability_time="Known 7 days prior to forecast issue time t",
        missing_value_behavior="Null if date - 7 days was unobserved",
        leakage_risk="None: Strictly antecedent",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="discharge_delta_1d_cumecs",
        formula="Q_ds(t) - Q_ds(date - 1 day)",
        unit="m³/s (cumecs)",
        source="Derived from HKB D/S",
        lookback_window="Trailing 1 day rate of change",
        availability_time="Available at time t",
        missing_value_behavior="Null if lag 1 is missing",
        leakage_risk="None: Strictly antecedent",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="discharge_delta_ratio_1d",
        formula="(Q_ds(t) - Q_ds(date - 1 day)) / (Q_ds(date - 1 day) + 1.0)",
        unit="dimensionless ratio",
        source="Derived from HKB D/S",
        lookback_window="Trailing 1 day normalized delta",
        availability_time="Available at time t",
        missing_value_behavior="Null if lag 1 is missing",
        leakage_risk="None: Strictly antecedent",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="discharge_rolling_mean_3d_cumecs",
        formula="mean(Q_ds(date), Q_ds(date - 1), Q_ds(date - 2))",
        unit="m³/s (cumecs)",
        source="Derived from HKB D/S",
        lookback_window="Trailing 3-day window [t - 48h, t]",
        availability_time="Available at time t",
        missing_value_behavior="Null if any of the 3 days is missing",
        leakage_risk="None: Strictly trailing (never centered)",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="discharge_rolling_mean_7d_cumecs",
        formula="mean(Q_ds(date - k) for k in 0..6)",
        unit="m³/s (cumecs)",
        source="Derived from HKB D/S",
        lookback_window="Trailing 7-day window [t - 144h, t]",
        availability_time="Available at time t",
        missing_value_behavior="Null if any of the 7 days is missing",
        leakage_risk="None: Strictly trailing",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="discharge_rolling_max_7d_cumecs",
        formula="max(Q_ds(date - k) for k in 0..6)",
        unit="m³/s (cumecs)",
        source="Derived from HKB D/S",
        lookback_window="Trailing 7-day window [t - 144h, t]",
        availability_time="Available at time t",
        missing_value_behavior="Null if any of the 7 days is missing",
        leakage_risk="None: Strictly trailing",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="discharge_rolling_std_7d_cumecs",
        formula="sample_std(Q_ds(date - k) for k in 0..6)",
        unit="m³/s (cumecs)",
        source="Derived from HKB D/S",
        lookback_window="Trailing 7-day window [t - 144h, t]",
        availability_time="Available at time t",
        missing_value_behavior="Null if any of the 7 days is missing",
        leakage_risk="None: Strictly trailing",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="inflow_current_cumecs",
        formula="Q_us(t)",
        unit="m³/s (cumecs)",
        source="Haryana I&WRD Hathnikund Barrage Upstream Inflow (HKB U/S)",
        lookback_window="Current observation (t)",
        availability_time="Available at forecast issue time t (08:00 IST morning gauge)",
        missing_value_behavior="Null if unobserved (7 dry season dates missing in HKB U/S)",
        leakage_risk="None: Measured at time t",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="inflow_release_ratio_current",
        formula="Q_us(t) / (Q_ds(t) + 1.0)",
        unit="dimensionless ratio",
        source="Derived from HKB U/S and HKB D/S",
        lookback_window="Current observation (t)",
        availability_time="Available at time t",
        missing_value_behavior="Null if HKB U/S is missing",
        leakage_risk="None: Captures canal diversion regime at time t",
        classification="OPERATIONAL",
    ),

    # --------------------------------------------------------------------------
    # RAINFALL PREDICTORS (OPERATIONAL - ANTECEDENT ONLY)
    # --------------------------------------------------------------------------
    FeatureMetadata(
        name="rainfall_mean_d_minus_1_mm",
        formula="RF_mean(date - 1 day)",
        unit="mm/day",
        source="IMD Pune 0.25° Gridded Regional Summary (91 cells)",
        lookback_window="Preceding 24h accumulation ending at 08:30 IST on date - 1",
        availability_time="Known prior to forecast issue time t (ended ~23.5h prior)",
        missing_value_behavior="Null if gridded record absent (0 missing in 2018-2024)",
        leakage_risk="None: Strictly antecedent (ended prior to current morning)",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="rainfall_max_cell_d_minus_1_mm",
        formula="RF_max(date - 1 day)",
        unit="mm/day",
        source="IMD Pune 0.25° Gridded Regional Summary",
        lookback_window="Preceding 24h peak single-cell rainfall on date - 1",
        availability_time="Known prior to forecast issue time t",
        missing_value_behavior="Null if gridded record absent",
        leakage_risk="None: Strictly antecedent",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="rainfall_accum_3d_prior_mm",
        formula="sum(RF_mean(date - k) for k in [1, 2, 3])",
        unit="mm",
        source="Derived from IMD Gridded Rainfall",
        lookback_window="Trailing 3-day window [date - 3, date - 1]",
        availability_time="Known prior to forecast issue time t",
        missing_value_behavior="Null if any constituent day is missing",
        leakage_risk="None: Strictly antecedent",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="rainfall_accum_7d_prior_mm",
        formula="sum(RF_mean(date - k) for k in 1..7)",
        unit="mm",
        source="Derived from IMD Gridded Rainfall",
        lookback_window="Trailing 7-day window [date - 7, date - 1]",
        availability_time="Known prior to forecast issue time t",
        missing_value_behavior="Null if any constituent day is missing",
        leakage_risk="None: Strictly antecedent",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="rainfall_max_cell_3d_prior_mm",
        formula="max(RF_max(date - k) for k in [1, 2, 3])",
        unit="mm/day",
        source="Derived from IMD Gridded Rainfall",
        lookback_window="Trailing 3-day peak cell intensity",
        availability_time="Known prior to forecast issue time t",
        missing_value_behavior="Null if any constituent day is missing",
        leakage_risk="None: Strictly antecedent",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="rainfall_valid_cells_d_minus_1",
        formula="valid_cells_count(date - 1 day)",
        unit="count of cells (out of 91)",
        source="IMD Pune Gridded Quality Audit",
        lookback_window="Quality check on date - 1",
        availability_time="Available with gridded extraction",
        missing_value_behavior="Null if unobserved; 91 expected",
        leakage_risk="None: Quality audit flag",
        classification="OPERATIONAL",
    ),

    # --------------------------------------------------------------------------
    # RETROSPECTIVE ONLY RAINFALL FEATURE (FORBIDDEN IN REAL-TIME FORECASTING)
    # --------------------------------------------------------------------------
    FeatureMetadata(
        name="rainfall_mean_same_day_retro_mm",
        formula="RF_mean(date)",
        unit="mm/day",
        source="IMD Pune 0.25° Gridded Regional Summary",
        lookback_window="Accumulation ending at 08:30 IST on date t",
        availability_time="RETROSPECTIVE ARCHIVE ONLY: IMD gridded products have 24-48h publication latency",
        missing_value_behavior="Null if gridded record absent",
        leakage_risk="OPERATIONAL LEAKAGE RISK: Not available in real-time operational forecasting. Strictly research/retrospective only.",
        classification="RETROSPECTIVE_ANALYSIS_ONLY",
    ),

    # --------------------------------------------------------------------------
    # SEASONAL PREDICTORS (ASTRONOMICAL / CALENDAR - DETERMINISTIC)
    # --------------------------------------------------------------------------
    FeatureMetadata(
        name="day_of_year",
        formula="calendar day index (1 to 366)",
        unit="integer (1..366)",
        source="Calendar date of time t",
        lookback_window="Current date",
        availability_time="Known deterministically at time t",
        missing_value_behavior="Never missing",
        leakage_risk="None",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="month",
        formula="calendar month (1 to 12)",
        unit="integer (1..12)",
        source="Calendar date of time t",
        lookback_window="Current date",
        availability_time="Known deterministically at time t",
        missing_value_behavior="Never missing",
        leakage_risk="None",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="sin_doy",
        formula="sin(2 * pi * day_of_year / 365.25)",
        unit="dimensionless cyclical index [-1.0, 1.0]",
        source="Cyclical calendar transformation",
        lookback_window="Current date",
        availability_time="Known deterministically at time t",
        missing_value_behavior="Never missing",
        leakage_risk="None",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="cos_doy",
        formula="cos(2 * pi * day_of_year / 365.25)",
        unit="dimensionless cyclical index [-1.0, 1.0]",
        source="Cyclical calendar transformation",
        lookback_window="Current date",
        availability_time="Known deterministically at time t",
        missing_value_behavior="Never missing",
        leakage_risk="None",
        classification="OPERATIONAL",
    ),
    FeatureMetadata(
        name="is_monsoon",
        formula="1 if month in [6, 7, 8, 9] else 0",
        unit="binary flag {0, 1}",
        source="Meteorological monsoon definition (June–September)",
        lookback_window="Current date",
        availability_time="Known deterministically at time t",
        missing_value_behavior="Never missing",
        leakage_risk="None",
        classification="OPERATIONAL",
    ),
]


def get_feature_names_by_classification(classification: str) -> List[str]:
    """Retrieve list of feature names filtered by classification."""
    return [f.name for f in FEATURE_MANIFEST if f.classification == classification]


def get_feature_metadata_dict() -> Dict[str, Dict[str, Any]]:
    """Return dictionary of feature metadata keyed by feature name."""
    return {f.name: f.to_dict() for f in FEATURE_MANIFEST}
