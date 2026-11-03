"""Audit trail viewer component for ticket-level history."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.utils.audit_storage import export_audit_trail_csv, get_audit_trail


def render_audit_trail(ticket_id: str) -> None:
    """Render audit entries for the selected ticket with CSV export."""
    entries = get_audit_trail(ticket_id)
    st.subheader("Audit Trail")

    if not entries:
        st.caption("No audit records yet. Generate a mitigation strategy to create one.")
        return

    frame = pd.DataFrame(entries)
    display = frame[
        ["timestamp_utc", "risk_level", "confidence_pct", "shap_drivers", "strategy"]
    ].copy()
    display.columns = [
        "Timestamp (UTC)",
        "Risk",
        "Confidence %",
        "Top SHAP Drivers",
        "Mitigation Strategy",
    ]

    st.dataframe(display, hide_index=True, use_container_width=True)

    csv_bytes = export_audit_trail_csv([ticket_id])
    st.download_button(
        "Download Audit CSV",
        data=csv_bytes,
        file_name=f"audit_{ticket_id}.csv",
        mime="text/csv",
        use_container_width=True,
    )
