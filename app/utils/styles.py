"""
Global styles for a minimalist dark UI.
"""

from __future__ import annotations

import streamlit as st


COLORS = {
    "bg_primary": "#0a0a0a",
    "bg_secondary": "#121212",
    "bg_tertiary": "#1a1a1a",
    "border_primary": "#262626",
    "border_secondary": "#2f2f2f",
    "text_primary": "#ffffff",
    "text_secondary": "#c2c2c2",
    "text_muted": "#8a8a8a",
    "accent": "#4f46e5",
    "accent_soft": "rgba(79, 70, 229, 0.12)",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "error": "#ef4444",
}


def inject_global_css() -> None:
    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

            * {{
                font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }}

            #MainMenu, footer {{ visibility: hidden; }}

            .stApp {{
                background: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
            }}

            section[data-testid="stMain"] > div:first-child {{
                padding-top: 1.5rem;
            }}

            .main .block-container {{
                max-width: 1280px;
                padding: 2rem 3.5rem 3rem;
            }}

            h1, h2, h3, h4, h5, h6 {{
                color: {COLORS['text_primary']} !important;
                font-weight: 600 !important;
                letter-spacing: -0.02em;
            }}

            p, span, div, label {{
                color: {COLORS['text_secondary']};
            }}

            .page-title {{
                font-size: 1.8rem;
                font-weight: 600;
                margin-bottom: 0.35rem;
                color: {COLORS['text_primary']};
            }}

            .page-subtitle {{
                font-size: 0.95rem;
                color: {COLORS['text_muted']};
                margin-bottom: 2rem;
            }}

            .section-header {{
                font-size: 0.8rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: {COLORS['text_muted']};
                margin: 1.5rem 0 0.75rem;
            }}

            [data-testid="stMetric"] {{
                background: transparent;
                border: 1px solid {COLORS['border_primary']};
                border-radius: 6px;
                padding: 1rem 1.1rem;
                box-shadow: none;
            }}

            [data-testid="stMetric"] label {{
                color: {COLORS['text_muted']} !important;
                font-size: 0.7rem !important;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 600;
            }}



            [data-testid="stMetricValue"] {{
                color: {COLORS['text_primary']} !important;
                font-size: 1.5rem !important;
                font-weight: 600 !important;
            }}

            .stButton > button {{
                border-radius: 6px !important;
                font-weight: 600 !important;
                padding: 0.6rem 1.2rem !important;
                border: 1px solid {COLORS['border_primary']} !important;
                background: transparent !important;
                color: #000 !important;
                box-shadow: none !important;
                transition: all 0.15s ease;
            }}

            .stButton > button[kind="primary"] {{
                background: #ff4b4b !important;
                color: #000 !important;
                border: 1px solid #ff4b4b !important;
            }}

            .stButton > button:hover {{
                border-color: {COLORS['text_secondary']} !important;
            }}

            .stTextInput > div > div > input,
            .stTextArea textarea,
            [data-baseweb="select"] > div {{
                background: {COLORS['bg_secondary']} !important;
                border: 1px solid {COLORS['border_primary']} !important;
                border-radius: 6px !important;
                color: {COLORS['text_primary']} !important;
            }}

            .stTextInput > label,
            .stSelectbox > label,
            .stTextArea > label {{
                color: {COLORS['text_muted']} !important;
                font-size: 0.8rem !important;
            }}

            [data-testid="stDataFrame"] {{
                background: transparent;
                border: 1px solid {COLORS['border_primary']};
                border-radius: 6px;
            }}

            [data-testid="stDataFrame"] thead tr th {{
                background: {COLORS['bg_secondary']} !important;
                color: {COLORS['text_muted']} !important;
                font-size: 0.7rem !important;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }}

            [data-testid="stDataFrame"] tbody tr td {{
                background: transparent !important;
                color: {COLORS['text_secondary']} !important;
                border-bottom: 1px solid {COLORS['border_primary']} !important;
            }}

            [data-testid="stSidebar"] {{
                background: {COLORS['bg_primary']} !important;
                border-right: 1px solid {COLORS['border_primary']} !important;
                height: fit-content !important;
            }}

            [data-testid="stSidebar"] > div:first-child {{
                background: {COLORS['bg_primary']} !important;
            }}

            [data-testid="stSidebar"] a {{
                color: {COLORS['text_muted']} !important;
                font-weight: 500;
                padding: 0.45rem 0.4rem !important;
                border-radius: 6px;
            }}

            [data-testid="stSidebar"] a:hover {{
                color: {COLORS['text_primary']} !important;
                background: {COLORS['bg_secondary']} !important;
            }}

            [data-testid="stSidebar"] a[aria-current="page"] {{
                color: {COLORS['text_primary']} !important;
                background: {COLORS['bg_secondary']} !important;
                font-weight: 600;
            }}

            .section-title {{
                color: {COLORS['text_muted']};
                font-size: 0.7rem;
                font-weight: 600;
                letter-spacing: 0.1em;
                margin: 1rem 0 0.35rem;
            }}

            .sidebar-footer {{
                margin-top: 4.5rem;
                color: {COLORS['text_muted']};
                font-size: 0.75rem;
                border-top: 1px solid {COLORS['border_primary']};
                padding-top: 0.9rem;
            }}

            .pill {{
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                padding: 0.25rem 0.6rem;
                border-radius: 999px;
                border: 1px solid {COLORS['border_primary']};
                font-size: 0.7rem;
                color: {COLORS['text_secondary']};
            }}

            .pill.success {{
                border-color: rgba(34, 197, 94, 0.4);
                color: {COLORS['success']};
            }}

            .pill.warning {{
                border-color: rgba(245, 158, 11, 0.4);
                color: {COLORS['warning']};
            }}

            .hero {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                border: 1px solid {COLORS['border_primary']};
                border-radius: 8px;
                padding: 1.1rem 1.3rem;
                background: {COLORS['bg_secondary']};
                margin-bottom: 1.6rem;
            }}

            .hero-title {{
                font-size: 1.1rem;
                color: {COLORS['text_primary']};
                font-weight: 600;
            }}

            .hero-subtitle {{
                color: {COLORS['text_muted']};
                font-size: 0.85rem;
                margin-top: 0.2rem;
            }}

            .card {{
                border: 1px solid {COLORS['border_primary']};
                border-radius: 8px;
                padding: 1.2rem;
                background: {COLORS['bg_secondary']};
            }}

            .card-title {{
                font-size: 0.9rem;
                color: {COLORS['text_primary']};
                font-weight: 600;
                margin-bottom: 0.75rem;
            }}

            .risk-banner {{
                border: 1px solid {COLORS['border_primary']};
                border-radius: 8px;
                padding: 1rem 1.1rem;
                margin-bottom: 1.4rem;
                background: transparent;
            }}

            .risk-banner-value {{
                font-size: 1.2rem;
                font-weight: 600;
            }}

            .risk-value-high {{ color: {COLORS['error']}; }}
            .risk-value-medium {{ color: {COLORS['warning']}; }}
            .risk-value-low {{ color: {COLORS['success']}; }}

            [data-testid="stSidebarNav"] {{
                display: none !important;
            }}
        
            [data-testid="stHeader"] {{
                background: transparent !important;
            }}

            /* Custom Sidebar Open Button */
            [data-testid="collapsedControl"] {{
                background-color: {COLORS['bg_secondary']} !important;
                border: 1px solid {COLORS['border_primary']} !important;
                border-radius: 8px !important;
                color: {COLORS['text_primary']} !important;
                padding: 0.4rem !important;
                margin: 1rem !important;
                transition: all 0.2s ease !important;
                z-index: 999999;
            }}
            [data-testid="collapsedControl"]:hover {{
                background-color: {COLORS['bg_tertiary']} !important;
                border-color: {COLORS['accent']} !important;
            }}
            [data-testid="collapsedControl"] svg {{
                fill: {COLORS['text_primary']} !important;
                color: {COLORS['text_primary']} !important;
            }}

            /* Custom Sidebar Close Button */
            [data-testid="stSidebarCollapseButton"], [data-testid="stSidebar"] button[kind="header"] {{
                background-color: {COLORS['bg_secondary']} !important;
                border: 1px solid {COLORS['border_primary']} !important;
                border-radius: 8px !important;
                color: {COLORS['text_primary']} !important;
                transition: all 0.2s ease !important;
            }}
            [data-testid="stSidebarCollapseButton"]:hover, [data-testid="stSidebar"] button[kind="header"]:hover {{
                background-color: {COLORS['bg_tertiary']} !important;
                border-color: {COLORS['accent']} !important;
            }}
            [data-testid="stSidebarCollapseButton"] svg, [data-testid="stSidebar"] button[kind="header"] svg {{
                fill: {COLORS['text_primary']} !important;
                color: {COLORS['text_primary']} !important;
            }}

            /* Enforce Custom Logo Size and Sidebar Header Padding */
            [data-testid="stSidebarHeader"] {{
                padding: 2.5rem 1.5rem 0.5rem 1.5rem !important;
            }}
            
            [data-testid="stSidebarHeader"] img{{
                height: 4.5rem !important;
            }}
            
            [data-testid="stLogoLink"] {{
                height: 4.5rem !important;
            }}
            [data-testid="stLogoLink"] img {{
                height: 4.5rem !important;
                width: auto !important;
                object-fit: contain !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="page-title">{title}</div>
        <div class="page-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str) -> None:
    st.markdown(f"<div class=\"section-header\">{title}</div>", unsafe_allow_html=True)


def render_top_bar(title: str, pill_text: str | None = None, pill_kind: str = "") -> None:
    pill_html = ""
    if pill_text:
        pill_html = f"<div class=\"pill {pill_kind}\">{pill_text}</div>"

    st.markdown(
        f"""
        <div class="hero">
            <div>
                <div class="hero-title">{title}</div>
                <div class="hero-subtitle">Risk framework overview</div>
            </div>
            {pill_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_topbar(title: str) -> None:
    render_top_bar(title)
