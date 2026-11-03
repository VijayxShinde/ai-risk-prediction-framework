"""Routing constants and safe navigation helpers for Streamlit MPA."""

from __future__ import annotations

import streamlit as st
from streamlit.errors import StreamlitAPIException


MAIN_PAGE = "main.py"
DASHBOARD_PAGE = "pages/1_Dashboard.py"
FORECASTING_PAGE = "pages/2_Forecasting.py"
ANOMALY_PAGE = "pages/3_Anomaly_Detection.py"
WHAT_IF_PAGE = "pages/4_What_If_Simulation.py"
SETTINGS_PAGE = "pages/5_Settings.py"
JIRA_SYNC_PAGE = "pages/6_Jira_Sync.py"
AUDITOR_PAGE = "pages/7_Ticket_Auditor.py"


def page_candidates(path: str) -> list[str]:
    """Return candidate page paths for environment differences."""
    windows_path = path.replace("/", "\\")
    return [path, windows_path, f"./{path}", path.split("/")[-1]]


def switch_page_safe(path: str) -> bool:
    """Switch to page and return False instead of raising on path mismatch."""
    for candidate in page_candidates(path):
        try:
            st.switch_page(candidate)
            return True
        except StreamlitAPIException:
            continue
    return False


def page_link_safe(path: str, label: str, icon: str | None = None) -> None:
    """Render page link using resilient path candidates."""
    for candidate in page_candidates(path):
        try:
            if icon:
                st.page_link(candidate, label=label, icon=icon)
            else:
                st.page_link(candidate, label=label)
            return
        except StreamlitAPIException:
            continue
    st.caption(f"{label} unavailable")
