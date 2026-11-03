"""Audit trail persistence utilities.

Recommended defaults:
- Persistent JSON storage across refreshes/reruns.
- CSV export for compliance/reporting workflows.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path

from app.models.audit_trail import AuditEntry


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = PROJECT_ROOT / "logs" / "audit_trails"
AUDIT_FILE = AUDIT_DIR / "entries.json"


def _ensure_store() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    if not AUDIT_FILE.exists():
        AUDIT_FILE.write_text("[]", encoding="utf-8")


def _read_entries() -> list[AuditEntry]:
    _ensure_store()
    raw = AUDIT_FILE.read_text(encoding="utf-8")
    if not raw.strip():
        return []

    try:
        entries = json.loads(raw)
    except json.JSONDecodeError:
        return []

    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict)]


def _write_entries(entries: list[AuditEntry]) -> None:
    _ensure_store()
    AUDIT_FILE.write_text(json.dumps(entries, ensure_ascii=True, indent=2), encoding="utf-8")


def now_utc_iso() -> str:
    """Return UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def save_audit_entry(entry: AuditEntry) -> None:
    """Persist one audit entry."""
    entries = _read_entries()
    entries.append(entry)
    _write_entries(entries)


def get_audit_trail(ticket_id: str | None = None) -> list[AuditEntry]:
    """Load audit history, optionally filtered by ticket id."""
    entries = _read_entries()
    if ticket_id is None:
        return list(reversed(entries))
    filtered = [entry for entry in entries if entry.get("ticket_id") == ticket_id]
    return list(reversed(filtered))


def export_audit_trail_csv(ticket_ids: list[str] | None = None) -> bytes:
    """Export all or selected ticket audit entries as CSV bytes."""
    entries = _read_entries()
    if ticket_ids:
        include = set(ticket_ids)
        entries = [entry for entry in entries if entry.get("ticket_id") in include]

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "timestamp_utc",
            "ticket_id",
            "ticket_index",
            "risk_level",
            "confidence_pct",
            "shap_drivers",
            "reasoning",
            "strategy",
        ],
    )
    writer.writeheader()
    writer.writerows(entries)
    return output.getvalue().encode("utf-8")
