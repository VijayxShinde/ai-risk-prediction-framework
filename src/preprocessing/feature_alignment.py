from __future__ import annotations

import os
import re
from pathlib import Path

import joblib
import pandas as pd


from src.config import Paths

FEATURE_COLUMNS_PATH = str(Paths.FEATURE_COLUMNS)


def preprocess_row(ticket_row: pd.Series, dataset: pd.DataFrame) -> pd.DataFrame:
    TARGET_COL = "Risk_Level"

    X = pd.DataFrame([ticket_row.values], columns=ticket_row.index)

    original_dtypes = dataset.drop(columns=[TARGET_COL], errors="ignore").dtypes
    for col in X.columns:
        if col in original_dtypes.index:
            X[col] = X[col].astype(original_dtypes[col])

    X = X.drop(columns=["Actual_Days", "Cost_Consumed"], errors="ignore")
    X = X.drop(
        columns=["Summary", "Description", "Issue_ID", "Issue_key"], errors="ignore"
    )

    cat_cols = X.select_dtypes(include=["object", "category"]).columns
    if len(cat_cols) > 0:
        X = pd.get_dummies(X, columns=cat_cols)

    X.columns = [re.sub(r"[\[\]<]", "_", str(c)) for c in X.columns]

    if os.path.exists(FEATURE_COLUMNS_PATH):
        training_columns = joblib.load(FEATURE_COLUMNS_PATH)
        X = X.reindex(columns=training_columns, fill_value=0)

    return X