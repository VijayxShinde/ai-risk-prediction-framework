import json
import sys
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
from src.preprocessing.feature_engineering import preprocess_features

import os
import re

# Constants
from src.config import Paths

MODEL_PATH = str(Paths.XGB_MODEL)
DATA_PATH = str(Paths.ML_READY_DATA)
OUTPUT_PLOT_PATH = str(Paths.SHAP_SUMMARY_IMG)


def preprocess_for_shap(df: pd.DataFrame) -> tuple:
    X = preprocess_features(df, verbose=True)
    return X, list(X.columns)


def patch_booster_base_score(booster):
    """
    Safety patch: if the booster's base_score is stored as a per-class vector
    string (e.g. '[3.3E-5,-1.7E-5,-1.6E-5]'), SHAP's TreeExplainer crashes
    trying to cast it to float. This patches it to a scalar via save/load_model.

    This is a known XGBoost/SHAP version-mismatch issue. The permanent fix is
    training with base_score=0.5 explicitly (already set in train.py). This
    function exists only as a fallback for older saved model files.
    """
    tmp_model_file = None
    try:
        fd, tmp_model_file = tempfile.mkstemp(suffix=".json")
        os.close(fd)

        booster.save_model(tmp_model_file)

        # Read as raw bytes; XGBoost model JSON may contain surrogate chars
        # from embedded binary data — surrogatepass avoids decode failures.
        raw_bytes = open(tmp_model_file, "rb").read()
        model_json = json.loads(raw_bytes.decode("utf-8", errors="surrogatepass"))

        raw_bs = model_json["learner"]["learner_model_param"]["base_score"]

        if raw_bs.strip().startswith("["):
            # Vector form: '[3.3140182E-5,-1.7166138E-5,-1.5854836E-5]'
            # Python's float() handles scientific notation like '3.3E-5' natively.
            tokens = raw_bs.strip()[1:-1].split(",")
            values = [float(t.strip()) for t in tokens]
            scalar = float(np.mean(values))
            print(f"[PATCH] base_score is a {len(values)}-class vector: {raw_bs}")
            print(f"[PATCH] Rewriting as scalar mean: {scalar:.12f}")

            model_json["learner"]["learner_model_param"]["base_score"] = str(scalar)
            patched = json.dumps(model_json).encode("utf-8", errors="surrogatepass")
            open(tmp_model_file, "wb").write(patched)

            booster.load_model(tmp_model_file)
            print("[PATCH] Booster reloaded with scalar base_score.")
        else:
            print(f"[INFO] base_score is a scalar ({raw_bs}) - no patch needed.")

    finally:
        if tmp_model_file and os.path.exists(tmp_model_file):
            os.unlink(tmp_model_file)


def run_shap_analysis():
    # 1. Load model
    print(f"[INFO] Loading model from {MODEL_PATH}...")
    try:
        model = joblib.load(MODEL_PATH)
    except FileNotFoundError:
        print(f"[ERROR] Model file not found at {MODEL_PATH}. Please run train.py first.")
        return

    print(f"[INFO] Model type: {type(model).__name__}")

    # 2. Load data
    print(f"[INFO] Loading data from {DATA_PATH}...")
    try:
        df = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        print(f"[ERROR] Data file not found at {DATA_PATH}. Please run data_pipeline.py first.")
        return

    # 3. Preprocess to match the exact feature space the model was trained on
    print("[INFO] Preprocessing data to match training feature space...")
    X, feature_names = preprocess_for_shap(df)

    # 4. Sample rows for speed
    print("[INFO] Sampling up to 100 rows for SHAP computation...")
    X_sample = X.sample(n=min(100, len(X)), random_state=42)
    X_array = X_sample.values.astype(float)

    # 5. Get the raw XGBoost Booster and patch base_score if needed
    print("[INFO] Extracting booster...")
    booster = model.get_booster()
    patch_booster_base_score(booster)

    # 6. Initialize SHAP TreeExplainer on the booster
    print("[INFO] Initializing SHAP TreeExplainer...")
    explainer = shap.TreeExplainer(booster)

    # 7. Calculate SHAP values
    # For multiclass XGBoost, returns shape (n_samples, n_features, n_classes)
    print("[INFO] Calculating SHAP values...")
    shap_vals = explainer.shap_values(X_array)

    # 8. Generate summary plot
    print(f"[INFO] Generating summary plot at {OUTPUT_PLOT_PATH}...")
    plt.figure(figsize=(12, 8))

    if isinstance(shap_vals, np.ndarray) and shap_vals.ndim == 3:
        # Multiclass ndarray: (n_samples, n_features, n_classes)
        n_classes = shap_vals.shape[2]
        target_class_index = 2 if n_classes > 2 else n_classes - 1
        print(f"[INFO] Multiclass ({n_classes} classes) - plotting index {target_class_index} (High Risk).")
        shap.summary_plot(
            shap_vals[:, :, target_class_index],
            X_array,
            feature_names=feature_names,
            show=False,
        )
    elif isinstance(shap_vals, list):
        # Older SHAP versions return a list of per-class arrays
        n_classes = len(shap_vals)
        target_class_index = 2 if n_classes > 2 else n_classes - 1
        print(f"[INFO] Multiclass ({n_classes} classes) - plotting index {target_class_index} (High Risk).")
        shap.summary_plot(
            shap_vals[target_class_index],
            X_array,
            feature_names=feature_names,
            show=False,
        )
    else:
        shap.summary_plot(shap_vals, X_array, feature_names=feature_names, show=False)

    plt.tight_layout()
    os.makedirs(os.path.dirname(OUTPUT_PLOT_PATH), exist_ok=True)
    plt.savefig(OUTPUT_PLOT_PATH, bbox_inches="tight")
    plt.close()

    print(f"[SUCCESS] SHAP analysis complete. Plot saved to {OUTPUT_PLOT_PATH}")


if __name__ == "__main__":
    try:
        run_shap_analysis()
    except Exception as e:
        print(f"[ERROR] SHAP explainer failed: {e}")
        import traceback
        traceback.print_exc()
