"""Reusable UI components for What-If scenario comparison."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from app.components.shap_visuals import render_shap_force_plot, render_shap_table


def render_delta_metrics(comparison: dict[str, Any]) -> None:
    """Render top-level delta metrics and driver-change badges."""
    delta = comparison["delta"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "High Risk Change",
        f"{delta['high_risk_pct_change']:+.1f}%",
        delta_color="inverse",
    )
    c2.metric("Confidence Change", f"{delta['confidence_pct_change']:+.1f}%")
    c3.metric("Budget Delta", f"${delta['budget_delta']:+,.0f}", delta_color="inverse")
    c4.metric("Timeline Delta", f"{delta['timeline_delta']:+.1f} days")

    if delta["new_drivers"]:
        st.warning("New risk drivers: " + ", ".join(delta["new_drivers"][:3]))
    if delta["mitigated_drivers"]:
        st.success("Mitigated drivers: " + ", ".join(delta["mitigated_drivers"][:3]))


def render_scenario_panels(comparison: dict[str, Any], model) -> None:
    """Render original vs simulated scenario cards and SHAP sections."""
    left, right = st.columns([11, 9])

    with left:
        st.markdown("### Original Scenario")
        st.metric("Risk", comparison["original"]["risk_label"])
        st.metric("High-Risk Probability", f"{comparison['original']['high_risk_pct']:.1f}%")
        st.metric("Confidence", f"{comparison['original']['confidence_pct']:.1f}%")
        st.caption("Top Drivers: " + ", ".join(comparison["original"]["top_drivers"][:5]))

        view_mode = st.radio(
            "Original SHAP View",
            options=["Table", "Force"],
            horizontal=True,
            key="what_if_original_shap",
        )
        if view_mode == "Force":
            render_shap_force_plot(comparison["artifacts"]["original_features"], model)
        else:
            render_shap_table(comparison["artifacts"]["original_features"], model)

    with right:
        st.markdown("### Simulated Scenario")
        st.metric("Risk", comparison["simulated"]["risk_label"])
        st.metric(
            "High-Risk Probability",
            f"{comparison['simulated']['high_risk_pct']:.1f}%",
            f"{comparison['delta']['high_risk_pct_change']:+.1f}%",
            delta_color="inverse",
        )
        st.metric(
            "Confidence",
            f"{comparison['simulated']['confidence_pct']:.1f}%",
            f"{comparison['delta']['confidence_pct_change']:+.1f}%",
        )
        st.caption("Top Drivers: " + ", ".join(comparison["simulated"]["top_drivers"][:5]))

        view_mode_sim = st.radio(
            "Simulated SHAP View",
            options=["Table", "Force"],
            horizontal=True,
            key="what_if_sim_shap",
        )
        if view_mode_sim == "Force":
            render_shap_force_plot(comparison["artifacts"]["simulated_features"], model)
        else:
            render_shap_table(comparison["artifacts"]["simulated_features"], model)


def safe_float(val, default=0.0) -> float:
    """Safely convert value to float, defaulting on NaN/None/empty string."""
    if pd.isna(val) or val is None or val == "":
        return default
    try:
        import numpy as np
        f_val = float(val)
        if np.isnan(f_val):
            return default
        return f_val
    except (ValueError, TypeError):
        return default


def render_input_metrics(simulated_row: pd.Series, comparison: dict[str, Any]) -> None:
    """Render input-level before/after highlights."""
    st.markdown("### Baseline vs Simulated Inputs")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(
        "Estimated Days",
        f"{safe_float(simulated_row.get('Estimated_Days')):.2f}",
        f"{safe_float(comparison['delta']['timeline_delta']):+.2f}",
    )
    m2.metric(
        "Budget",
        f"${safe_float(simulated_row.get('Budget_Allocated')):,.0f}",
        f"${safe_float(comparison['delta']['budget_delta']):+,.0f}",
        delta_color="inverse",
    )
    m3.metric("Story Points", f"{safe_float(simulated_row.get('Story_Points')):.2f}")
    m4.metric("Priority", f"{simulated_row.get('Priority', 'N/A')}")


def render_scenario_export(
    comparison: dict[str, Any],
    baseline_row: pd.Series,
    simulated_row: pd.Series,
) -> None:
    """Render simple CSV export (original vs simulated + deltas)."""
    original = comparison["original"]
    simulated = comparison["simulated"]
    delta = comparison["delta"]

    export_df = pd.DataFrame(
        {
            "Metric": [
                "Risk Label",
                "High Risk (%)",
                "Confidence (%)",
                "Estimated Days",
                "Budget Allocated",
                "Story Points",
                "Priority",
                "Assignee Seniority",
            ],
            "Original": [
                original["risk_label"],
                f"{safe_float(original['high_risk_pct']):.2f}",
                f"{safe_float(original['confidence_pct']):.2f}",
                f"{safe_float(baseline_row.get('Estimated_Days')):.2f}",
                f"{safe_float(baseline_row.get('Budget_Allocated')):.2f}",
                f"{safe_float(baseline_row.get('Story_Points')):.2f}",
                str(baseline_row.get("Priority", "N/A")),
                str(baseline_row.get("Assignee_Seniority", "N/A")),
            ],
            "Simulated": [
                simulated["risk_label"],
                f"{safe_float(simulated['high_risk_pct']):.2f}",
                f"{safe_float(simulated['confidence_pct']):.2f}",
                f"{safe_float(simulated_row.get('Estimated_Days')):.2f}",
                f"{safe_float(simulated_row.get('Budget_Allocated')):.2f}",
                f"{safe_float(simulated_row.get('Story_Points')):.2f}",
                str(simulated_row.get("Priority", "N/A")),
                str(simulated_row.get("Assignee_Seniority", "N/A")),
            ],
            "Delta": [
                "",
                f"{safe_float(delta['high_risk_pct_change']):+.2f}",
                f"{safe_float(delta['confidence_pct_change']):+.2f}",
                f"{safe_float(delta['timeline_delta']):+.2f}",
                f"{safe_float(delta['budget_delta']):+.2f}",
                f"{safe_float(simulated_row.get('Story_Points')) - safe_float(baseline_row.get('Story_Points')):+.2f}",
                "" if baseline_row.get("Priority") == simulated_row.get("Priority") else f"{baseline_row.get('Priority')} -> {simulated_row.get('Priority')}",
                "" if baseline_row.get("Assignee_Seniority") == simulated_row.get("Assignee_Seniority") else f"{baseline_row.get('Assignee_Seniority')} -> {simulated_row.get('Assignee_Seniority')}",
            ],
        }
    )

    st.download_button(
        "Download Scenario Comparison (CSV)",
        data=export_df.to_csv(index=False).encode("utf-8"),
        file_name="what_if_scenario_comparison.csv",
        mime="text/csv",
        use_container_width=True,
    )
