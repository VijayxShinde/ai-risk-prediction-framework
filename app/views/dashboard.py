"""Dashboard views with minimalist layout."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.metrics import roc_auc_score

from app.utils.routes import AUDITOR_PAGE, switch_page_safe
from app.utils.styles import render_page_header, render_section_header, render_top_bar
from src.anomaly.anomaly_detector import AnomalyEngine
from src.forecasting.forecast import ProjectForecaster


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "ml_ready_data.csv"
FORECAST_FIG_PATH = PROJECT_ROOT / "reports" / "fig_phase2_a_prophet_forecast.png"
SEVERITY_FIG_PATH = PROJECT_ROOT / "reports" / "fig_phase2_b_severity_dist.png"
FEATURE_COLUMNS = [
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


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("dashboard")
    if logger.handlers:
        return logger

    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "dashboard_audit.log")
    formatter = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    file_handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


LOGGER = _setup_logger()


def _prepare_anomaly_features(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    frame["budget_overrun_pct"] = (
        (frame["Cost_Consumed"] - frame["Budget_Allocated"]) / frame["Budget_Allocated"] * 100
    )
    frame["days_overrun_pct"] = (
        (frame["Actual_Days"] - frame["Estimated_Days"]) / frame["Estimated_Days"] * 100
    )
    frame["efficiency_score"] = frame["Estimated_Days"] / frame["Actual_Days"]
    frame["cost_efficiency"] = frame["Budget_Allocated"] / frame["Cost_Consumed"]
    frame = frame.replace([np.inf, -np.inf], np.nan)
    frame = frame.dropna(subset=FEATURE_COLUMNS).copy()
    return frame


def _infer_alert_name(contribution: str) -> str:
    mapping = {
        "budget_overrun_pct": "Budget Overrun",
        "days_overrun_pct": "Schedule Overrun",
        "efficiency_score": "Efficiency Drop",
        "cost_efficiency": "Cost Efficiency Decline",
        "Actual_Days": "Duration Spike",
        "Cost_Consumed": "Cost Spike",
    }
    if not contribution or contribution == "None":
        return "General Risk Pattern"

    top_feature = contribution.split(",", 1)[0].split(":", 1)[0].strip()
    return mapping.get(top_feature, "General Risk Pattern")


def _build_alerts_table(anomaly_results: pd.DataFrame) -> pd.DataFrame:
    if anomaly_results.empty:
        return pd.DataFrame(columns=["timestamp", "ticket", "alert", "severity", "status"])

    severity_rank = {"High": 3, "Medium": 2, "Low": 1, "Normal": 0}
    df_anom = pd.DataFrame(anomaly_results.loc[anomaly_results["is_anomaly"]])

    if df_anom.empty:
        return pd.DataFrame(columns=["timestamp", "ticket", "alert", "severity", "status"])

    df_anom["anomaly_intensity"] = -df_anom["anomaly_score"]
    df_anom["severity_rank"] = df_anom["severity"].astype(str).map(severity_rank).fillna(0)
    df_top = df_anom.sort_values(by=["severity_rank", "anomaly_intensity"], ascending=[False, False]).head(5)

    now_ts = pd.Timestamp.utcnow().floor("s")
    alerts = []
    for idx, row in df_top.iterrows():
        idx_int = cast(int, idx)
        synthetic_ts = now_ts - pd.to_timedelta(idx_int, unit="m")
        alerts.append(
            {
                "timestamp": synthetic_ts.strftime("%Y-%m-%d %H:%M:%S"),
                "ticket": f"{str(row.get('Risk_Level', 'UNKNOWN')).upper()}-{idx_int:05d}",
                "alert": _infer_alert_name(row.get("feature_contributions", "None")),
                "severity": str(row["severity"]),
                "status": "Open",
            }
        )

    return pd.DataFrame(alerts)


def _build_shap_proxy_table(anomaly_results: pd.DataFrame) -> pd.DataFrame:
    if anomaly_results.empty or "feature_contributions" not in anomaly_results.columns:
        return pd.DataFrame(columns=["Feature", "Influence"])

    anomalies = anomaly_results[anomaly_results["is_anomaly"]].copy()
    if anomalies.empty:
        return pd.DataFrame(columns=["Feature", "Influence"])

    friendly_names = {
        "budget_overrun_pct": "Budget Overrun %",
        "days_overrun_pct": "Schedule Overrun %",
        "efficiency_score": "Delivery Efficiency",
        "cost_efficiency": "Cost Efficiency",
        "Actual_Days": "Actual Days",
        "Estimated_Days": "Estimated Days",
        "Cost_Consumed": "Cost Consumed",
        "Budget_Allocated": "Budget Allocated",
        "Story_Points": "Story Points",
    }

    contribution_totals: dict[str, float] = {}
    for raw in anomalies["feature_contributions"].astype(str).tolist():
        if not raw or raw == "None":
            continue
        for segment in raw.split(","):
            parts = segment.split(":", 1)
            if len(parts) != 2:
                continue
            feature = parts[0].strip()
            try:
                magnitude = float(parts[1].strip())
            except ValueError:
                continue
            contribution_totals[feature] = contribution_totals.get(feature, 0.0) + abs(magnitude)

    if not contribution_totals:
        return pd.DataFrame(columns=["Feature", "Influence"])

    total = sum(contribution_totals.values()) or 1.0
    rows = []
    for feature, magnitude in sorted(
        contribution_totals.items(), key=lambda item: item[1], reverse=True
    )[:5]:
        rows.append(
            {
                "Feature": friendly_names.get(feature, feature),
                "Influence": f"{(magnitude / total) * 100:.1f}%",
            }
        )
    return pd.DataFrame(rows)


def _render_interactive_forecast_chart(forecast_df: pd.DataFrame | None, forecast_horizon: int) -> None:
    if forecast_df is None or forecast_df.empty:
        st.warning("Forecast output is not available for the current settings.")
        return

    chart_df = forecast_df.copy()
    chart_df["ds"] = pd.to_datetime(chart_df["ds"], errors="coerce")
    chart_df = chart_df.dropna(subset=["ds"]).sort_values("ds")

    if chart_df.empty:
        st.warning("Forecast output is not available for the current settings.")
        return

    future_points = min(forecast_horizon, len(chart_df))
    history_df = chart_df.iloc[:-future_points].tail(max(60, forecast_horizon * 4)).copy()
    future_df = chart_df.tail(future_points).copy()

    fig = go.Figure()

    if not history_df.empty:
        fig.add_trace(
            go.Scatter(
                x=history_df["ds"],
                y=history_df["yhat"],
                mode="lines",
                name="Trend Baseline",
                line={"color": "#7a7a7a", "width": 2},
            )
        )

    fig.add_trace(
        go.Scatter(
            x=future_df["ds"],
            y=future_df["yhat"],
            mode="lines",
            name="Forecast",
            line={"color": "#4f46e5", "width": 3},
        )
    )

    fig.add_trace(
        go.Scatter(
            x=future_df["ds"],
            y=future_df["yhat_upper"],
            mode="lines",
            line={"width": 0},
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=future_df["ds"],
            y=future_df["yhat_lower"],
            mode="lines",
            line={"width": 0},
            fill="tonexty",
            fillcolor="rgba(79, 70, 229, 0.18)",
            name="Confidence Band",
        )
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 8, "r": 8, "t": 16, "b": 8},
        xaxis_title=None,
        yaxis_title="Projected Cost",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
    )
    st.plotly_chart(fig, use_container_width=True)


def _prepare_forecast_lab_df(forecast_df: pd.DataFrame | None) -> pd.DataFrame | None:
    required_cols = {"ds", "yhat", "yhat_lower", "yhat_upper"}
    if forecast_df is None or forecast_df.empty:
        return None
    if not required_cols.issubset(set(forecast_df.columns)):
        return None

    chart_df = forecast_df.copy()
    chart_df["ds"] = pd.to_datetime(chart_df["ds"], errors="coerce")
    chart_df = chart_df.dropna(subset=["ds"]).sort_values("ds")
    if chart_df.empty:
        return None
    return chart_df


def _render_forecasting_lab_interactive_chart(
    chart_df: pd.DataFrame, forecast_horizon: int, view_mode: str
) -> None:
    future_points = min(forecast_horizon, len(chart_df))
    if future_points < 1:
        st.warning("Forecast horizon is too small to render interactive charts.")
        return

    history_df = chart_df.iloc[:-future_points].tail(max(60, forecast_horizon * 4)).copy()
    future_df = chart_df.tail(future_points).copy()

    invalid_bounds = (future_df["yhat_lower"] > future_df["yhat_upper"]).any()
    if invalid_bounds:
        st.warning("Some confidence bounds are inverted (lower > upper). Review forecast integrity.")

    fig = go.Figure()

    if view_mode == "Forecast":
        if not history_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=history_df["ds"],
                    y=history_df["yhat"],
                    mode="lines",
                    name="Trend Baseline",
                    line={"color": "#7a7a7a", "width": 2},
                )
            )

        fig.add_trace(
            go.Scatter(
                x=future_df["ds"],
                y=future_df["yhat"],
                mode="lines",
                name="Forecast",
                line={"color": "#4f46e5", "width": 3},
            )
        )
        fig.add_trace(
            go.Scatter(
                x=future_df["ds"],
                y=future_df["yhat_upper"],
                mode="lines",
                line={"width": 0},
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=future_df["ds"],
                y=future_df["yhat_lower"],
                mode="lines",
                line={"width": 0},
                fill="tonexty",
                fillcolor="rgba(79, 70, 229, 0.18)",
                name="Confidence Band",
            )
        )
        yaxis_title = "Projected Cost"
    elif view_mode == "Uncertainty":
        uncertainty_df = future_df.copy()
        uncertainty_df["interval_width"] = uncertainty_df["yhat_upper"] - uncertainty_df["yhat_lower"]
        fig.add_trace(
            go.Bar(
                x=uncertainty_df["ds"],
                y=uncertainty_df["interval_width"],
                name="Interval Width",
                marker={"color": "#f59e0b"},
            )
        )
        yaxis_title = "Interval Width"
    else:
        delta_df = future_df.copy()
        delta_df["daily_change"] = delta_df["yhat"].diff().fillna(0.0)
        fig.add_trace(
            go.Bar(
                x=delta_df["ds"],
                y=delta_df["daily_change"],
                name="Day-over-Day Change",
                marker={"color": "#22c55e"},
            )
        )
        yaxis_title = "Forecast Delta"

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 8, "r": 8, "t": 16, "b": 8},
        xaxis_title=None,
        yaxis_title=yaxis_title,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_interactive_severity_chart(severity_counts: pd.Series) -> None:
    sev_df = severity_counts.reset_index()
    sev_df.columns = ["Severity", "Count"]

    fig = px.bar(
        sev_df,
        x="Severity",
        y="Count",
        color="Severity",
        color_discrete_map={
            "High": "#ef4444",
            "Medium": "#f59e0b",
            "Low": "#22c55e",
            "Normal": "#6b7280",
        },
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 8, "r": 8, "t": 16, "b": 8},
        xaxis_title=None,
        yaxis_title="Tickets",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


@st.cache_resource(show_spinner=False)
def _load_dashboard_models(contamination: float, forecast_horizon: int) -> dict:
    LOGGER.info(
        "Loading dashboard models with contamination=%.2f and horizon=%d",
        contamination,
        forecast_horizon,
    )

    df = pd.read_csv(DATA_PATH)

    ts_df = pd.DataFrame(
        {
            "ds": pd.date_range(start="2021-01-01", periods=len(df), freq="D"),
            "y": df["Cost_Consumed"].values,
        }
    )
    ts_df_model = ts_df.copy()
    ts_df_model["y"] = ts_df_model["y"].rolling(window=14, min_periods=1).mean()

    forecaster = ProjectForecaster(enable_sprint_seasonality=True)
    forecast_result = forecaster.generate_forecast(
        ts_df_model,
        metric_column="y",
        periods=forecast_horizon,
        include_metrics=True,
        include_components=False,
        date_column="ds",
    )

    anomaly_input_df = _prepare_anomaly_features(df)
    engine = AnomalyEngine(contamination=contamination)
    anomaly_results = engine.detect_anomalies(anomaly_input_df, FEATURE_COLUMNS)

    y_true = (
        (anomaly_input_df["budget_overrun_pct"] > 30)
        | (anomaly_input_df["days_overrun_pct"] > 35)
        | (anomaly_input_df["efficiency_score"] < 0.6)
    ).astype(int)
    roc_auc = roc_auc_score(y_true, -anomaly_results["anomaly_score"].to_numpy())

    severity_order = ["High", "Medium", "Low", "Normal"]
    severity_counts = (
        anomaly_results["severity"]
        .astype(str)
        .value_counts()
        .reindex(severity_order, fill_value=0)
    )

    alerts_table = _build_alerts_table(anomaly_results)
    return {
        "forecast": forecast_result,
        "anomaly": anomaly_results,
        "severity_counts": severity_counts,
        "roc_auc": roc_auc,
        "alerts": alerts_table,
    }


def render_dashboard() -> None:
    render_page_header(
        title="Dashboard Overview",
        subtitle="Real-time insights into your project risk landscape",
    )

    contamination = float(st.session_state.get("model_anomaly_sensitivity", 0.05))
    forecast_horizon = int(st.session_state.get("model_forecast_horizon", 14))

    render_top_bar("Portfolio Health", pill_text="Live", pill_kind="success")

    if st.button("Refresh analytics", use_container_width=False):
        st.cache_resource.clear()
        LOGGER.info("Dashboard model cache cleared by user")
        st.rerun()

    try:
        dashboard_data = _load_dashboard_models(contamination, forecast_horizon)
    except Exception as exc:
        LOGGER.exception("Dashboard model loading failed: %s", exc)
        st.error("Unable to load forecasting and anomaly analytics. Please try again.")
        return

    forecast_metrics = dashboard_data["forecast"].get("metrics") or {}
    severity_counts = dashboard_data["severity_counts"]
    anomaly_rate = dashboard_data["anomaly"]["is_anomaly"].mean() * 100.0
    risk_score = max(0.0, 100.0 - anomaly_rate)
    total_budget = pd.read_csv(DATA_PATH)["Budget_Allocated"].sum()

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric(label="Risk Score", value=f"{risk_score:.1f}")
    kpi2.metric(label="Total Budget", value=f"${total_budget:,.0f}")
    kpi3.metric(label="Active Tickets", value=f"{len(dashboard_data['anomaly']):,}")
    kpi4.metric(label="Detected Anomalies", value=f"{int(dashboard_data['anomaly']['is_anomaly'].sum())}")

    left, right = st.columns([1.8, 1.2], gap="large")

    with left:
        render_section_header("Forecast Trajectory")
        _render_interactive_forecast_chart(
            dashboard_data["forecast"].get("forecast"),
            forecast_horizon,
        )

        mape = forecast_metrics.get("mape")
        rmse = forecast_metrics.get("rmse")
        r2 = forecast_metrics.get("r2")
        r1c1, r1c2 = st.columns(2)
        r2c1, r2c2 = st.columns(2)
        r1c1.metric("MAPE", f"{mape:.2f}%" if mape is not None else "N/A")
        r1c2.metric("RMSE", f"{rmse:.2f}" if rmse is not None else "N/A")
        r2c1.metric("R2", f"{r2:.3f}" if r2 is not None else "N/A")
        r2c2.metric("Forecast Days", str(forecast_horizon))

    with right:
        render_section_header("Severity Mix")
        _render_interactive_severity_chart(severity_counts)

        s1, s2, s3 = st.columns(3)
        s1.metric("High", f"{int(severity_counts['High'])}")
        s2.metric("Medium", f"{int(severity_counts['Medium'])}")
        s3.metric("Low", f"{int(severity_counts['Low'])}")

        st.metric("ROC-AUC", f"{dashboard_data['roc_auc']:.3f}")

    col1, col2 = st.columns([2.0, 1.0], gap="large")
    with col1:
        render_section_header("Recent Anomaly Alerts")
        _render_alerts_table(dashboard_data["alerts"])

    with col2:
        render_section_header("Top Drivers")
        shap_proxy_df = _build_shap_proxy_table(dashboard_data["anomaly"])
        if shap_proxy_df.empty:
            st.info("No anomaly-linked feature contributions available yet.")
        else:
            st.dataframe(shap_proxy_df, hide_index=True, use_container_width=True)

    render_section_header("Open selected alert in Ticket Auditor")
    _render_auditor_selector(dashboard_data["alerts"])

    from app.components.ieee_metrics import render_ieee_metrics

    render_section_header("Governance")
    render_ieee_metrics()


def _render_alerts_table(alerts_df: pd.DataFrame) -> None:
    if alerts_df.empty:
        st.info("No anomaly alerts available for the current settings.")
        return

    table_df = alerts_df[["timestamp", "ticket", "alert", "severity", "status"]].copy()
    table_df.columns = ["Timestamp", "Ticket", "Alert Type", "Severity", "Status"]
    st.dataframe(table_df, hide_index=True, use_container_width=True)


def _render_auditor_selector(alerts_df: pd.DataFrame) -> None:
    if alerts_df.empty:
        return

    options = list(range(len(alerts_df)))
    selected_idx = st.selectbox(
        "Select alert to audit",
        options=options,
        format_func=lambda i: f"{alerts_df.iloc[i]['ticket']} ({alerts_df.iloc[i]['severity']})",
    )
    if st.button("Open in Auditor", use_container_width=False):
        st.session_state["auditor_ticket_index"] = selected_idx
        switched = switch_page_safe(AUDITOR_PAGE)
        if not switched:
            st.warning("Ticket Auditor page is not available in this environment.")


def render_forecasting_page() -> None:
    render_page_header(
        title="Forecasting Lab",
        subtitle="Prophet-based time-series risk forecasting with sprint seasonality",
    )

    contamination = float(st.session_state.get("model_anomaly_sensitivity", 0.05))
    forecast_horizon = int(st.session_state.get("model_forecast_horizon", 14))

    render_top_bar("Forecast Run", pill_text=f"{forecast_horizon} days", pill_kind="")

    if st.button("Regenerate forecast", use_container_width=False):
        st.cache_resource.clear()
        LOGGER.info("Forecast cache cleared by user")
        st.rerun()

    st.caption(
        f"Forecast horizon: {forecast_horizon} days · Anomaly sensitivity: {contamination:.2f} · Model: Prophet"
    )

    try:
        dashboard_data = _load_dashboard_models(contamination, forecast_horizon)
    except Exception as exc:
        LOGGER.exception("Forecast model loading failed: %s", exc)
        st.error("Unable to load forecasting models. Please try again.")
        return

    forecast_df = dashboard_data["forecast"].get("forecast")
    forecast_metrics = dashboard_data["forecast"].get("metrics") or {}
    forecast_meta = dashboard_data["forecast"].get("metadata") or {}

    mape = forecast_metrics.get("mape")
    rmse = forecast_metrics.get("rmse")
    r2 = forecast_metrics.get("r2")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("MAPE", f"{mape:.2f}%" if mape is not None else "N/A")
    m2.metric("RMSE", f"{rmse:.2f}" if rmse is not None else "N/A")
    m3.metric("R2", f"{r2:.3f}" if r2 is not None else "N/A")
    m4.metric("Forecast Days", str(forecast_horizon))

    render_section_header("Forecast: Cost Risk Trajectory")
    view_mode = st.radio(
        "Chart view",
        options=["Forecast", "Uncertainty", "Daily Change"],
        horizontal=True,
    )

    chart_df = _prepare_forecast_lab_df(forecast_df)
    if chart_df is not None:
        _render_forecasting_lab_interactive_chart(chart_df, forecast_horizon, view_mode)
    elif FORECAST_FIG_PATH.exists():
        st.image(str(FORECAST_FIG_PATH), use_container_width=True)
        st.caption("Pre-generated Prophet forecast figure.")
    elif forecast_df is not None and not forecast_df.empty:
        st.line_chart(
            forecast_df.set_index("ds")[["yhat", "yhat_lower", "yhat_upper"]].tail(
                forecast_horizon + 60
            )
        )
    else:
        st.warning("Forecast figure not available. Run the forecast figure generation script.")

    render_section_header("Prophet Configuration")
    seasonalities = forecast_meta.get("seasonalities", [])
    training_periods = forecast_meta.get("training_periods", "N/A")
    col_a, col_b = st.columns(2)
    col_a.markdown(
        f"""
        **Seasonalities:** {', '.join(seasonalities) if seasonalities else 'weekly'}  
        **Training Periods:** {training_periods} data points  
        **Changepoint Prior:** 0.05  
        **Sprint Cycle:** 14-day Fourier seasonality
        """
    )
    col_b.markdown(
        """
        **Validation Method:** 80/20 train-test split  
        **Metrics Computed:** MAPE, RMSE, R2  
        **Confidence Intervals:** 80% and 95%  
        **Growth Type:** Linear
        """
    )

    if forecast_df is not None and not forecast_df.empty:
        forecast_csv = forecast_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download full forecast CSV",
            data=forecast_csv,
            file_name="prophet_forecast_output.csv",
            mime="text/csv",
            use_container_width=False,
        )


def render_anomaly_page() -> None:
    render_page_header(
        title="Anomaly Triage Board",
        subtitle="Isolation Forest anomaly detection with severity ranking",
    )

    contamination = float(st.session_state.get("model_anomaly_sensitivity", 0.05))
    forecast_horizon = int(st.session_state.get("model_forecast_horizon", 14))

    render_top_bar("Anomaly Triage", pill_text=f"Sensitivity {contamination:.2f}", pill_kind="")

    if st.button("Refresh anomalies", use_container_width=False):
        st.cache_resource.clear()
        LOGGER.info("Anomaly cache cleared by user")
        st.rerun()

    try:
        dashboard_data = _load_dashboard_models(contamination, forecast_horizon)
    except Exception as exc:
        LOGGER.exception("Anomaly model loading failed: %s", exc)
        st.error("Unable to load anomaly detection models. Please try again.")
        return

    anomaly_results = dashboard_data["anomaly"]
    severity_counts = dashboard_data["severity_counts"]
    roc_auc = dashboard_data["roc_auc"]
    alerts_table = dashboard_data["alerts"]

    anomaly_rate = anomaly_results["is_anomaly"].mean() * 100.0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Anomaly Rate", f"{anomaly_rate:.2f}%")
    c2.metric("ROC-AUC Score", f"{roc_auc:.3f}")
    c3.metric("High Severity", int(severity_counts["High"]))
    c4.metric("Total Anomalies", int(anomaly_results["is_anomaly"].sum()))

    left, right = st.columns([3, 2])
    with left:
        render_section_header("Severity Distribution")
        _render_interactive_severity_chart(severity_counts)

        render_section_header("Recent Anomaly Alerts")
        _render_alerts_table(alerts_table)
        _render_auditor_selector(alerts_table)

    with right:
        render_section_header("Top Risk Drivers")
        shap_proxy_df = _build_shap_proxy_table(anomaly_results)
        if shap_proxy_df.empty:
            st.info("No feature contribution data available.")
        else:
            st.dataframe(shap_proxy_df, hide_index=True, use_container_width=True)

        render_section_header("Severity Breakdown")
        for level in ["High", "Medium", "Low", "Normal"]:
            count = int(severity_counts[level])
            st.metric(level, count)

        st.caption("ROC-AUC compares domain-derived labels vs anomaly scores.")

    render_section_header("Raw Anomaly Data")
    severity_filter = st.selectbox(
        "Filter by Severity",
        options=["All", "High", "Medium", "Low", "Normal"],
        index=0,
        key="anomaly_severity_filter",
    )
    display_df = anomaly_results.copy()
    if severity_filter != "All":
        display_df = display_df[display_df["severity"].astype(str) == severity_filter]

    anomaly_only = st.toggle("Show anomalies only", value=True, key="anomaly_only_toggle")
    if anomaly_only:
        display_df = display_df[display_df["is_anomaly"]]

    cols_to_show = [
        c
        for c in [
            "is_anomaly",
            "anomaly_score",
            "severity",
            "budget_overrun_pct",
            "days_overrun_pct",
            "efficiency_score",
            "cost_efficiency",
            "feature_contributions",
        ]
        if c in display_df.columns
    ]
    # Inject CSS to center the page number text and hide the native arrow spinner buttons
    st.markdown(
        """
        <style>
        div[data-testid="stNumberInput"] input {
            text-align: center;
            -moz-appearance: textfield;
        }
        div[data-testid="stNumberInput"] input::-webkit-outer-spin-button,
        div[data-testid="stNumberInput"] input::-webkit-inner-spin-button {
            -webkit-appearance: none;
            margin: 0;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Initialize session state keys if not present
    if "anomaly_page_size" not in st.session_state:
        st.session_state["anomaly_page_size"] = 200
    if "anomaly_page_num" not in st.session_state:
        st.session_state["anomaly_page_num"] = 1

    page_size = st.session_state["anomaly_page_size"]
    page_num = st.session_state["anomaly_page_num"]

    # Slice the dataframe based on pagination choices
    total_rows = len(display_df)
    if page_size == "All":
        paginated_df = display_df[cols_to_show].copy()
        start_idx = 0
        end_idx = total_rows
        paginated_df.index = range(1, total_rows + 1)
    else:
        page_size_int = int(page_size)
        total_pages = max(1, int(np.ceil(total_rows / page_size_int)))
        if page_num > total_pages:
            page_num = total_pages
            st.session_state["anomaly_page_num"] = total_pages
        start_idx = (page_num - 1) * page_size_int
        end_idx = min(start_idx + page_size_int, total_rows)
        paginated_df = display_df[cols_to_show].iloc[start_idx:end_idx].copy()
        paginated_df.index = range(start_idx + 1, start_idx + len(paginated_df) + 1)

    # Rename columns to user-friendly headers
    column_mapping = {
        "is_anomaly": "Is Anomaly",
        "anomaly_score": "Anomaly Score",
        "severity": "Severity",
        "budget_overrun_pct": "Budget Overrun %",
        "days_overrun_pct": "Schedule Overrun %",
        "efficiency_score": "Delivery Efficiency Score",
        "cost_efficiency": "Cost Efficiency Score",
        "feature_contributions": "Risk Driver Summary"
    }
    display_paginated_df = paginated_df.rename(columns=column_mapping)

    # Render table first
    st.dataframe(display_paginated_df, use_container_width=True, hide_index=False)

    # Render pagination controls below the table
    col_nav, col_info, col_size = st.columns([1, 5, 2])

    with col_size:
        limit_options = [50, 100, 200, 500, "All"]
        selected_size = st.selectbox(
            "Rows per page",
            options=limit_options,
            index=limit_options.index(page_size) if page_size in limit_options else 2,
            key="anomaly_page_size",
            label_visibility="collapsed"
        )
        if selected_size != page_size:
            st.session_state["anomaly_page_num"] = 1
            st.rerun()

    if page_size != "All":
        page_size_int = int(page_size)
        total_pages = max(1, int(np.ceil(total_rows / page_size_int)))

        with col_nav:
            new_page = st.number_input(
                "Page",
                min_value=1,
                max_value=total_pages,
                value=page_num,
                step=1,
                label_visibility="collapsed",
                key="anomaly_page_num"
            )
            if new_page != page_num:
                st.session_state["anomaly_page_num"] = new_page
                st.rerun()

    with col_info:
        page_info = f" (Page {page_num}/{total_pages})" if page_size != "All" else ""
        st.markdown(
            f"<div style='padding-top: 0.4rem; color: #8a8a8a; font-size: 0.9rem; text-align: center;'>"
            f"Showing {start_idx + 1 if total_rows > 0 else 0} - {end_idx} of {total_rows}{page_info}"
            f"</div>",
            unsafe_allow_html=True
        )

    csv_bytes = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download anomaly report (CSV)",
        data=csv_bytes,
        file_name="anomaly_triage_report.csv",
        mime="text/csv",
        use_container_width=False,
    )
