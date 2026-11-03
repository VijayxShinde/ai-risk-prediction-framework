"""Login/Signup View Component for SQLite-backed auth."""

from __future__ import annotations

import streamlit as st

from app.utils.styles import COLORS
from src.database.auth_db import create_user, hash_password, verify_user


def get_login_styles() -> str:
    return f"""
    <style>
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}

        .stApp {{
            background-color: {COLORS['bg_primary']};
        }}

        .login-container {{
            max-width: 80px;
            margin: 0 auto;
            padding: 2rem 2.2rem;
            background: {COLORS['bg_secondary']};
            border-radius: 10px;
            border: 1px solid {COLORS['border_primary']};
        }}

        .login-header {{
            text-align: center;
            margin-bottom: 1.6rem;
        }}

        .login-title {{
            font-size: 1.4rem;
            font-weight: 600;
            color: {COLORS['text_primary']};
            margin-bottom: 0.35rem;
            letter-spacing: -0.02em;
        }}

        .login-subtitle {{
            color: {COLORS['text_muted']};
            font-size: 0.85rem;
        }}

        .auth-toggle {{
            text-align: center;
            margin-top: 1.4rem;
            padding-top: 1.2rem;
            border-top: 1px solid {COLORS['border_primary']};
        }}

        .auth-toggle-text {{
            color: {COLORS['text_muted']};
            font-size: 0.8rem;
        }}

        .error-message {{
            border: 1px solid rgba(239, 68, 68, 0.4);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            color: {COLORS['error']};
            font-size: 0.85rem;
            margin-bottom: 1rem;
            background: rgba(239, 68, 68, 0.08);
        }}

        .success-message {{
            border: 1px solid rgba(34, 197, 94, 0.4);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            color: {COLORS['success']};
            font-size: 0.85rem;
            margin-bottom: 1rem;
            background: rgba(34, 197, 94, 0.08);
        }}

        .stTextInput > div > div > input {{
            background: {COLORS['bg_secondary']} !important;
            border: 1px solid {COLORS['border_primary']} !important;
            border-radius: 6px !important;
            padding: 0.7rem 0.875rem !important;
            font-size: 0.9rem !important;
            color: {COLORS['text_primary']} !important;
        }}

        .stTextInput > div > div > input:focus {{
            border-color: {COLORS['text_secondary']} !important;
            box-shadow: none !important;
        }}

        .stButton > button {{
            width: 100%;
            border-radius: 6px !important;
            padding: 0.7rem 1.5rem !important;
            font-weight: 600 !important;
        }}
    </style>
    """


def render_login_view() -> None:
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"
    if "login_error" not in st.session_state:
        st.session_state.login_error = None
    if "signup_success" not in st.session_state:
        st.session_state.signup_success = False

    st.markdown(get_login_styles(), unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:

        st.markdown('<div class="login-container">', unsafe_allow_html=True)

        st.markdown(
            """
            <div class="login-header">
                <div class="login-title">RiskAI</div>
                <div class="login-subtitle">AI-Driven Risk Prediction Framework</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.login_error:
            st.markdown(
                f'<div class="error-message">{st.session_state.login_error}</div>',
                unsafe_allow_html=True,
            )

        if st.session_state.signup_success:
            st.markdown(
                '<div class="success-message">Account created. Please sign in.</div>',
                unsafe_allow_html=True,
            )
            st.session_state.signup_success = False

        if st.session_state.auth_mode == "login":
            _render_login_form()
        else:
            _render_signup_form()

        st.markdown("</div>", unsafe_allow_html=True)


def _render_login_form() -> None:
    username = st.text_input(
        "Username",
        placeholder="Enter your username",
        key="login_username",
        label_visibility="collapsed",
    )

    st.markdown("<div style='height: 0.4rem'></div>", unsafe_allow_html=True)

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password",
        key="login_password",
        label_visibility="collapsed",
    )

    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

    if st.button("Sign In", type="primary", use_container_width=True):
        _handle_login(username, password)

    st.markdown(
        """
        <div class="auth-toggle">
            <span class="auth-toggle-text">Don't have an account?</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Create Account", type="secondary", use_container_width=True):
        st.session_state.auth_mode = "signup"
        st.session_state.login_error = None
        st.rerun()


def _render_signup_form() -> None:
    full_name = st.text_input(
        "Full Name",
        placeholder="Enter your full name",
        key="signup_name",
        label_visibility="collapsed",
    )
    st.markdown("<div style='height: 0.4rem'></div>", unsafe_allow_html=True)

    email = st.text_input(
        "Email",
        placeholder="Enter your email",
        key="signup_email",
        label_visibility="collapsed",
    )
    st.markdown("<div style='height: 0.4rem'></div>", unsafe_allow_html=True)

    username = st.text_input(
        "Username",
        placeholder="Choose a username",
        key="signup_username",
        label_visibility="collapsed",
    )
    st.markdown("<div style='height: 0.4rem'></div>", unsafe_allow_html=True)

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Create a password",
        key="signup_password",
        label_visibility="collapsed",
    )
    st.markdown("<div style='height: 0.4rem'></div>", unsafe_allow_html=True)

    confirm_password = st.text_input(
        "Confirm Password",
        type="password",
        placeholder="Confirm your password",
        key="signup_confirm_password",
        label_visibility="collapsed",
    )

    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

    if st.button("Create Account", type="primary", use_container_width=True):
        _handle_signup(full_name, email, username, password, confirm_password)

    st.markdown(
        """
        <div class="auth-toggle">
            <span class="auth-toggle-text">Already have an account?</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Sign In", type="secondary", use_container_width=True):
        st.session_state.auth_mode = "login"
        st.session_state.login_error = None
        st.rerun()


def _handle_login(username: str, password: str) -> None:
    st.session_state.login_error = None

    if not username or not password:
        st.session_state.login_error = "Please enter both username and password."
        st.rerun()
        return

    user_record = verify_user(username, password)

    if user_record:
        st.session_state.authenticated = True
        st.session_state.user = {
            "username": user_record.get("username", username),
            "full_name": user_record.get("full_name") or username,
            "email": user_record.get("email") or "",
            "role": user_record.get("role") or "Viewer",
        }
        st.session_state.login_error = None
        st.rerun()
    else:
        st.session_state.login_error = "Invalid credentials. Please check your username and password."
        st.rerun()


def _handle_signup(
    full_name: str, email: str, username: str, password: str, confirm_password: str
) -> None:
    st.session_state.login_error = None

    if not all([full_name, email, username, password, confirm_password]):
        st.session_state.login_error = "Please fill in all fields."
        st.rerun()
        return

    if password != confirm_password:
        st.session_state.login_error = "Passwords do not match."
        st.rerun()
        return

    if len(password) < 8:
        st.session_state.login_error = "Password must be at least 8 characters."
        st.rerun()
        return

    username = username.strip()

    created = create_user(
        username=username,
        hashed_password=hash_password(password),
        role="Project Manager",
        full_name=full_name.strip(),
        email=email.strip(),
    )

    if not created:
        st.session_state.login_error = (
            f"Username '{username}' is already taken. Please choose another."
        )
        st.rerun()
        return

    st.session_state.signup_success = True
    st.session_state.auth_mode = "login"
    st.rerun()
