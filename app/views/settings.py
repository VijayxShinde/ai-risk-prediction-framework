"""Settings view with minimalist layout."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from app.utils.styles import render_page_header, render_section_header, render_top_bar


_SETTINGS_FILE = Path(__file__).resolve().parents[2] / "logs" / "user_settings.json"

_PERSISTENT_KEYS = [
    "settings_name",
    "settings_email",
    "settings_role",
    "notif_email_high_risk",
    "notif_anomaly",
    "notif_weekly_digest",
    "notif_slack",
    "jira_url",
    "jira_project_key",
    "model_anomaly_sensitivity",
    "model_forecast_horizon",
    "model_risk_threshold",
    "model_genai_provider",
]


def _load_saved_settings() -> None:
    if not _SETTINGS_FILE.exists():
        return
    try:
        saved = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
        for key, value in saved.items():
            if key not in st.session_state:
                st.session_state[key] = value
    except (json.JSONDecodeError, OSError):
        pass


def _save_current_settings() -> None:
    _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    snapshot = {k: st.session_state.get(k) for k in _PERSISTENT_KEYS if k in st.session_state}
    _SETTINGS_FILE.write_text(json.dumps(snapshot, indent=2, default=str), encoding="utf-8")


def render_settings() -> None:
    _load_saved_settings()

    render_page_header(
        title="Settings",
        subtitle="Configure your dashboard preferences and integrations",
    )

    render_top_bar("Workspace Preferences", pill_text="User", pill_kind="")

    left, right = st.columns(2)
    with left:
        _render_profile_settings()
        _render_notification_settings()

    with right:
        _render_jira_settings()
        _render_model_settings()

    render_section_header("Save Changes")
    col_save, _ = st.columns([1, 3])
    with col_save:
        if st.button("Save Settings", type="primary", use_container_width=False):
            _save_current_settings()
            st.success(
                f"Settings saved to `{_SETTINGS_FILE.relative_to(Path.cwd()) if _SETTINGS_FILE.is_relative_to(Path.cwd()) else _SETTINGS_FILE}`."
            )


def _render_profile_settings() -> None:
    render_section_header("Profile")

    user = st.session_state.get("user", {})

    st.text_input(
        "Full Name",
        value=user.get("full_name", ""),
        key="settings_name",
        placeholder="Enter your full name",
    )

    st.text_input(
        "Email Address",
        value=user.get("email", ""),
        key="settings_email",
        placeholder="Enter your email",
    )

    st.selectbox(
        "Role",
        options=["Administrator", "Project Manager", "Data Analyst", "Viewer"],
        key="settings_role",
    )


def _render_notification_settings() -> None:
    render_section_header("Notifications")

    st.toggle(
        "Email notifications for high-risk alerts",
        value=True,
        key="notif_email_high_risk",
    )

    st.toggle("In-app anomaly notifications", value=True, key="notif_anomaly")

    st.toggle("Weekly risk summary digest", value=False, key="notif_weekly_digest")

    st.toggle("Real-time Slack notifications", value=False, key="notif_slack")


def _render_jira_settings() -> None:
    render_section_header("Jira Integration")

    st.text_input(
        "Jira Instance URL",
        placeholder="https://your-company.atlassian.net",
        key="jira_url",
    )

    st.text_input(
        "API Token",
        type="password",
        placeholder="Enter your Jira API token",
        key="jira_token",
    )

    st.text_input("Project Key", placeholder="e.g., PROJ", key="jira_project_key")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Test Connection", key="test_jira", use_container_width=False):
            jira_url = st.session_state.get("jira_url", "")
            if jira_url:
                st.info(
                    "Connection is validated via OAuth on the Jira Sync page. "
                    "Navigate to Jira Sync to authorize and test."
                )
            else:
                st.warning("Enter a Jira Instance URL above first.")

    with col2:
        if st.button("Go to Jira Sync", key="sync_jira", type="secondary", use_container_width=False):
            from app.utils.routes import JIRA_SYNC_PAGE, switch_page_safe

            switched = switch_page_safe(JIRA_SYNC_PAGE)
            if not switched:
                st.info("Navigate to Jira Sync in the sidebar.")


def _render_model_settings() -> None:
    render_section_header("Model Configuration")

    st.slider(
        "Anomaly Detection Sensitivity",
        min_value=0.01,
        max_value=0.15,
        value=0.05,
        step=0.01,
        format="%.2f",
        key="model_anomaly_sensitivity",
        help="Lower values detect fewer anomalies; higher values detect more.",
    )

    st.slider(
        "Forecast Horizon (days)",
        min_value=7,
        max_value=90,
        value=14,
        step=7,
        key="model_forecast_horizon",
        help="Number of days to forecast into the future",
    )

    st.selectbox(
        "Risk Threshold Mode",
        options=["Conservative", "Balanced", "Aggressive"],
        index=1,
        key="model_risk_threshold",
        help="Conservative flags more risks, Aggressive flags fewer",
    )

    st.selectbox(
        "GenAI Provider",
        options=["NVIDIA (Qwen 3.5)", "OpenAI (GPT-4)", "Anthropic (Claude)"],
        index=0,
        key="model_genai_provider",
        help="Select the AI provider for mitigation recommendations",
    )

    st.markdown(
        """
        <div class="card" style="margin-top: 1rem;">
            <div class="card-title">Current Model</div>
            <div style="display:flex; justify-content:space-between; margin-bottom: 0.4rem;">
                <span>Classifier</span>
                <span style="color:#ffffff; font-weight:600;">XGBoost v2.0</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom: 0.4rem;">
                <span>Last Trained</span>
                <span style="color:#ffffff; font-weight:600;">Apr 7, 2026</span>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span>Accuracy</span>
                <span style="color:#22c55e; font-weight:600;">87.3%</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
