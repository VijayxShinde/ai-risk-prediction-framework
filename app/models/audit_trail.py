"""Typed schema for auditor history entries."""

from __future__ import annotations

from typing import TypedDict


class AuditEntry(TypedDict):
    """Represents one prediction + mitigation generation event."""

    ticket_id: str
    ticket_index: int
    timestamp_utc: str
    risk_level: str
    confidence_pct: float
    shap_drivers: str
    strategy: str
    reasoning: str
