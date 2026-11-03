from __future__ import annotations

import numpy as np
import pandas as pd
import shap
import streamlit as st

from src.config import Paths


def _align_features(ticket_features: pd.DataFrame) -> pd.DataFrame:
    feature_path = str(Paths.FEATURE_COLUMNS)
    if not feature_path:
        return ticket_features

    try:
        import joblib

        feature_columns = joblib.load(feature_path)
    except Exception:
        return ticket_features

    missing = [col for col in feature_columns if col not in ticket_features.columns]
    for col in missing:
        ticket_features[col] = 0

    extra = [col for col in ticket_features.columns if col not in feature_columns]
    if extra:
        ticket_features = ticket_features.drop(columns=extra)

    return ticket_features[feature_columns]


def _compute_top_drivers(ticket_features: pd.DataFrame, pipeline, top_n: int = 5) -> pd.DataFrame:
    """Compute top absolute SHAP drivers for one ticket row."""
    aligned_features = _align_features(ticket_features.copy())
    explainer = shap.TreeExplainer(pipeline)
    shap_values = explainer.shap_values(aligned_features)

    if isinstance(shap_values, list):
        shap_array = np.array(shap_values)
        if shap_array.ndim == 3:
            target_class = min(2, shap_array.shape[0] - 1)
            shap_abs = np.abs(shap_array[target_class]).flatten()
        else:
            shap_abs = np.abs(shap_array).flatten()
    else:
        shap_array = np.array(shap_values)
        if shap_array.ndim == 3:
            target_class = min(2, shap_array.shape[-1] - 1)
            shap_abs = np.abs(shap_array[0, :, target_class]).flatten()
        elif shap_array.ndim == 2:
            shap_abs = np.abs(shap_array[0]).flatten()
        else:
            shap_abs = np.abs(shap_array).flatten()

    feature_names = list(aligned_features.columns)
    rows = list(zip(feature_names, shap_abs))
    rows.sort(key=lambda item: item[1], reverse=True)
    top = rows[:top_n]

    total = sum(value for _, value in top) or 1.0
    return pd.DataFrame(
        {
            "Risk Driver": [feature.replace("_", " ").title() for feature, _ in top],
            "Influence (%)": [((value / total) * 100) for _, value in top],
            "Raw SHAP": [value for _, value in top],
        }
    )


def get_top_driver_names(ticket_features: pd.DataFrame, pipeline, top_n: int = 5) -> list[str]:
    """Return list of top SHAP driver names for prompt context."""
    table = _compute_top_drivers(ticket_features, pipeline, top_n=top_n)
    if table.empty:
        return []
    return table["Risk Driver"].tolist()


def render_shap_table(ticket_features: pd.DataFrame, pipeline) -> pd.DataFrame:
    """Render tabular local SHAP explanation and return the table."""
    st.subheader("Top Risk Drivers (Local SHAP)")
    df_shap = _compute_top_drivers(ticket_features, pipeline, top_n=5)

    if df_shap.empty:
        st.info("SHAP explanation not available for this model.")
        return df_shap

    st.dataframe(
        df_shap,
        column_config={
            "Risk Driver": st.column_config.TextColumn("Risk Driver", width="medium"),
            "Influence (%)": st.column_config.ProgressColumn(
                "Influence (%)",
                min_value=0,
                max_value=100,
                format="%d%%",
                width="medium",
            ),
            "Raw SHAP": st.column_config.NumberColumn("Raw SHAP", format="%.4f", width="small"),
        },
        hide_index=True,
        use_container_width=True,
    )
    return df_shap


def render_shap_force_plot(ticket_features: pd.DataFrame, pipeline) -> pd.DataFrame:
    """Render a lightweight force-plot-style horizontal bar chart."""
    st.subheader("Local SHAP Force View")
    df_shap = _compute_top_drivers(ticket_features, pipeline, top_n=8)
    if df_shap.empty:
        st.info("SHAP force view is not available for this model.")
        return df_shap

    chart_df = df_shap[["Risk Driver", "Influence (%)"]].copy()
    st.bar_chart(chart_df.set_index("Risk Driver"))
    st.caption("Approximate force-style ranking using normalized absolute SHAP impact.")
    return df_shap
