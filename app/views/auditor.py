"""Ticket auditor view with minimalist layout."""

from __future__ import annotations

import os
from typing import Any

import pandas as pd
import streamlit as st

from app.components.audit_trail_viewer import render_audit_trail
from app.components.genai_auditor import render_mitigation_engine
from app.components.shap_visuals import (
    get_top_driver_names,
    render_shap_force_plot,
    render_shap_table,
)
from app.components.ticket_viewer import render_ticket_context
from app.utils.routes import WHAT_IF_PAGE, switch_page_safe
from app.utils.styles import render_page_header, render_section_header, render_top_bar
from src.config import Paths


REAL_DATA_PATH = str(Paths.REAL_JIRA_SNAPSHOT)
SYNTHETIC_DATA_PATH = str(Paths.ML_READY_DATA)
DATA_PATH = REAL_DATA_PATH if Paths.REAL_JIRA_SNAPSHOT.exists() else SYNTHETIC_DATA_PATH
MODEL_PATH = str(Paths.XGB_MODEL)


def parse_adf_description(desc: Any) -> str:
    import ast
    import json
    import re

    if not desc or not isinstance(desc, str):
        return str(desc) if desc is not None else ""

    desc_str = desc.strip()
    if not (desc_str.startswith("{") and desc_str.endswith("}")):
        return desc_str

    parsed = None
    try:
        parsed = ast.literal_eval(desc_str)
    except Exception:
        try:
            parsed = json.loads(desc_str)
        except Exception:
            pass

    if isinstance(parsed, dict):
        text_fragments = []

        def extract_text(node):
            if isinstance(node, dict):
                if node.get("type") == "text" and "text" in node:
                    text_fragments.append(str(node["text"]))
                else:
                    for val in node.values():
                        extract_text(val)
            elif isinstance(node, list):
                for item in node:
                    extract_text(item)

        extract_text(parsed)
        if text_fragments:
            return "".join(text_fragments)

    matches = re.findall(r"['\"]text['\"]\s*:\s*['\"](.*?)['\"]", desc_str)
    if matches:
        return " ".join(matches)

    return desc_str


@st.cache_data
def load_dataset(path: str) -> pd.DataFrame | None:
    if not os.path.exists(path):
        if "real_jira_snapshot.csv" in path:
            path = "data/ml_ready_data.csv"

    if not os.path.exists(path):
        return None

    df = pd.read_csv(path)

    required_cols = ["Estimated_Days", "Budget_Allocated", "Story_Points", "Assignee_Seniority"]
    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        import numpy as np

        state = np.random.get_state()
        np.random.seed(42)
        try:
            n_rows = len(df)
            seniorities = ["Senior", "Junior", "Junior", "Mid", "Senior"]
            story_pts = [8.0, 3.0, 5.0, 2.0, 8.0]

            if "Assignee_Seniority" not in df.columns:
                df["Assignee_Seniority"] = [seniorities[i % len(seniorities)] for i in range(n_rows)]
            if "Story_Points" not in df.columns:
                df["Story_Points"] = [story_pts[i % len(story_pts)] for i in range(n_rows)]

            from src.preprocessing.data_pipeline import generate_metrics_with_signals

            df = generate_metrics_with_signals(df)
        finally:
            np.random.set_state(state)

    return df


@st.cache_resource
def load_model(path: str):
    if os.path.exists(path):
        import joblib

        return joblib.load(path)
    return None


def render_auditor() -> None:
    render_page_header(
        title="Ticket Auditor",
        subtitle="Review one ticket at a time with plain-language risk guidance",
    )

    dataset = load_dataset(DATA_PATH)
    model = load_model(MODEL_PATH)

    if dataset is None or model is None:
        st.warning("Model or data not available. Please ensure data is generated.")
        return

    if os.path.exists(REAL_DATA_PATH):
        pill_text = f"Real Jira · {len(dataset)} tickets"
        pill_kind = "success"
    else:
        pill_text = f"Synthetic · {len(dataset)} tickets"
        pill_kind = "warning"

    render_top_bar("Ticket Focus", pill_text=pill_text, pill_kind=pill_kind)

    _render_full_auditor(dataset, model)


def _ticket_label(ticket_data: pd.Series, ticket_index: int) -> str:
    risk = ticket_data.get("Risk_Level", "N/A")
    summary = ticket_data.get("Summary", f"Ticket #{ticket_index}")
    summary_str = str(summary)
    if len(summary_str) > 40:
        summary_str = summary_str[:37] + "..."
    return f"[{risk}] {summary_str}"


def _compute_confidence(model, processed_features: pd.DataFrame, risk_label: str) -> float:
    risk_map = {"Low": 0, "Medium": 1, "High": 2}
    try:
        probabilities = model.predict_proba(processed_features)[0]
        idx = risk_map.get(risk_label, 0)
        return float(probabilities[idx] * 100)
    except Exception:
        return 0.0


def _render_split_columns(
    ticket_index: int,
    ticket_data: pd.Series,
    model,
    dataset: pd.DataFrame,
    shap_mode: str,
    button_key: str,
) -> None:
    risk_label, processed_features, _ = render_ticket_context(ticket_data, model, dataset)
    if risk_label is None:
        return

    confidence_pct = _compute_confidence(model, processed_features, risk_label)
    _render_risk_banner(risk_label, confidence=confidence_pct / 100)

    raw_desc = ticket_data.get("Description", "")
    parsed_desc = parse_adf_description(raw_desc)
    summary_text = ticket_data.get("Summary", "N/A")

    st.markdown(
        f"""
        <div class="card" style="margin-bottom: 1.4rem;">
            <div style="font-weight: 600; font-size: 1rem; color: #ffffff; margin-bottom: 0.6rem;">
                {summary_text}
            </div>
            <div style="font-size: 0.9rem; color: #c2c2c2; line-height: 1.6; white-space: pre-wrap;">
                {parsed_desc}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    est_days = ticket_data.get("Estimated_Days")
    story_pts = ticket_data.get("Story_Points")
    budget = ticket_data.get("Budget_Allocated")
    priority_val = ticket_data.get("Priority", "N/A")

    def format_days(val):
        if pd.isna(val) or val is None:
            return "N/A"
        fval = float(val)
        return f"{int(fval)} days" if fval.is_integer() else f"{fval:.1f} days"

    def format_pts(val):
        if pd.isna(val) or val is None:
            return "N/A"
        fval = float(val)
        return f"{int(fval)} pts" if fval.is_integer() else f"{fval:.1f} pts"

    days_str = format_days(est_days)
    pts_str = format_pts(story_pts)
    budget_str = f"${float(budget):,.0f}" if budget is not None and pd.notna(budget) else "N/A"

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Estimated Days", days_str)
    m2.metric("Story Points", pts_str)
    m3.metric("Budget", budget_str)
    m4.metric("Priority", str(priority_val))

    if st.button("Try What-If Scenario", key=f"what_if_{ticket_index}", use_container_width=False):
        st.session_state["what_if_ticket_index"] = ticket_index
        switched = switch_page_safe(WHAT_IF_PAGE)
        if not switched:
            st.warning("What-If Simulation page is not available in this environment.")

    top_drivers = get_top_driver_names(processed_features, model, top_n=5)

    render_section_header("Why this ticket is risky")
    st.caption("Top factors that increase risk for this ticket.")
    st.markdown('<div class="card" style="margin-bottom: 1.2rem;">', unsafe_allow_html=True)
    if shap_mode == "Force View":
        render_shap_force_plot(processed_features, model)
    else:
        render_shap_table(processed_features, model)
    st.markdown("</div>", unsafe_allow_html=True)

    render_section_header("Suggested actions")
    st.caption("Practical steps to lower delivery risk.")
    st.markdown('<div class="card" style="margin-bottom: 1.2rem;">', unsafe_allow_html=True)
    def safe_int(val: Any, default: int = 0) -> int:
        if pd.isna(val) or val is None:
            return default
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return default

    def safe_float(val: Any, default: float = 0.0) -> float:
        if pd.isna(val) or val is None:
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    shap_drivers = {
        "summary": str(ticket_data.get("Summary", "N/A")),
        "priority": str(ticket_data.get("Priority", "N/A")),
        "assignee_seniority": str(ticket_data.get("Assignee_Seniority", "N/A")),
        "estimated_days": safe_int(ticket_data.get("Estimated_Days", 0)),
        "story_points": safe_int(ticket_data.get("Story_Points", 0)),
        "budget_allocated": safe_float(ticket_data.get("Budget_Allocated", 0.0)),
        "top_factors": top_drivers,
    }
    render_mitigation_engine(
        ticket_index,
        risk_label,
        shap_drivers,
        audit_context={
            "ticket_id": _ticket_label(ticket_data, ticket_index),
            "confidence_pct": confidence_pct,
            "top_drivers": top_drivers,
        },
        button_key=button_key,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    render_audit_trail(_ticket_label(ticket_data, ticket_index))


def _render_full_auditor(dataset: pd.DataFrame, model) -> None:
    render_section_header("Select Ticket")

    preselected = int(st.session_state.get("auditor_ticket_index", 0) or 0)
    if preselected < 0 or preselected >= len(dataset):
        preselected = 0

    single_ticket = st.selectbox(
        "Primary ticket",
        options=range(len(dataset)),
        index=preselected,
        format_func=lambda x: _ticket_label(dataset.iloc[x], x),
        label_visibility="collapsed",
    )
    st.session_state["auditor_ticket_index"] = single_ticket

    comparison_mode = st.toggle(
        "Compare multiple tickets",
        value=False,
        help="Compare up to 2 tickets side-by-side.",
    )
    shap_mode = st.radio(
        "Explanation view",
        options=["Table View", "Force View"],
        horizontal=True,
    )

    if comparison_mode:
        selected = st.multiselect(
            "Tickets to compare (max 2)",
            options=range(len(dataset)),
            default=[single_ticket],
            format_func=lambda x: _ticket_label(dataset.iloc[x], x),
            max_selections=2,
        )
        if not selected:
            st.info("Select at least one ticket for comparison.")
            return
        columns = st.columns(2, gap="large")
        for pos, idx in enumerate(selected):
            ticket_data = dataset.iloc[idx]
            with columns[pos]:
                st.markdown(
                    f"<div class=\"section-header\">{_ticket_label(ticket_data, idx)}</div>",
                    unsafe_allow_html=True,
                )
                _render_split_columns(
                    ticket_index=idx,
                    ticket_data=ticket_data,
                    model=model,
                    dataset=dataset,
                    shap_mode=shap_mode,
                    button_key=f"mitigate_{idx}",
                )
    else:
        ticket_data = dataset.iloc[single_ticket]
        _render_split_columns(
            ticket_index=single_ticket,
            ticket_data=ticket_data,
            model=model,
            dataset=dataset,
            shap_mode=shap_mode,
            button_key=f"mitigate_{single_ticket}",
        )


def _render_risk_banner(risk_level: str, confidence: float) -> None:
    level_lower = risk_level.lower()
    st.markdown(
        f"""
        <div class="risk-banner">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:0.7rem; letter-spacing:0.08em; text-transform:uppercase; color:#8a8a8a;">Predicted Risk</div>
                    <div class="risk-banner-value risk-value-{level_lower}">{risk_level.upper()}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:0.7rem; letter-spacing:0.08em; text-transform:uppercase; color:#8a8a8a;">Confidence</div>
                    <div class="risk-banner-value risk-value-{level_lower}">{confidence:.0%}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
