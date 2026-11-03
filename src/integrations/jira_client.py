"""Jira API client for issue ingestion and metric extraction."""

from __future__ import annotations

import base64
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib import parse, request
from urllib.error import HTTPError, URLError

from .oauth_handler import JiraOAuthHandler
from src.config import get_jira_story_points_field, get_jira_workday_hours


class JiraConnectionError(Exception):
    """Raised when Jira connectivity fails."""


class InvalidJQLError(Exception):
    """Raised when a provided JQL query is invalid."""


class RateLimitError(Exception):
    """Raised when Jira API rate limits are exceeded."""


class JiraHTTPStatusError(JiraConnectionError):
    """Raised when Jira responds with an HTTP status code."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class JiraCredentials:
    base_url: str
    user_email: str
    api_token: str
    project_key: str
    access_token: str = ""
    cloud_id: str = ""
    refresh_token: str = ""
    token_expires_at: float = 0.0


class JiraAPIClient:
    """Lightweight Jira REST client for project issue ingestion."""

    TOKEN_CACHE_PATH = Path(os.getenv("JIRA_TOKEN_CACHE_PATH", ".jira_tokens.json"))

    def __init__(
        self,
        base_url: str,
        user_email: str = "",
        api_token: str = "",
        project_key: str = "",
        access_token: str = "",
        cloud_id: str = "",
        refresh_token: str = "",
        token_expires_at: float = 0.0,
        oauth_handler: Optional[JiraOAuthHandler] = None,
        timeout_seconds: int = 20,
    ) -> None:
        if not access_token:
            cached = self.load_cached_tokens()
            access_token = cached.get("access_token", "")
            cloud_id = cloud_id or cached.get("cloud_id", "")
            refresh_token = cached.get("refresh_token", "")
            token_expires_at = float(cached.get("token_expires_at", 0.0))

        has_basic = bool(user_email and api_token)
        has_oauth = bool(access_token)
        if not base_url or not project_key or (not has_basic and not has_oauth):
            raise JiraConnectionError("Jira credentials are incomplete")

        self.credentials = JiraCredentials(
            base_url=base_url.rstrip("/"),
            user_email=user_email,
            api_token=api_token,
            project_key=project_key,
            access_token=access_token,
            cloud_id=cloud_id,
            refresh_token=refresh_token,
            token_expires_at=float(token_expires_at or 0.0),
        )
        self.timeout_seconds = timeout_seconds
        if oauth_handler is None and refresh_token:
            try:
                oauth_handler = JiraOAuthHandler.from_env()
            except Exception:
                oauth_handler = None

        self.oauth_handler = oauth_handler
        self.logger = self._setup_logger()

        if self.credentials.access_token:
            self.save_cached_tokens(
                {
                    "access_token": self.credentials.access_token,
                    "refresh_token": self.credentials.refresh_token,
                    "token_expires_at": self.credentials.token_expires_at,
                    "cloud_id": self.credentials.cloud_id,
                }
            )

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("jira.integration")
        if logger.handlers:
            return logger

        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_dir / "jira_integration.log")
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        return logger

    def _auth_header(self) -> Dict[str, str]:
        if self.credentials.access_token:
            self._ensure_valid_oauth_token()
            return {
                "Authorization": f"Bearer {self.credentials.access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

        token_bytes = (
            f"{self.credentials.user_email}:{self.credentials.api_token}".encode(
                "utf-8"
            )
        )

        auth_token = base64.b64encode(token_bytes).decode("ascii")
        return {
            "Authorization": f"Basic {auth_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _ensure_valid_oauth_token(self) -> None:
        if not self.credentials.access_token:
            return

        if not self.credentials.token_expires_at:
            return

        if not JiraOAuthHandler.is_token_expired(self.credentials.token_expires_at):
            return

        if not self.oauth_handler or not self.credentials.refresh_token:
            raise JiraConnectionError(
                "Jira OAuth token expired. Please re-authorize via the Jira Sync page."
            )

        refreshed = self.oauth_handler.refresh_access_token(
            self.credentials.refresh_token
        )
        self.update_oauth_credentials(
            access_token=refreshed.get("access_token", ""),
            refresh_token=refreshed.get("refresh_token")
            or self.credentials.refresh_token,
            token_expires_at=float(refreshed.get("expires_at", 0.0)),
        )

    def _request_json(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if self.credentials.access_token and self.credentials.cloud_id:
            url = f"https://api.atlassian.com/ex/jira/{self.credentials.cloud_id}{endpoint}"
        else:
            url = f"{self.credentials.base_url}{endpoint}"
        if params:
            url = f"{url}?{parse.urlencode(params)}"

        req = request.Request(url, headers=self._auth_header(), method="GET")
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore") if exc.fp else ""
            self.logger.error("Jira HTTP %d: %s", exc.code, body[:300])
            if exc.code == 401:
                raise JiraConnectionError(
                    "Jira OAuth token is invalid or expired. Please re-authorize via the Jira Sync page."
                ) from exc
            if exc.code == 400 and "jql" in body.lower():
                raise InvalidJQLError(body or "Invalid JQL query") from exc
            if exc.code == 429:
                raise RateLimitError("Jira API rate limit exceeded") from exc
            raise JiraHTTPStatusError(
                exc.code,
                f"Jira request failed: HTTP {exc.code}",
            ) from exc
        except URLError as exc:
            raise JiraConnectionError(f"Jira network error: {exc}") from exc

    def fetch_issues(
        self, jql_query: str, max_results: int = 1000
    ) -> List[Dict[str, Any]]:
        """Fetch Jira issues using JQL with pagination."""
        issues: List[Dict[str, Any]] = []
        start_at = 0
        page_size = max(100, min(1000, max_results))

        self.logger.info("Jira JQL query: %s", jql_query)

        sp_field = get_jira_story_points_field()
        while start_at < max_results:
            params = {
                "jql": jql_query,
                "startAt": start_at,
                "maxResults": min(page_size, max_results - start_at),
                "fields": f"summary,description,priority,issuetype,{sp_field},timeoriginalestimate,timespent,created,updated,status",
            }
            try:
                payload = self._request_json("/rest/api/3/search", params)
            except JiraHTTPStatusError as exc:
                if exc.status_code not in (410, 404):
                    raise
                self.logger.info(
                    "Jira /rest/api/3/search returned HTTP %d; retrying with /rest/api/3/search/jql",
                    exc.status_code,
                )
                try:
                    payload = self._request_json("/rest/api/3/search/jql", params)
                except JiraHTTPStatusError:
                    self.logger.info(
                        "Jira /rest/api/3/search/jql also failed; retrying with /rest/api/2/search"
                    )
                    payload = self._request_json("/rest/api/2/search", params)
            page = payload.get("issues", [])
            if not page:
                break

            issues.extend(page)
            start_at += len(page)
            if len(page) < params["maxResults"]:
                break

        self.logger.info("Fetched %d Jira issues", len(issues))
        return issues

    def default_jql(self) -> str:
        """Return default project-scoped JQL for all issues."""
        return f"project = {self.credentials.project_key}"

    def sync_issues(
        self,
        jql_query: Optional[str] = None,
        max_results: int = 250,
    ) -> List[Dict[str, Any]]:
        """Fetch Jira issues and convert to model-ready metric rows."""
        query = (jql_query or "").strip() or self.default_jql()
        issues = self.fetch_issues(query, max_results=max_results)
        return self.issues_to_metrics(issues)

    def issues_to_metrics(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert raw Jira payload list into model-ready metric rows."""
        rows: List[Dict[str, Any]] = []
        for issue in issues:
            row = self.extract_metrics(issue)
            row["Issue_key"] = issue.get("key", "")
            row["Issue_ID"] = issue.get("id", "")
            rows.append(row)
        return rows

    def update_oauth_credentials(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_expires_at: float = 0.0,
        cloud_id: Optional[str] = None,
    ) -> None:
        """Update OAuth credentials after code exchange or refresh."""
        self.credentials.access_token = access_token
        if refresh_token is not None:
            self.credentials.refresh_token = refresh_token
        if token_expires_at:
            self.credentials.token_expires_at = float(token_expires_at)
        if cloud_id is not None:
            self.credentials.cloud_id = cloud_id

        if self.credentials.access_token:
            self.save_cached_tokens(
                {
                    "access_token": self.credentials.access_token,
                    "refresh_token": self.credentials.refresh_token,
                    "token_expires_at": self.credentials.token_expires_at,
                    "cloud_id": self.credentials.cloud_id,
                }
            )

    @classmethod
    def load_cached_tokens(cls) -> Dict[str, Any]:
        """Load cached OAuth tokens from disk."""
        if not cls.TOKEN_CACHE_PATH.exists():
            return {}
        try:
            payload = json.loads(cls.TOKEN_CACHE_PATH.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                return {}
            return payload
        except (OSError, json.JSONDecodeError):
            return {}

    @classmethod
    def save_cached_tokens(cls, payload: Dict[str, Any]) -> None:
        """Persist OAuth tokens to disk."""
        cls.TOKEN_CACHE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def clear_cached_tokens(cls) -> None:
        """Remove OAuth tokens from disk."""
        if cls.TOKEN_CACHE_PATH.exists():
            try:
                cls.TOKEN_CACHE_PATH.unlink()
            except OSError:
                pass

    def extract_metrics(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Map Jira issue fields to model-ready metrics used by dashboard engines."""
        fields = issue.get("fields", {})
        summary = fields.get("summary") or ""
        description = fields.get("description") or ""

        # Extract Story Points
        sp_field = get_jira_story_points_field()
        story_points = fields.get(sp_field)
        story_points = float(story_points) if story_points is not None else 0.0

        workday_seconds = get_jira_workday_hours() * 3600.0
        estimated_seconds = fields.get("timeoriginalestimate") or 0
        spent_seconds = fields.get("timespent") or 0
        estimated_days = max(0.0, round(float(estimated_seconds) / workday_seconds, 2))
        actual_days = max(0.0, round(float(spent_seconds) / workday_seconds, 2))

        priority = (fields.get("priority") or {}).get("name", "Medium")
        issue_type = (fields.get("issuetype") or {}).get("name", "Task")
        
        assignee = fields.get("assignee")
        assignee_name = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"

        return {
            "Priority": priority,
            "Issue_Type": issue_type,
            "Assignee_Name": assignee_name,
            "Story_Points": story_points,
            "Estimated_Days": estimated_days,
            "Actual_Days": actual_days,
            "Summary": summary,
            "Description": description,
        }
