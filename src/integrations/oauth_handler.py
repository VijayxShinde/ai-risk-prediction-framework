"""OAuth 2.0 (3LO) helpers for Jira Cloud integration."""

from __future__ import annotations

import logging
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Sequence
from urllib.parse import urlencode

import requests

try:
    from requests_oauthlib import OAuth2Session
except Exception:  # pragma: no cover - fallback when dependency is unavailable
    OAuth2Session = None


AUTH_BASE_URL = "https://auth.atlassian.com/authorize"
TOKEN_URL = "https://auth.atlassian.com/oauth/token"
ACCESSIBLE_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"


class JiraOAuthError(Exception):
    """Raised when Jira OAuth operations fail."""


@dataclass
class JiraOAuthConfig:
    """Configuration required for Jira OAuth 3LO."""

    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: Sequence[str]


class JiraOAuthHandler:
    """Manage Jira OAuth authorization URL, token exchange, and cloud lookup."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: Optional[Sequence[str]] = None,
        timeout_seconds: int = 20,
    ) -> None:
        if not client_id or not client_secret or not redirect_uri:
            raise JiraOAuthError("Missing OAuth configuration values")

        self.config = JiraOAuthConfig(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=tuple(scopes or ["read:jira-work", "read:jira-user", "read:account", "offline_access"]),
        )
        self.timeout_seconds = timeout_seconds
        self.logger = self._setup_logger()

    @classmethod
    def from_env(cls) -> "JiraOAuthHandler":
        """Build handler from environment variables."""
        return cls(
            client_id=os.getenv("JIRA_OAUTH_CLIENT_ID", ""),
            client_secret=os.getenv("JIRA_OAUTH_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("JIRA_OAUTH_REDIRECT_URI", ""),
        )

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("jira.oauth")
        if logger.handlers:
            return logger

        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_dir / "jira_oauth.log")
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        return logger

    @staticmethod
    def generate_state() -> str:
        """Generate CSRF state value for OAuth requests."""
        return uuid.uuid4().hex

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate Jira authorization URL for OAuth 3LO."""
        state_value = state or self.generate_state()
        scope_str = " ".join(self.config.scopes)

        if OAuth2Session is not None:
            session = OAuth2Session(
                client_id=self.config.client_id,
                redirect_uri=self.config.redirect_uri,
                scope=list(self.config.scopes),
            )
            auth_url, _ = session.authorization_url(
                AUTH_BASE_URL,
                state=state_value,
                audience="api.atlassian.com",
                prompt="consent",
            )
            return auth_url

        params = {
            "audience": "api.atlassian.com",
            "client_id": self.config.client_id,
            "scope": scope_str,
            "redirect_uri": self.config.redirect_uri,
            "state": state_value,
            "response_type": "code",
            "prompt": "consent",
        }
        return f"{AUTH_BASE_URL}?{urlencode(params)}"

    def exchange_auth_code(self, auth_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        if not auth_code:
            raise JiraOAuthError("Missing authorization code")

        payload = {
            "grant_type": "authorization_code",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "code": auth_code,
            "redirect_uri": self.config.redirect_uri,
        }

        try:
            response = requests.post(TOKEN_URL, json=payload, timeout=self.timeout_seconds)
            response.raise_for_status()
            token_data = response.json()
        except requests.RequestException as exc:
            self.logger.error("OAuth code exchange failed: %s", exc)
            raise JiraOAuthError("Failed to exchange Jira OAuth code") from exc

        expires_in = int(token_data.get("expires_in", 3600))
        token_data["expires_at"] = time.time() + max(0, expires_in)
        self.logger.info("OAuth code exchange successful")
        return token_data

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an expired access token using refresh token."""
        if not refresh_token:
            raise JiraOAuthError("Missing refresh token")

        payload = {
            "grant_type": "refresh_token",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "refresh_token": refresh_token,
        }

        try:
            response = requests.post(TOKEN_URL, json=payload, timeout=self.timeout_seconds)
            response.raise_for_status()
            token_data = response.json()
        except requests.RequestException as exc:
            self.logger.error("OAuth token refresh failed: %s", exc)
            raise JiraOAuthError("Failed to refresh Jira OAuth token") from exc

        expires_in = int(token_data.get("expires_in", 3600))
        token_data["expires_at"] = time.time() + max(0, expires_in)
        self.logger.info("OAuth token refresh successful")
        return token_data

    def fetch_cloud_id(self, access_token: str, target_url: Optional[str] = None) -> str:
        """Fetch Atlassian Cloud ID from accessible resources endpoint."""
        if not access_token:
            raise JiraOAuthError("Missing access token")

        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        try:
            response = requests.get(
                ACCESSIBLE_RESOURCES_URL,
                headers=headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            resources = response.json()
        except requests.RequestException as exc:
            self.logger.error("Cloud ID lookup failed: %s", exc)
            raise JiraOAuthError("Failed to fetch Atlassian cloud resources") from exc

        if not isinstance(resources, list) or not resources:
            raise JiraOAuthError("No accessible Jira cloud resources found")

        # Match resource URL with target_url or JIRA_URL environment variable
        target = (target_url or os.getenv("JIRA_URL") or "").strip().lower()
        if target:
            from urllib.parse import urlparse
            parsed_target = urlparse(target)
            target_host = parsed_target.netloc or parsed_target.path
            target_host = target_host.strip("/")

            for res in resources:
                res_url = str(res.get("url", "")).strip().lower()
                parsed_res = urlparse(res_url)
                res_host = parsed_res.netloc or parsed_res.path
                res_host = res_host.strip("/")
                if target_host and res_host == target_host:
                    cloud_id = str(res.get("id", "")).strip()
                    if cloud_id:
                        self.logger.info("Resolved Atlassian cloud id from matching URL: %s -> %s", target, cloud_id)
                        return cloud_id

        cloud_id = str(resources[0].get("id", "")).strip()
        if not cloud_id:
            raise JiraOAuthError("Cloud ID missing in accessible resources response")

        self.logger.info("Resolved Atlassian cloud id (fallback to first resource)")
        return cloud_id

    @staticmethod
    def is_token_expired(expires_at: float, skew_seconds: int = 60) -> bool:
        """Return True when token is expired or about to expire."""
        if not expires_at:
            return True
        return time.time() >= (expires_at - skew_seconds)
