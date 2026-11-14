import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import json
import joblib
from ml.training.train_discharge_models import OPERATIONAL_FEATURE_ALLOWLIST, ModelTrainingPipeline

pipeline = ModelTrainingPipeline()
train_rows, val_rows, test_rows = pipeline.load_dataset()
all_rows = train_rows + val_rows + test_rows

bundle = joblib.load('ml/models/hathnikund_rf_v1.joblib')
rf = bundle['model']
imputer = bundle['imputer']

X_all_raw = pipeline._extract_matrix(all_rows, OPERATIONAL_FEATURE_ALLOWLIST)
y_all = pipeline._extract_target(all_rows)
X_all_imp = imputer.transform(X_all_raw)
y_pred_all = rf.predict(X_all_imp)

high_flow_indices = [i for i, y in enumerate(y_all) if y >= 1500.0]
print(f"Total high-flow days (target >= 1500 cumecs): {len(high_flow_indices)}")
print("-" * 105)
print(f"{'Date':10s} | {'Part':5s} | {'Q(t)':7s} | {'Target Q':8s} | {'RF Pred':7s} | {'Error':9s} | {'% Under':7s} | {'RF 3d Prior':11s} | {'Inflow(t)':9s}")
print("-" * 105)

for idx in high_flow_indices:
    r = all_rows[idx]
    q_t = float(r['discharge_current_cumecs'])
    t_q = float(y_all[idx])
    p_q = float(y_pred_all[idx])
    err = p_q - t_q
    pct = (abs(err) / t_q) * 100.0
    rf3 = float(r['rainfall_accum_3d_prior_mm']) if r['rainfall_accum_3d_prior_mm'] else 0.0
    inf = float(r['inflow_current_cumecs']) if r['inflow_current_cumecs'] else 0.0
    print(f"{r['date']:10s} | {r['partition']:5s} | {q_t:7.1f} | {t_q:8.1f} | {p_q:7.1f} | {err:9.1f} | {pct:6.1f}% | {rf3:11.1f} | {inf:9.1f}")
