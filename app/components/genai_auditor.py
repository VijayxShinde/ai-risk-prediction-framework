import streamlit as st
import time

from app.utils.audit_storage import now_utc_iso, save_audit_entry
from src.mitigation.llm_agent import generate_mitigation_strategy

MITIGATION_TTL = 600  # 10 minutes

def render_mitigation_engine(
    ticket_id, risk_level, shap_drivers, audit_context=None, button_key=None
):
    provider = st.session_state.get("genai_provider", "NVIDIA (Qwen 3.5)")
    st.subheader(f"{provider} Autonomous Auditor")

    if "mitigation_cache" not in st.session_state:
        st.session_state.mitigation_cache = {}

    cached_result = None
    if ticket_id in st.session_state.mitigation_cache:
        entry = st.session_state.mitigation_cache[ticket_id]
        if time.time() - entry["timestamp"] < MITIGATION_TTL:
            cached_result = entry["result"]
        else:
            del st.session_state.mitigation_cache[ticket_id]

    if cached_result:
        if cached_result["reasoning_trace"]:
            with st.expander("IEEE Audit Trace (Reasoning)", expanded=True):
                st.info(cached_result["reasoning_trace"])
        if cached_result["final_strategy"]:
            st.markdown("**Mitigation Strategy**")
            st.markdown(cached_result["final_strategy"])
        st.caption(f"Cached (expires in {MITIGATION_TTL // 60} min)")
        return cached_result
    else:
        if st.button(
            "Generate Mitigation Strategy", type="primary", key=button_key
        ):
            with st.spinner(f"Connecting to {provider.split('(')[0].strip()} for analysis..."):
                ticket_details = {
                    "summary": str(shap_drivers.get("summary", "N/A"))
                    if isinstance(shap_drivers, dict)
                    else "N/A",
                    "priority": str(shap_drivers.get("priority", "N/A"))
                    if isinstance(shap_drivers, dict)
                    else "N/A",
                    "assignee_seniority": str(
                        shap_drivers.get("assignee_seniority", "N/A")
                    )
                    if isinstance(shap_drivers, dict)
                    else "N/A",
                    "estimated_days": int(shap_drivers.get("estimated_days", 0))
                    if isinstance(shap_drivers, dict)
                    else 0,
                    "story_points": int(shap_drivers.get("story_points", 0))
                    if isinstance(shap_drivers, dict)
                    else 0,
                    "budget_allocated": float(shap_drivers.get("budget_allocated", 0))
                    if isinstance(shap_drivers, dict)
                    else 0,
                }

                result = generate_mitigation_strategy(
                    ticket_details=ticket_details,
                    risk_level=risk_level,
                    top_risk_factors=shap_drivers.get("top_factors", [])
                    if isinstance(shap_drivers, dict)
                    else [],
                )

                st.session_state.mitigation_cache[ticket_id] = {
                    "result": result,
                    "timestamp": time.time(),
                }

                if isinstance(audit_context, dict):
                    ticket_label = str(audit_context.get("ticket_id", f"TICKET-{ticket_id}"))
                    confidence_pct = float(audit_context.get("confidence_pct", 0.0))
                    top_drivers = audit_context.get("top_drivers", [])
                    save_audit_entry(
                        {
                            "ticket_id": ticket_label,
                            "ticket_index": int(ticket_id),
                            "timestamp_utc": now_utc_iso(),
                            "risk_level": str(risk_level),
                            "confidence_pct": confidence_pct,
                            "shap_drivers": ", ".join(top_drivers),
                            "strategy": str(result.get("final_strategy", "")),
                            "reasoning": str(result.get("reasoning_trace", "")),
                        }
                    )

                st.rerun()

        st.info(
            "Click the button above to generate an AI-powered mitigation plan for this ticket."
        )
        return None
