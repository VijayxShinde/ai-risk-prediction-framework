# Session Handoff — 2026-04-06

## Where We Left Off

### Root Problem
SHAP 0.49.1 is incompatible with XGBoost 3.2.0.
XGBoost 3.x stores `base_score` as a per-class vector string (e.g. `[5E-1,5E-1,5E-1]`).
SHAP's `XGBTreeModelLoader._tree.py` line 2104 does `float(base_score)` — crashes on a vector.

### What Was Tried (and Why It Failed)
| Approach | Why it failed |
|---|---|
| `save_config()` / `load_config()` | SHAP doesn't read from config — it reads from model binary |
| `save_model()` / `load_model()` on temp file | SHAP calls `save_raw()` on the internal booster buffer — unaffected by `load_model` |
| `shap.Explainer(model, masker)` | XGBClassifier is not directly callable in that API |
| Retrain with `base_score=0.5` | XGBoost 3.x still stores it as vector internally regardless |
| `pip install --upgrade shap` | 0.49.1 is already the latest — bug not fixed yet in SHAP |

### Current Fix In Progress
**Downgrading XGBoost to 2.1.4** — last known version that stores `base_score` as a scalar,
fully compatible with SHAP 0.49.1.

Command was running when session ended:
```
cmd /c ".venv\Scripts\pip.exe install xgboost==2.1.4 > logs\xgb_downgrade.log 2>&1"
```

## Resume Steps Tomorrow

1. Check if the downgrade completed:
   ```
   type logs\xgb_downgrade.log
   ```

2. If successful, retrain the model (so it's saved with XGBoost 2.1.4 format):
   ```
   cmd /c ".venv\Scripts\python.exe src\models\train.py > logs\train_run.log 2>&1"
   ```

3. Run the SHAP explainer:
   ```
   cmd /c ".venv\Scripts\python.exe src\xai\shap_explainer.py > logs\shap_debug.log 2>&1"
   type logs\shap_debug.log
   ```

4. If SHAP works, the output plot will be at `app/components/shap_summary.png`.

5. Update `requirements.txt` to pin `xgboost==2.1.4` so it doesn't accidentally upgrade again.

## Files Changed Today (Summary)
| File | Change |
|---|---|
| `src/xai/shap_explainer.py` | Full rewrite — preprocessing replicated, emojis removed, base_score patch attempt |
| `src/models/train.py` | Added `base_score=0.5`, removed all emojis |
| `src/preprocessing/data_pipeline.py` | Removed warning emoji |
