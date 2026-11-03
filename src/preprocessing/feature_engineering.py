"""Canonical feature preprocessing shared by training, SHAP, and prediction paths."""

from __future__ import annotations

import re
from typing import Dict, Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


TARGET_COL = "Risk_Level"
RISK_MAP: Dict[str, int] = {"Low": 0, "Medium": 1, "High": 2}
LEAKAGE_COLS: list[str] = ["Actual_Days", "Cost_Consumed"]
TEXT_ID_COLS: list[str] = [
    "Summary",
    "Description",
    "Developer_Comments",
    "Issue_ID",
    "Issue_key",
]
MAX_CATEGORY_UNIQUE: int = 15


def _map_risk_label(series: pd.Series) -> pd.Series:
    if series.dtype == object:
        return series.map(RISK_MAP)
    return series


def _add_engineered_features(
    df: pd.DataFrame,
    use_tfidf: bool = False,
    tfidf_max_features: int = 20,
) -> pd.DataFrame:
    X = df.drop(columns=[TARGET_COL], errors="ignore").copy()

    if "Budget_Allocated" in X.columns and "Estimated_Days" in X.columns:
        estimated = X["Estimated_Days"].replace(0, 1)
        X["budget_per_day"] = (X["Budget_Allocated"] / estimated).replace([np.inf, -np.inf], 0).clip(0, 1e6)

    if "Story_Points" in X.columns and "Estimated_Days" in X.columns:
        estimated = X["Estimated_Days"].replace(0, 1)
        X["sp_density"] = (X["Story_Points"] / estimated).replace([np.inf, -np.inf], 0).clip(0, 1e6)

    if "Story_Points" in X.columns:
        X["is_large_story"] = (X["Story_Points"] > 8).astype(int)

    if "Description" in X.columns:
        X["description_length"] = X["Description"].fillna("").astype(str).str.split().str.len()

    if "Developer_Comments" in X.columns:
        X["comment_count"] = X["Developer_Comments"].fillna("").astype(str).str.count(r"\S+")

    if use_tfidf:
        text_columns = [col for col in ("Summary", "Description") if col in df.columns]
        if text_columns:
            combined_text = df[text_columns[0]].fillna("").astype(str)
            if len(text_columns) > 1:
                combined_text = combined_text + " " + df[text_columns[1]].fillna("").astype(str)

            tfidf = TfidfVectorizer(
                max_features=tfidf_max_features,
                stop_words="english",
                min_df=2,
                max_df=0.9,
            )
            try:
                tfidf_matrix = tfidf.fit_transform(combined_text)
                tfidf_df = pd.DataFrame(
                    tfidf_matrix.toarray(),
                    columns=[f"tfidf_{i}" for i in range(tfidf_matrix.shape[1])],
                    index=X.index,
                )
                X = pd.concat([X, tfidf_df], axis=1)
            except ValueError:
                pass

    return X


def preprocess_features(
    df: pd.DataFrame,
    feature_columns_path: Optional[str] = None,
    verbose: bool = False,
    seed: Optional[int] = None,
    use_tfidf: bool = False,
    tfidf_max_features: int = 20,
) -> pd.DataFrame:
    X = _add_engineered_features(df, use_tfidf=use_tfidf, tfidf_max_features=tfidf_max_features)

    X = X.drop(columns=[c for c in LEAKAGE_COLS if c in X.columns], errors="ignore")

    text_to_drop = [c for c in TEXT_ID_COLS if c in X.columns]
    X = X.drop(columns=text_to_drop)

    categorical_cols = X.select_dtypes(include=["object", "category"]).columns
    to_encode, to_drop = [], []
    for col in categorical_cols:
        (to_encode if X[col].nunique() <= MAX_CATEGORY_UNIQUE else to_drop).append(col)

    if to_drop:
        if verbose:
            print(f"[INFO] Dropping high-cardinality columns: {to_drop}")
        X = X.drop(columns=to_drop)

    if to_encode:
        if verbose:
            print(f"[INFO] One-hot encoding columns: {to_encode}")
        X = pd.get_dummies(X, columns=to_encode)

    X.columns = [re.sub(r"[\[\]<]", "_", str(c)) for c in X.columns]

    if seed is not None:
        np.random.seed(seed)

    return X


def prepare_training_data(
    df: pd.DataFrame,
    feature_columns_path: Optional[str] = None,
    verbose: bool = False,
    seed: int = 42,
    use_tfidf: bool = False,
    tfidf_max_features: int = 20,
) -> tuple[pd.DataFrame, pd.Series]:
    y = df[TARGET_COL].copy()
    y = _map_risk_label(y)

    X = preprocess_features(
        df,
        feature_columns_path=feature_columns_path,
        verbose=verbose,
        seed=seed,
        use_tfidf=use_tfidf,
        tfidf_max_features=tfidf_max_features,
    )

    return X, y
