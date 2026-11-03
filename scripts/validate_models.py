#!/usr/bin/env python3
"""Validate trained models on real Jira snapshot data."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.preprocessing.feature_engineering import preprocess_features


DATA_PATH = PROJECT_ROOT / "data" / "real_jira_snapshot.csv"
MODEL_DIR = PROJECT_ROOT / "models"
RF_MODEL_PATH = MODEL_DIR / "rf_model.pkl"
XGB_MODEL_PATH = MODEL_DIR / "xgb_model.pkl"
FEATURE_COLUMNS_PATH = MODEL_DIR / "feature_columns.pkl"


def _align_features(X: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    missing = [col for col in feature_columns if col not in X.columns]
    if missing:
        for col in missing:
            X[col] = 0
    extra = [col for col in X.columns if col not in feature_columns]
    if extra:
        X = X.drop(columns=extra)
    return X[feature_columns]


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing data file: {DATA_PATH}")
    if not FEATURE_COLUMNS_PATH.exists():
        raise FileNotFoundError(f"Missing feature schema: {FEATURE_COLUMNS_PATH}")

    df = pd.read_csv(DATA_PATH)
    if "Risk_Level" not in df.columns:
        raise ValueError("Expected Risk_Level column in real Jira snapshot data")

    feature_columns = joblib.load(FEATURE_COLUMNS_PATH)
    X = preprocess_features(df, verbose=False, use_tfidf=False, tfidf_max_features=20)
    X = _align_features(X, feature_columns)

    y = df["Risk_Level"].copy()
    if y.dtype == object:
        y = y.map({"Low": 0, "Medium": 1, "High": 2})

    results = {}
    for name, model_path in ("RandomForest", RF_MODEL_PATH), ("XGBoost", XGB_MODEL_PATH):
        if not model_path.exists():
            raise FileNotFoundError(f"Missing model file: {model_path}")
        model = joblib.load(model_path)
        preds = model.predict(X)
        acc = accuracy_score(y, preds)
        macro_f1 = f1_score(y, preds, average="macro")
        results[name] = {"accuracy": acc, "macro_f1": macro_f1}

        print(f"\n--- {name} Results (real Jira data) ---")
        print(f"Accuracy: {acc:.4f}")
        print(f"Macro F1: {macro_f1:.4f}")
        print(
            classification_report(
                y,
                preds,
                labels=[0, 1, 2],
                target_names=["Low", "Medium", "High"],
                zero_division=0,
            )
        )

    print("\n[INFO] Validation complete.")
    for name, metrics in results.items():
        print(f"[INFO] {name}: accuracy={metrics['accuracy']:.4f}, macro_f1={metrics['macro_f1']:.4f}")


if __name__ == "__main__":
    main()
