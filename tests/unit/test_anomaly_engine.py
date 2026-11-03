"""Unit tests for AnomalyEngine."""

import numpy as np
import pandas as pd
import pytest

from src.anomaly import AnomalyEngine

pytestmark = pytest.mark.unit


@pytest.fixture
def sample_data():
    np.random.seed(42)
    n_samples = 200
    data = {
        "burn_rate": np.random.normal(1.2, 0.3, n_samples),
        "velocity_delta": np.random.normal(0, 0.5, n_samples),
        "schedule_variance": np.random.normal(0, 2, n_samples),
        "scope_creep_rate": np.random.normal(0.1, 0.05, n_samples),
        "blocker_count": np.random.poisson(0.5, n_samples).astype(float),
        "comment_sentiment": np.random.normal(0.1, 0.3, n_samples).astype(float),
    }
    anomaly_indices = np.random.choice(n_samples, size=int(n_samples * 0.05), replace=False)
    for idx in anomaly_indices:
        data["burn_rate"][idx] = np.random.normal(4, 0.5)
    return pd.DataFrame(data)


@pytest.fixture
def feature_columns():
    return [
        "burn_rate",
        "velocity_delta",
        "schedule_variance",
        "scope_creep_rate",
        "blocker_count",
        "comment_sentiment",
    ]


def test_anomaly_engine_initialization():
    engine = AnomalyEngine(contamination=0.05)
    assert engine.contamination == 0.05


def test_anomaly_detection_output_schema(sample_data, feature_columns):
    engine = AnomalyEngine(contamination=0.05)
    results = engine.detect_anomalies(data=sample_data, feature_columns=feature_columns, contamination=0.05)

    required_columns = ["is_anomaly", "anomaly_score", "severity", "feature_contributions"]
    for col in required_columns:
        assert col in results.columns, f"Missing required column: {col}"

    assert len(results) == len(sample_data)


def test_anomaly_detection_finds_anomalies(sample_data, feature_columns):
    engine = AnomalyEngine(contamination=0.05)
    results = engine.detect_anomalies(data=sample_data, feature_columns=feature_columns, contamination=0.05)

    assert results["is_anomaly"].sum() > 0, "Expected at least some anomalies"


def test_anomaly_score_range(sample_data, feature_columns):
    engine = AnomalyEngine(contamination=0.05)
    results = engine.detect_anomalies(data=sample_data, feature_columns=feature_columns, contamination=0.05)

    assert results["anomaly_score"].notna().all()
    assert results["anomaly_score"].min() >= -1.0, "Anomaly scores should be >= ~-1 for IsolationForest"
    assert results["anomaly_score"].max() <= 1.0, "Anomaly scores should be <= ~1 for IsolationForest"


def test_severity_levels_valid(sample_data, feature_columns):
    engine = AnomalyEngine(contamination=0.05)
    results = engine.detect_anomalies(data=sample_data, feature_columns=feature_columns, contamination=0.05)

    valid_severities = {"High", "Medium", "Low", "Normal"}
    assert set(results["severity"].unique()).issubset(valid_severities)


def test_empty_data_handled():
    engine = AnomalyEngine(contamination=0.05)
    empty_df = pd.DataFrame()
    with pytest.raises(ValueError):
        engine.detect_anomalies(data=empty_df, feature_columns=[], contamination=0.05)


def test_save_and_load_model(sample_data, feature_columns, tmp_path):
    engine = AnomalyEngine(contamination=0.05)
    engine.detect_anomalies(data=sample_data, feature_columns=feature_columns, contamination=0.05)

    save_path = tmp_path / "test_isolation_forest.pkl"
    engine.save_model(str(save_path))
    assert save_path.exists()