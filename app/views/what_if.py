"""What-If Simulation view (minimalist layout)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.simulation_viewer import (
    render_delta_metrics,
    render_input_metrics,
    render_scenario_export,
    render_scenario_panels,
)
from app.utils.routes import AUDITOR_PAGE, switch_page_safe
from app.utils.styles import render_page_header, render_section_header, render_top_bar
from app.views.auditor import DATA_PATH, MODEL_PATH, load_dataset, load_model, _ticket_label
from src.simulation.what_if_simulator import WhatIfSimulator


def render_what_if_page() -> None:
    render_page_header(
        title="What-If Simulation",
        subtitle="Test parameter changes and project their risk impact",
    )

    dataset = load_dataset(DATA_PATH)
    model = load_model(MODEL_PATH)
    if dataset is None or model is None:
        st.warning("Model or data not available. Please ensure artifacts are present.")
        return

    simulator = WhatIfSimulator(model=model, dataset=dataset, daily_burn_rate=500.0)

    preselected = int(st.session_state.get("what_if_ticket_index", 0) or 0)
    if preselected < 0 or preselected >= len(dataset):
        preselected = 0

    render_top_bar("Scenario Builder", pill_text="Interactive", pill_kind="")

    render_section_header("Baseline Ticket")
    ticket_idx = st.selectbox(
        "Ticket",
        options=range(len(dataset)),
        index=preselected,
        format_func=lambda i: _ticket_label(dataset.iloc[i], i),
        label_visibility="collapsed",
    )
    st.session_state["what_if_ticket_index"] = ticket_idx

    baseline_row = dataset.iloc[ticket_idx]

    c_title, c_reset = st.columns([4, 1])
    with c_title:
        st.markdown("#### Parameter Adjustment")
    with c_reset:
        if st.button("Reset Scenario", type="secondary", use_container_width=False):
            st.session_state["timeline_ext"] = 0
            st.session_state["budget_mult"] = 1.0
            st.session_state["efficiency"] = 1.0
            st.session_state["priority_override"] = None
            st.session_state["seniority_override"] = None
            st.session_state["issue_type_override"] = None
            st.rerun()

    c1, c2, c3 = st.columns(3)
    with c1:
        timeline_extension = st.slider(
            "Timeline Extension (days)",
            min_value=-10,
            max_value=20,
            value=0,
            step=1,
            help="Positive values add delivery days, negative values compress schedule.",
            key="timeline_ext",
        )
    with c2:
        budget_multiplier = st.slider(
            "Budget Multiplier",
            min_value=0.5,
            max_value=2.5,
            value=1.0,
            step=0.05,
            help="1.00 = unchanged. Used only when budget is explicitly adjusted.",
            key="budget_mult",
        )
    with c3:
        team_efficiency = st.slider(
            "Team Efficiency",
            min_value=0.6,
            max_value=1.4,
            value=1.0,
            step=0.05,
            help="Affects timeline only. 0.8 means slower velocity; 1.2 means faster velocity.",
            key="efficiency",
        )

    budget_changed = abs(budget_multiplier - 1.0) > 1e-9
    timeline_changed = timeline_extension != 0

    with st.expander("Advanced Options", expanded=False):
        priority_override = st.selectbox(
            "Priority Override",
            options=[None, "Low", "Medium", "High"],
            format_func=lambda v: "No change" if v is None else str(v),
            key="priority_override",
        )
        seniority_override = st.selectbox(
            "Assignee Seniority Override",
            options=[None, "Junior", "Mid", "Senior"],
            format_func=lambda v: "No change" if v is None else str(v),
            key="seniority_override",
        )
        issue_type_override = st.selectbox(
            "Issue Type Override",
            options=[None, "Bug", "Task", "Epic"],
            format_func=lambda v: "No change" if v is None else str(v),
            key="issue_type_override",
        )

    deltas = {
        "timeline_extension_days": float(timeline_extension),
        "budget_multiplier": budget_multiplier,
        "team_efficiency": team_efficiency,
        "timeline_changed": timeline_changed,
        "budget_changed": budget_changed,
        "priority_override": priority_override,
        "seniority_override": seniority_override,
        "issue_type_override": issue_type_override,
    }

    simulated_row = simulator.apply_deltas(baseline_row=baseline_row, deltas=deltas)
    comparison = simulator.compare_scenarios(baseline_row=baseline_row, simulated_row=simulated_row)

    render_section_header("Scenario Impact")
    render_delta_metrics(comparison)
    render_scenario_panels(comparison, model)
    render_input_metrics(simulated_row, comparison)

    render_section_header("Export")
    render_scenario_export(comparison, baseline_row, simulated_row)

    render_section_header("Navigation")
    nav1, nav2 = st.columns(2)
    with nav1:
        if st.button("Open Current Ticket in Auditor", use_container_width=False):
            st.session_state["auditor_ticket_index"] = ticket_idx
            switched = switch_page_safe(AUDITOR_PAGE)
            if not switched:
                st.warning("Ticket Auditor page is not available in this environment.")
    with nav2:
        st.caption("Tip: from Ticket Auditor, use the 'Try What-If Scenario' button.")
