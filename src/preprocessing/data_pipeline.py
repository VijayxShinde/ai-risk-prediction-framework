import logging
import os
from importlib import import_module
from typing import Any, Dict, List

import numpy as np
import pandas as pd

# Constants
from src.config import Paths, get_daily_burn_rate

RAW_DATA_PATH = str(Paths.RAW_JIRA_DATA)
PROCESSED_DATA_PATH = str(Paths.ML_READY_DATA)
SAMPLE_SIZE = 10000
DAILY_BURN_RATE = get_daily_burn_rate()

LOGGER = logging.getLogger("preprocessing.pipeline")
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)
    LOGGER.propagate = False


def _normalize_jira_schema(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "Issue key": "Issue_key",
        "Issue id": "Issue_ID",
        "Issue Type": "Issue_Type",
        "Story Points": "Story_Points",
    }
    for source, target in rename_map.items():
        if source in df.columns and target not in df.columns:
            df = df.rename(columns={source: target})

    if "Summary" not in df.columns:
        LOGGER.warning("Summary column missing; creating empty Summary field.")
        df["Summary"] = ""
    if "Description" not in df.columns:
        LOGGER.warning("Description column missing; creating empty Description field.")
        df["Description"] = ""

    return df


def _fetch_jira_issues(sample_size: int) -> List[Dict[str, Any]]:
    module = import_module("src.integrations.jira_client")
    jira_cls = getattr(module, "JiraAPIClient", None)
    if jira_cls is None:
        raise ImportError("Jira integration client is not available")

    base_url = os.getenv("JIRA_URL", "").strip()
    project_key = os.getenv("JIRA_PROJECT_KEY", "").strip()
    user_email = os.getenv("JIRA_USER_EMAIL", "").strip()
    api_token = os.getenv("JIRA_API_TOKEN", "").strip()

    token_payload = {}
    if hasattr(jira_cls, "load_cached_tokens"):
        token_payload = jira_cls.load_cached_tokens()

    access_token = os.getenv("JIRA_OAUTH_ACCESS_TOKEN", "").strip() or token_payload.get("access_token", "")
    cloud_id = os.getenv("JIRA_OAUTH_CLOUD_ID", "").strip() or token_payload.get("cloud_id", "")
    refresh_token = token_payload.get("refresh_token", "")
    token_expires_at = float(token_payload.get("token_expires_at", 0.0))

    if not access_token and not (user_email and api_token):
        raise FileNotFoundError(
            "raw_jira_data.csv not found and Jira API sync failed. "
            "Please log into the Streamlit app to authenticate Jira first."
        )

    client = jira_cls(
        base_url=base_url,
        project_key=project_key,
        access_token=access_token,
        cloud_id=cloud_id,
        refresh_token=refresh_token,
        token_expires_at=token_expires_at,
        user_email=user_email,
        api_token=api_token,
    )

    if hasattr(client, "sync_issues"):
        return client.sync_issues(max_results=sample_size)

    jql_query = None
    if hasattr(client, "default_jql"):
        jql_query = client.default_jql()
    issues = client.fetch_issues(jql_query or f"project = {project_key}")
    if hasattr(client, "issues_to_metrics"):
        return client.issues_to_metrics(issues)
    return issues


def load_and_sample_data(path: str, sample_size: int) -> pd.DataFrame:
    LOGGER.info("[1/6] Loading data from %s...", path)
    if not os.path.exists(path):
        LOGGER.warning("Raw Jira CSV not found. Attempting Jira API sync...")
        try:
            rows = _fetch_jira_issues(sample_size)
        except Exception as exc:
            LOGGER.error("Jira API sync failed: %s", exc)
            raise FileNotFoundError(
                "raw_jira_data.csv not found and Jira API sync failed. "
                "Please log into the Streamlit app to authenticate Jira first."
            ) from exc

        if not rows:
            raise FileNotFoundError(
                "raw_jira_data.csv not found and Jira API sync failed. "
                "Please log into the Streamlit app to authenticate Jira first."
            )

        df = pd.DataFrame(rows)
        df.to_csv(path, index=False)
        LOGGER.info("Saved Jira issues to %s", path)
    else:
        df = pd.read_csv(path)

    df = _normalize_jira_schema(df)
    if len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42)
    return df


def generate_metrics_with_signals(df):
    LOGGER.info("[2/6] Generating synthetic metrics with hidden signals...")

    defaults = {
        "Priority": "Medium",
        "Issue_Type": "Task",
        "Assignee_Seniority": "Mid",
        "Story_Points": 3.0,
    }
    for column, fallback in defaults.items():
        if column not in df.columns:
            LOGGER.warning("Missing %s column; defaulting to %s", column, fallback)
            df[column] = fallback

    # Base Estimation
    if "Estimated_Days" not in df.columns:
        df["Estimated_Days"] = np.random.randint(2, 15, size=len(df))
    if "Budget_Allocated" not in df.columns:
        df["Budget_Allocated"] = df["Estimated_Days"] * DAILY_BURN_RATE

    # HIDDEN SIGNALS: Determine Actual Days based on metadata
    def calculate_actuals(row):
        base_days = row["Estimated_Days"]
        multiplier = 1.0

        # Signal 1: Junior + High Story Points = Delay
        if row["Assignee_Seniority"] == "Junior" and row["Story_Points"] >= 8:
            multiplier += 0.6

        # Signal 2: Bug + High Priority = Complexity/Delay
        if row["Issue_Type"] == "Bug" and row["Priority"] == "High":
            multiplier += 0.4

        # Signal 3: Senior + Small tasks = Efficiency
        if row["Assignee_Seniority"] == "Senior" and row["Story_Points"] <= 3:
            multiplier -= 0.2

        # Add some random noise
        noise = np.random.normal(1.1, 0.2)
        actual = (base_days * multiplier) * noise
        return max(1, round(actual))

    if "Actual_Days" not in df.columns:
        df["Actual_Days"] = df.apply(calculate_actuals, axis=1)
    if "Cost_Consumed" not in df.columns:
        df["Cost_Consumed"] = df["Actual_Days"] * DAILY_BURN_RATE

    return df


def calculate_risk_level(df):
    LOGGER.info("[3/6] Calculating target variable: Risk_Level...")

    def determine_risk(row):
        cost_overrun_pct = (row["Cost_Consumed"] / row["Budget_Allocated"]) - 1
        days_overrun = row["Actual_Days"] - row["Estimated_Days"]

        if cost_overrun_pct > 0.25 or days_overrun >= 4:
            return "High"
        elif cost_overrun_pct > 0.10 or days_overrun >= 2:
            return "Medium"
        else:
            return "Low"

    df["Risk_Level"] = df.apply(determine_risk, axis=1)
    LOGGER.info("Risk Level Distribution:\n%s", df["Risk_Level"].value_counts())
    return df


def clean_for_ml(df):
    LOGGER.info("[4/6] Cleaning dataset for ML export...")
    # Preserve ALL signals and metadata
    cols_to_keep = [
        "Priority",
        "Issue_Type",
        "Assignee_Seniority",
        "Story_Points",
        "Estimated_Days",
        "Budget_Allocated",
        "Actual_Days",
        "Cost_Consumed",
        "Summary",
        "Description",
        "Risk_Level",
    ]
    # Filter only existing columns to avoid KeyError
    df_final = df[[col for col in cols_to_keep if col in df.columns]].copy()
    return df_final


def save_processed_data(df, path):
    LOGGER.info("[5/6] Saving processed data to %s...", path)
    df.to_csv(path, index=False)
    LOGGER.info("Pipeline executed successfully.")


if __name__ == "__main__":
    try:
        data = load_and_sample_data(RAW_DATA_PATH, SAMPLE_SIZE)
        data = generate_metrics_with_signals(data)
        data = calculate_risk_level(data)
        data = clean_for_ml(data)
        save_processed_data(data, PROCESSED_DATA_PATH)
    except Exception as e:
        LOGGER.error("Pipeline failed: %s", e)
