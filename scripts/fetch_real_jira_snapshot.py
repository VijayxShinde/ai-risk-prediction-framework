#!/usr/bin/env python3
"""Fetch real Jira data snapshot for model training."""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.config import Paths
from src.integrations.jira_client import JiraAPIClient


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _safe_get(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def generate_heuristic_risk_label(issue: Dict[str, Any]) -> str:
    """Generate synthetic risk label based on issue patterns."""
    risk_signals = 0

    created = _safe_get(issue.get("Created"))
    if not issue.get("Resolution") and created:
        try:
            created_year = int(created.split("-")[0])
            if created_year < datetime.utcnow().year:
                risk_signals += 2
        except ValueError:
            pass

    comment_count = issue.get("comment_count", 0)
    if comment_count > 10:
        risk_signals += 2
    elif comment_count > 5:
        risk_signals += 1

    if issue.get("Issue Type") == "Bug" and issue.get("Priority") in {"High", "Highest"}:
        risk_signals += 2

    if issue.get("Inward issue link (Blocker)"):
        risk_signals += 2

    if risk_signals >= 4:
        return "High"
    if risk_signals >= 2:
        return "Medium"
    return "Low"


def fetch_jira_snapshot(max_issues: int = 5000) -> pd.DataFrame:
    logger.info("Loading Jira client...")
    client = JiraAPIClient(
        base_url=os.getenv("JIRA_URL", "https://atlassian.net"),
        project_key=os.getenv("JIRA_PROJECT_KEY", ""),
        access_token="",
    )

    logger.info("Fetching up to %s issues...", max_issues)
    issues = client.sync_issues(max_results=max_issues)
    if not issues:
        raise ValueError("Empty issue list returned from Jira")

    logger.info("Fetched %s issues", len(issues))
    df = pd.DataFrame(issues)

    key_columns = {
        "Summary": "Summary",
        "Description": "Description",
        "Issue Type": "Issue_Type",
        "Priority": "Priority",
        "Status": "Status",
        "Created": "Created",
        "Updated": "Updated",
        "Assignee": "Assignee",
        "Resolution": "Resolution",
    }

    available_cols = [col for col in key_columns.keys() if col in df.columns]
    if not available_cols:
        logger.warning("Key columns not found, using available columns")
        available_cols = df.columns[:15].tolist()

    df_subset = df[available_cols].copy()
    rename_map = {v: k for k, v in key_columns.items() if v in available_cols}
    df_subset = df_subset.rename(columns=rename_map)

    df_subset["Summary"] = df_subset.get("Summary", "").fillna("Unknown")
    df_subset["Description"] = df_subset.get("Description", "").fillna("")

    logger.info("Generating heuristic risk labels...")
    df_subset["Risk_Level"] = df_subset.apply(
        lambda row: generate_heuristic_risk_label(row.to_dict()), axis=1
    )
    logger.info("Risk distribution:\n%s", df_subset["Risk_Level"].value_counts())

    return df_subset


def main() -> None:
    output_path = Paths.DATA_DIR / "real_jira_snapshot.csv"
    try:
        df = fetch_jira_snapshot(max_issues=5000)
        df.to_csv(output_path, index=False)
        logger.info("Saved %s issues to %s", len(df), output_path)
        logger.info("Shape: %s", df.shape)
        logger.info("Columns: %s", list(df.columns))
    except Exception as exc:
        logger.error("Failed to fetch Jira snapshot: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
