import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import json
import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor, GradientBoostingRegressor

from ml.evaluation.discharge_baselines import (
    ForecastMetricsCalculator,
    DischargePersistenceBaseline,
    DischargeTrailingMeanBaseline,
    SimpleLinearDischargeBaseline,
)
from ml.training.train_discharge_models import OPERATIONAL_FEATURE_ALLOWLIST, ModelTrainingPipeline

pipeline = ModelTrainingPipeline()
train_rows, val_rows, test_rows = pipeline.load_dataset()

# Check row counts
print(f'Partitions count: TRAIN={len(train_rows)}, VAL={len(val_rows)}, TEST={len(test_rows)}')

# Load saved models
model_path = Path('ml/models/hathnikund_rf_v1.joblib')
bundle = joblib.load(model_path)
rf = bundle['model']
imputer = bundle['imputer']

# Re-run baselines
pers = DischargePersistenceBaseline()
trail = DischargeTrailingMeanBaseline()
linear = SimpleLinearDischargeBaseline()
linear.fit(train_rows)

# Preprocessing
X_train_raw = pipeline._extract_matrix(train_rows, OPERATIONAL_FEATURE_ALLOWLIST)
y_train = pipeline._extract_target(train_rows)
X_val_raw = pipeline._extract_matrix(val_rows, OPERATIONAL_FEATURE_ALLOWLIST)
y_val = pipeline._extract_target(val_rows)
X_test_raw = pipeline._extract_matrix(test_rows, OPERATIONAL_FEATURE_ALLOWLIST)
y_test = pipeline._extract_target(test_rows)

X_train_imp = imputer.transform(X_train_raw)
X_val_imp = imputer.transform(X_val_raw)
X_test_imp = imputer.transform(X_test_raw)

hgb = HistGradientBoostingRegressor(max_iter=80, max_depth=4, l2_regularization=10.0, learning_rate=0.03, min_samples_leaf=10, random_state=42)
hgb.fit(X_train_raw, y_train)

gb = GradientBoostingRegressor(n_estimators=100, max_depth=3, learning_rate=0.03, min_samples_leaf=5, random_state=42)
gb.fit(X_train_imp, y_train)

models = {
    'Persistence': (lambda rows, x_imp, x_raw: pers.predict(rows)),
    'Trailing 3d Mean': (lambda rows, x_imp, x_raw: trail.predict(rows)),
    'Linear OLS': (lambda rows, x_imp, x_raw: linear.predict(rows)),
    'Random Forest v1': (lambda rows, x_imp, x_raw: rf.predict(x_imp).tolist()),
    'HistGradientBoosting v1': (lambda rows, x_imp, x_raw: hgb.predict(x_raw).tolist()),
    'Gradient Boosting v1': (lambda rows, x_imp, x_raw: gb.predict(x_imp).tolist()),
}

partitions = {
    'TRAIN': (train_rows, X_train_imp, X_train_raw, y_train),
    'VAL': (val_rows, X_val_imp, X_val_raw, y_val),
    'TEST': (test_rows, X_test_imp, X_test_raw, y_test),
}

reproduced_metrics = {}

for p_name, (p_rows, p_x_imp, p_x_raw, p_y) in partitions.items():
    print(f"\n=== {p_name} PARTITION (N={len(p_rows)}) ===")
    reproduced_metrics[p_name] = {}
    y_pers = pers.predict(p_rows)
    hf_mask = (p_y >= 1500.0)
    hf_count = int(np.sum(hf_mask))
    
    for m_name, pred_fn in models.items():
        preds = pred_fn(p_rows, p_x_imp, p_x_raw)
        m = ForecastMetricsCalculator.evaluate(p_y.tolist(), preds, y_pers)
        
        # High flow
        hf_true = p_y[hf_mask].tolist()
        hf_pred = [preds[i] for i in range(len(p_y)) if hf_mask[i]]
        hf_pers = [y_pers[i] for i in range(len(p_y)) if hf_mask[i]]
        m_hf = ForecastMetricsCalculator.evaluate(hf_true, hf_pred, hf_pers)
        
        skill = m.get('skill_score_vs_persistence', 0.0)
        reproduced_metrics[p_name][m_name] = {
            'overall': m,
            'high_flow': m_hf,
            'high_flow_count': hf_count
        }
        mae_str = f"{m['mae_cumecs']:.2f}"
        rmse_str = f"{m['rmse_cumecs']:.2f}"
        r2_str = f"{m['r2_score']:.4f}"
        bias_str = f"{m['mean_bias_cumecs']:.2f}"
        skill_str = f"{skill:.4f}"
        hf_mae_str = f"{m_hf['mae_cumecs']:.2f}"
        hf_rmse_str = f"{m_hf['rmse_cumecs']:.2f}"
        hf_bias_str = f"{m_hf['mean_bias_cumecs']:.2f}"
        print(f"{m_name:24s} | MAE: {mae_str:>6s} | RMSE: {rmse_str:>6s} | R2: {r2_str:>7s} | Bias: {bias_str:>6s} | Skill: {skill_str:>7s} | HF MAE ({hf_count}d): {hf_mae_str:>7s} | HF RMSE: {hf_rmse_str:>7s} | HF Bias: {hf_bias_str:>8s}")

# Write to scratch json for verification
with open('data/processed/analysis/phase_2c_reproduced_metrics.json', 'w') as f:
    json.dump(reproduced_metrics, f, indent=2)
print("\nReproduced metrics written to data/processed/analysis/phase_2c_reproduced_metrics.json")
