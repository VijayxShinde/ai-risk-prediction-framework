"""Minimalist sidebar navigation for Streamlit MPA."""

from __future__ import annotations

from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PAGES_DIR = PROJECT_ROOT / "app" / "pages"

PAGE_PATHS = {
    "dashboard": "pages/1_Dashboard.py",
    "forecasting": "pages/2_Forecasting.py",
    "anomaly": "pages/3_Anomaly_Detection.py",
    "what_if": "pages/4_What_If_Simulation.py",
    "jira_sync": "pages/6_Jira_Sync.py",
    "settings": "pages/5_Settings.py",
    "auditor": "pages/7_Ticket_Auditor.py",
}


def _exists(page_path: str) -> bool:
    if page_path == "main.py":
        return True
    return (PROJECT_ROOT / "app" / page_path).exists()


def _link(page_path: str, label: str) -> None:
    if _exists(page_path):
        st.page_link(page_path, label=label)
    else:
        st.caption(f"{label} unavailable")


def render_sidebar() -> None:
    user = st.session_state.get(
        "user",
        {
            "username": "demo",
            "full_name": "Demo User",
            "role": "Admin",
        },
    )
    display_name = (
        user.get("full_name")
        or user.get("name")
        or user.get("username")
        or "Demo User"
    )
    role = user.get("role", "Admin")
    initial = display_name[0].upper()

    logo_path = str(PROJECT_ROOT / "app" / "assets" / "logo.png")
    icon_path = str(PROJECT_ROOT / "app" / "assets" / "icon.png")
    st.logo(logo_path, icon_image=icon_path)

    with st.sidebar:

        st.markdown("<div class='section-title'>Workspace</div>", unsafe_allow_html=True)
        _link(PAGE_PATHS["dashboard"], "Dashboard")

        st.markdown("<div class='section-title'>Monitoring</div>", unsafe_allow_html=True)
        _link(PAGE_PATHS["forecasting"], "Forecasting Lab")
        _link(PAGE_PATHS["anomaly"], "Anomaly Triage")
        _link(PAGE_PATHS["auditor"], "Ticket Auditor")
        _link(PAGE_PATHS["what_if"], "What-If Simulation")

        st.markdown("<div class='section-title'>Integrations</div>", unsafe_allow_html=True)
        _link(PAGE_PATHS["jira_sync"], "Jira Sync")

        st.markdown("<div class='section-title'>System</div>", unsafe_allow_html=True)
        _link(PAGE_PATHS["settings"], "Settings")

        st.markdown(
            f"""
            <div class="sidebar-footer">
                <div style="display:flex; align-items:center; gap:0.5rem;">
                    <div style="width:28px; height:28px; border-radius:50%; background:#1f1f1f; display:flex; align-items:center; justify-content:center; color:#ffffff; font-size:0.8rem;">{initial}</div>
                    <div>
                        <div style="color:#ffffff; font-size:0.8rem; font-weight:600;">{display_name}</div>
                        <div style="color:#8a8a8a; font-size:0.7rem;">{role}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
