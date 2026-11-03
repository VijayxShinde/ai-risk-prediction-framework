# Agent Handoff Notes

This repository contains an AI risk prediction pipeline with shared preprocessing and saved model artifacts.

## Critical Rules
- `models/feature_columns.pkl` is the single source of truth for input feature order. Keep it in sync with training and inference.
- Training currently uses SMOTE for class balancing and TF-IDF text features (150 max features).
- The canonical preprocessing pipeline is in `src/preprocessing/feature_engineering.py`. Do not duplicate feature logic elsewhere.

## Training Artifacts
- Models: `models/rf_model.pkl`, `models/xgb_model.pkl`
- Feature schema: `models/feature_columns.pkl`

## Workflow Notes
- Use Python 3.10 from `.venv/Scripts/python.exe` for scripts, training, and tests.
- Retrain models via `src/training/train.py` after changing features.
- Update `models/feature_columns.pkl` whenever the feature set changes.
