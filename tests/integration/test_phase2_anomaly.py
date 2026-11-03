import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score

from src.anomaly import AnomalyEngine


def _prepare_features() -> pd.DataFrame:
    df = pd.read_csv("data/ml_ready_data.csv")
    df["budget_overrun_pct"] = (
        (df["Cost_Consumed"] - df["Budget_Allocated"]) / df["Budget_Allocated"] * 100
    )
    df["days_overrun_pct"] = (
        (df["Actual_Days"] - df["Estimated_Days"]) / df["Estimated_Days"] * 100
    )
    df["efficiency_score"] = df["Estimated_Days"] / df["Actual_Days"]
    df["cost_efficiency"] = df["Budget_Allocated"] / df["Cost_Consumed"]

    feature_columns = [
        "Story_Points",
        "Estimated_Days",
        "Actual_Days",
        "Budget_Allocated",
        "Cost_Consumed",
        "budget_overrun_pct",
        "days_overrun_pct",
        "efficiency_score",
        "cost_efficiency",
    ]
    return df[feature_columns].replace([np.inf, -np.inf], np.nan).dropna().copy()


@pytest.mark.integration
def test_phase2_anomaly_detection_outputs() -> None:
    features_df = _prepare_features()
    feature_columns = list(features_df.columns)

    engine = AnomalyEngine(contamination=0.05)
    results = engine.detect_anomalies(features_df, feature_columns)

    assert len(results) == len(features_df)
    assert "is_anomaly" in results.columns
    assert "anomaly_score" in results.columns
    assert "severity" in results.columns
    assert "feature_contributions" in results.columns


@pytest.mark.integration
@pytest.mark.slow
def test_phase2_anomaly_roc_auc_target() -> None:
    """Validate ROC-AUC of Isolation Forest against engineered ground-truth labels.

    Note: Labels are derived from the same domain data as the features
    (cost overrun > 30%). This is an integration smoke test for the
    anomaly pipeline, not a blind evaluation. For independent ground truth,
    use data/curated_anomalies.csv.
    """
    df = pd.read_csv("data/ml_ready_data.csv")
    features_df = _prepare_features()
    feature_columns = list(features_df.columns)

    df = df.loc[features_df.index]
    # Dynamically generate 'is_true_anomaly' using the same heuristic
    df["is_true_anomaly"] = ((df["Cost_Consumed"] / df["Budget_Allocated"]) - 1) > 0.30
    
    y_true = df["is_true_anomaly"].astype(int).to_numpy()

    engine = AnomalyEngine(contamination=0.03)
    results = engine.detect_anomalies(features_df, feature_columns)
    anomaly_scores = -results["anomaly_score"].to_numpy()

    roc_auc = roc_auc_score(y_true, anomaly_scores)
    assert roc_auc >= 0.75, (
        f"ROC-AUC {roc_auc:.4f} fell below the 0.75 minimum for ground-truth "
        "validation. Consider re-tuning contamination or feature engineering."
    )
