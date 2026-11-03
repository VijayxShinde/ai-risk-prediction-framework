"""
Anomaly Detection Engine for RiskAI Framework

This module implements an unsupervised anomaly detection system using Isolation Forest
to identify unusual patterns in project management data.
"""

import logging
import os
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import joblib


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s"
        )
    )
    logger.addHandler(console_handler)
    logger.propagate = False


class AnomalyEngine:
    """
    Anomaly Detection Engine using Isolation Forest algorithm.

    Isolation Forest detects anomalies by randomly partitioning data. Anomalies are
    isolated closer to the tree root (fewer splits) than normal points. The
    anomaly score is the average path length across all trees, normalized by
    expected path length for a uniform distribution.

    Example:
        engine = AnomalyEngine(contamination=0.05)
        results = engine.detect_anomalies(data, ['burn_rate', 'velocity_delta'])
    """

    def __init__(self, contamination: float = 0.05):
        """
        Initialize the AnomalyEngine.

        Args:
            contamination: Expected proportion of anomalies in the dataset (0.01-0.15)
        """
        if not 0.01 <= contamination <= 0.15:
            raise ValueError("contamination must be between 0.01 and 0.15")

        self.contamination = contamination
        self.isolation_forest = IsolationForest(
            contamination=contamination, random_state=42, n_estimators=100
        )
        self.scaler = StandardScaler()
        self.imputer = SimpleImputer(strategy="median")
        logger.info(f"AnomalyEngine initialized with contamination={contamination}")

    def _calculate_feature_contributions(
        self, data: pd.DataFrame, anomalies: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate feature contributions for detected anomalies using z-scores.

        For each anomaly, identifies which features deviated most from normal behavior
        by calculating z-scores: z = (value - mean) / std.

        Args:
            data: Original data with all features
            anomalies: DataFrame with detected anomalies

        Returns:
            DataFrame with feature_contributions column added
        """
        # Calculate mean and std for each feature
        feature_stats = {}
        for col in data.columns:
            if data[col].dtype in [np.float64, np.int64]:
                feature_stats[col] = {"mean": data[col].mean(), "std": data[col].std()}

        # Calculate contributions for each row
        contributions = []
        for idx, row in anomalies.iterrows():
            if row["is_anomaly"]:
                # Calculate z-scores for all features
                z_scores = {}
                for col, stats in feature_stats.items():
                    if stats["std"] > 0:  # Avoid division by zero
                        z_score = (row[col] - stats["mean"]) / stats["std"]
                        z_scores[col] = abs(z_score)

                # Get top 3 contributing features
                sorted_features = sorted(
                    z_scores.items(), key=lambda x: x[1], reverse=True
                )[:3]
                contrib_str = ", ".join(
                    [f"{feat}:{score:.2f}" for feat, score in sorted_features]
                )
                contributions.append(contrib_str)
            else:
                contributions.append("None")

        anomalies["feature_contributions"] = contributions
        return anomalies

    def detect_anomalies(
        self,
        data: pd.DataFrame,
        feature_columns: List[str],
        contamination: Optional[float] = None,
    ) -> pd.DataFrame:
        """
        Detect anomalies in the provided dataset using Isolation Forest.

        Args:
            data: DataFrame containing project data
            feature_columns: List of numerical columns to analyze
            contamination: Expected proportion of anomalies (0.01-0.15)

        Returns:
            DataFrame with original data plus is_anomaly, anomaly_score, severity columns

        Raises:
            ValueError: If data validation fails
            Exception: If model fitting fails
        """
        start_time = time.perf_counter()

        # Use instance contamination if not overridden
        if contamination is None:
            contamination = self.contamination

        # Validate inputs
        if not 0.01 <= contamination <= 0.15:
            raise ValueError("contamination must be between 0.01 and 0.15")

        # Re-initialize model if contamination differs from default
        if contamination != self.contamination:
            self.isolation_forest = IsolationForest(
                contamination=contamination, random_state=42, n_estimators=100
            )

        if len(data) < 100:
            raise ValueError(
                "Insufficient data for Isolation Forest (minimum 100 rows required)"
            )

        missing_cols = set(feature_columns) - set(data.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Check that feature columns are numeric
        for col in feature_columns:
            if data[col].dtype not in [np.float64, np.int64]:
                raise ValueError(f"Feature column '{col}' must be numeric")

        # Filter to only the specified features
        feature_data = data[feature_columns].copy()

        # Preprocessing: Handle missing values and scale
        try:
            # Impute missing values
            feature_data_imputed = self.imputer.fit_transform(feature_data)
            feature_data_imputed = pd.DataFrame(
                feature_data_imputed, columns=feature_columns, index=data.index
            )

            # Scale features
            feature_data_scaled = self.scaler.fit_transform(feature_data_imputed)
            feature_data_scaled = pd.DataFrame(
                feature_data_scaled, columns=feature_columns, index=data.index
            )

            logger.info(
                f"Starting anomaly detection on {len(data)} rows with {len(feature_columns)} features"
            )

            # Fit the model and predict
            self.isolation_forest.fit(feature_data_scaled)
            predictions = self.isolation_forest.predict(feature_data_scaled)
            scores = self.isolation_forest.decision_function(feature_data_scaled)

            # Add results to original data
            result_data = data.copy()
            result_data["is_anomaly"] = predictions == -1  # -1 indicates anomaly
            result_data["anomaly_score"] = scores

            # Add severity classification
            result_data["severity"] = pd.cut(
                result_data["anomaly_score"],
                bins=[-np.inf, -0.5, -0.2, 0, np.inf],
                labels=["High", "Medium", "Low", "Normal"],
            )

            # Calculate feature contributions for anomalies
            result_data = self._calculate_feature_contributions(
                feature_data_imputed, result_data
            )

            # Calculate processing time
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            anomaly_count = sum(result_data["is_anomaly"])
            anomaly_pct = (anomaly_count / len(result_data)) * 100

            logger.info(
                f"Detected {anomaly_count} anomalies ({anomaly_pct:.2f}%) in {duration_ms:.2f}ms"
            )

            if duration_ms > 500:
                logger.warning(
                    f"Processing time {duration_ms:.2f}ms exceeds 500ms threshold"
                )

            return result_data

        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}", exc_info=True)
            raise Exception(f"Isolation Forest fitting failed: {str(e)}")

    def save_model(self, filepath: str = "models/isolation_forest.pkl") -> None:
        """
        Save the fitted model and scaler to a pickle file.

        Args:
            filepath: Path to save the model
        """
        model_data = {
            "model": self.isolation_forest,
            "scaler": self.scaler,
            "metadata": {
                "fit_date": datetime.now().isoformat(),
                "contamination": self.contamination,
                "features": list(self.isolation_forest.feature_names_in_)
                if hasattr(self.isolation_forest, "feature_names_in_")
                else [],
            },
        }

        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")


# Example usage
if __name__ == "__main__":
    # This would be used for testing
    pass
