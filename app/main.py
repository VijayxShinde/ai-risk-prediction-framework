"""Landing page for native Streamlit multipage app."""

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.env import ensure_project_root

ensure_project_root()

from app.utils.routes import DASHBOARD_PAGE, switch_page_safe
from app.views.login import render_login_view

st.set_page_config(initial_sidebar_state="expanded", layout="centered")


def _intercept_jira_oauth_callback() -> None:
    code = st.query_params.get("code")
    if not code:
        return

    st.info("Securely exchanging Jira token...")
    try:
        import os

        from src.database.auth_db import get_user, get_user_by_role
        from src.integrations.jira_client import JiraAPIClient
        from src.integrations.oauth_handler import JiraOAuthHandler

        handler = JiraOAuthHandler.from_env()
        token_data = handler.exchange_auth_code(str(code))
        cloud_id = handler.fetch_cloud_id(token_data.get("access_token", ""))

        JiraAPIClient.save_cached_tokens(
            {
                "access_token": token_data.get("access_token", ""),
                "refresh_token": token_data.get("refresh_token", ""),
                "token_expires_at": token_data.get("expires_at", 0.0),
                "cloud_id": cloud_id,
            }
        )

        admin_username = os.getenv("DEFAULT_ADMIN_USER", "").strip()
        admin_user = get_user(admin_username) if admin_username else None
        if not admin_user:
            admin_user = get_user_by_role("Administrator")
        if not admin_user:
            st.error(
                "Admin user not found. Run scripts/bootstrap_admin.py to initialize the auth database."
            )
            st.query_params.clear()
            return

        st.session_state["authenticated"] = True
        st.session_state["username"] = admin_user.get("username", admin_username or "admin")
        st.session_state["role"] = admin_user.get("role", "Administrator")
        st.session_state["user"] = {
            "username": admin_user.get("username", admin_username or "admin"),
            "full_name": admin_user.get("full_name") or admin_user.get("username") or "Admin User",
            "email": admin_user.get("email") or "",
            "role": admin_user.get("role", "Administrator"),
        }
        st.query_params.clear()
        st.switch_page("pages/6_Jira_Sync.py")
        st.stop()
    except Exception as exc:
        st.error(f"Jira OAuth processing failed: {exc}")
        st.query_params.clear()


_intercept_jira_oauth_callback()

st.markdown(
    """
    <style>
    /* Hide sidebar and expand/collapse controls on login page only */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _inject_login_css() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background: #0a0a0a;
            }
            .login-shell {
                margin-top: 8vh;
                border: 1px solid #262626;
                border-radius: 8px;
                padding: 24px;
                background: #121212;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        switch_page_safe(DASHBOARD_PAGE)
        st.stop()

    _inject_login_css()
    render_login_view()


if __name__ == "__main__":
    main()
