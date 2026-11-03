import joblib
import os
import sys
from pathlib import Path

import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Constants
DATA_PATH = "data/ml_ready_data.csv"
MODEL_DIR = "models/"
RF_MODEL_PATH = os.path.join(MODEL_DIR, "rf_model.pkl")
XGB_MODEL_PATH = os.path.join(MODEL_DIR, "xgb_model.pkl")


def load_and_prepare_data(path, use_tfidf=False, tfidf_max_features=20):
    print("[INFO] Loading data from {}...".format(path))
    df = pd.read_csv(path)

    from src.preprocessing.feature_engineering import prepare_training_data

    return prepare_training_data(
        df,
        verbose=True,
        use_tfidf=use_tfidf,
        tfidf_max_features=tfidf_max_features,
    )


def train_and_evaluate(
    use_smote=False,
    use_tfidf=False,
    tfidf_max_features=20,
    save_models=True,
):
    X, y = load_and_prepare_data(
        DATA_PATH,
        use_tfidf=use_tfidf,
        tfidf_max_features=tfidf_max_features,
    )

    global_mean = y.value_counts(normalize=True).sort_index().mean()
    print(f"[INFO] Class distribution: {y.value_counts().to_dict()}, global mean: {global_mean:.4f}")

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print("[INFO] Data split into 80% train and 20% test sets.")

    sample_weights = None
    rf_class_weight = "balanced"
    if use_smote:
        smote = SMOTE(random_state=42, sampling_strategy="auto")
        X_train, y_train = smote.fit_resample(X_train, y_train)
        print(f"[INFO] Post-SMOTE class distribution: {y_train.value_counts().to_dict()}")
        rf_class_weight = None
    else:
        sample_weights = compute_sample_weight(class_weight="balanced", y=y_train)

    models = {
        "RandomForest": RandomForestClassifier(
            n_estimators=300,
            max_depth=15,
            min_samples_leaf=3,
            class_weight=rf_class_weight,
            n_jobs=-1,
            random_state=42,
        ),
        "XGBoost": XGBClassifier(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.05,
            min_child_weight=3,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.5,
            reg_lambda=2.0,
            eval_metric="mlogloss",
            early_stopping_rounds=30,
            random_state=42,
            n_jobs=-1,
        ),
    }

    results = {}

    for name, model in models.items():
        print(f"\n[INFO] Training {name} Classifier...")

        if name == "XGBoost":
            model.fit(
                X_train,
                y_train,
                sample_weight=sample_weights,
                eval_set=[(X_val, y_val)],
                verbose=False,
            )
        else:
            model.fit(X_train, y_train)

        preds = model.predict(X_val)
        acc = accuracy_score(y_val, preds)
        report = classification_report(
            y_val, preds, target_names=["Low", "Medium", "High"], output_dict=True
        )
        macro_f1 = report["macro avg"]["f1-score"]

        print(f"--- {name} Results (validation set) ---")
        print(f"Accuracy: {acc:.4f}")
        print(
            classification_report(
                y_val, preds, target_names=["Low", "Medium", "High"]
            )
        )

        if name == "XGBoost":
            print(f"Best iteration: {model.best_iteration}")

        results[name] = {
            "model": model,
            "accuracy": acc,
            "macro_f1": macro_f1,
        }

    if save_models:
        print("\n[INFO] Saving trained models to {}...".format(MODEL_DIR))
        joblib.dump(results["RandomForest"]["model"], RF_MODEL_PATH)
        joblib.dump(results["XGBoost"]["model"], XGB_MODEL_PATH)
        print(f"[SUCCESS] Saved: {RF_MODEL_PATH} and {XGB_MODEL_PATH}")

        FEATURE_COLUMNS_PATH = os.path.join(MODEL_DIR, "feature_columns.pkl")
        joblib.dump(list(X.columns), FEATURE_COLUMNS_PATH)
        print(f"[SUCCESS] Saved feature column names to {FEATURE_COLUMNS_PATH}")
        print(f"[INFO] Training feature columns ({len(X.columns)}): {list(X.columns)}")

    return results, list(X.columns)


def run_ablation_study():
    configs = [
        {"name": "baseline_no_smote_no_tfidf", "use_smote": False, "use_tfidf": False},
        {"name": "smote_only", "use_smote": True, "use_tfidf": False},
        {"name": "tfidf_20_only", "use_smote": False, "use_tfidf": True, "tfidf_max_features": 20},
        {"name": "smote_tfidf_20", "use_smote": True, "use_tfidf": True, "tfidf_max_features": 20},
        {"name": "tfidf_150_only", "use_smote": False, "use_tfidf": True, "tfidf_max_features": 150},
        {"name": "smote_tfidf_150", "use_smote": True, "use_tfidf": True, "tfidf_max_features": 150},
    ]

    results = []
    for cfg in configs:
        print("\n" + "=" * 80)
        print(f"[ABLAT] Running {cfg['name']}")
        cfg_results, _ = train_and_evaluate(
            use_smote=cfg.get("use_smote", False),
            use_tfidf=cfg.get("use_tfidf", False),
            tfidf_max_features=cfg.get("tfidf_max_features", 20),
            save_models=False,
        )
        xgb_metrics = cfg_results["XGBoost"]
        rf_metrics = cfg_results["RandomForest"]
        results.append(
            {
                "config": cfg,
                "xgb_macro_f1": xgb_metrics["macro_f1"],
                "xgb_accuracy": xgb_metrics["accuracy"],
                "rf_macro_f1": rf_metrics["macro_f1"],
                "rf_accuracy": rf_metrics["accuracy"],
            }
        )

    best = max(
        results,
        key=lambda item: (item["xgb_macro_f1"], item["xgb_accuracy"]),
    )
    best_cfg = best["config"]
    print("\n" + "=" * 80)
    print("[ABLAT] Best configuration selected:")
    print(
        f"[ABLAT] {best_cfg['name']} | "
        f"xgb_macro_f1={best['xgb_macro_f1']:.4f}, "
        f"xgb_accuracy={best['xgb_accuracy']:.4f}"
    )

    print("\n[ABLAT] Re-training best configuration and saving artifacts...")
    train_and_evaluate(
        use_smote=best_cfg.get("use_smote", False),
        use_tfidf=best_cfg.get("use_tfidf", False),
        tfidf_max_features=best_cfg.get("tfidf_max_features", 20),
        save_models=True,
    )

    return best


if __name__ == "__main__":
    try:
        run_ablation_study()
        print("\n[SUCCESS] Training pipeline completed successfully.")
    except Exception as e:
        print(f"\n[ERROR] Training failed: {e}")
