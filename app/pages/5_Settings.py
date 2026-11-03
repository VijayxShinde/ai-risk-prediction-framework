"""Settings page for native Streamlit multipage app."""

import streamlit as st

st.set_page_config(layout="wide", initial_sidebar_state="expanded")

from app.utils.styles import inject_global_css
from app.utils.sidebar import render_sidebar
from app.views.settings import render_settings

if not st.session_state.get("authenticated", False):
    st.switch_page("main.py")

inject_global_css()
render_sidebar()
render_settings()
