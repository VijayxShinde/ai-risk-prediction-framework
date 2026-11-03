"""Unit tests for Jira OAuth handler and Jira API client helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.integrations.jira_client import JiraAPIClient, JiraConnectionError
from src.integrations.oauth_handler import JiraOAuthError, JiraOAuthHandler


pytestmark = pytest.mark.unit


@pytest.fixture
def oauth_handler() -> JiraOAuthHandler:
    return JiraOAuthHandler(
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri="http://localhost:8501",
    )


def test_get_authorization_url_contains_required_params(oauth_handler: JiraOAuthHandler):
    url = oauth_handler.get_authorization_url(state="abc123")

    assert "client_id=client-id" in url
    assert "state=abc123" in url
    assert "response_type=code" in url


@patch("src.integrations.oauth_handler.requests.post")
def test_exchange_auth_code_success(mock_post: MagicMock, oauth_handler: JiraOAuthHandler):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "access_token": "access",
        "refresh_token": "refresh",
        "expires_in": 3600,
    }
    mock_post.return_value = response

    token_data = oauth_handler.exchange_auth_code("code-123")

    assert token_data["access_token"] == "access"
    assert token_data["refresh_token"] == "refresh"
    assert token_data["expires_at"] > 0


@patch("src.integrations.oauth_handler.requests.get")
def test_fetch_cloud_id_success(mock_get: MagicMock, oauth_handler: JiraOAuthHandler):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = [{"id": "cloud-xyz", "name": "Demo"}]
    mock_get.return_value = response

    cloud_id = oauth_handler.fetch_cloud_id("token-123")
    assert cloud_id == "cloud-xyz"


@patch("src.integrations.oauth_handler.requests.post")
def test_refresh_access_token_success(mock_post: MagicMock, oauth_handler: JiraOAuthHandler):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "access_token": "new-access",
        "refresh_token": "new-refresh",
        "expires_in": 1800,
    }
    mock_post.return_value = response

    token_data = oauth_handler.refresh_access_token("old-refresh")
    assert token_data["access_token"] == "new-access"
    assert token_data["expires_at"] > 0


def test_fetch_cloud_id_raises_when_empty_resources(oauth_handler: JiraOAuthHandler):
    with patch("src.integrations.oauth_handler.requests.get") as mock_get:
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = []
        mock_get.return_value = response

        with pytest.raises(JiraOAuthError):
            oauth_handler.fetch_cloud_id("token-123")


def test_jira_client_sync_issues_returns_mapped_rows():
    client = JiraAPIClient(
        base_url="https://example.atlassian.net",
        project_key="RISK",
        access_token="token",
        cloud_id="cloud-1",
    )

    issues = [
        {
            "id": "10001",
            "key": "RISK-1",
            "fields": {
                "summary": "Bug in release",
                "description": "Investigate deploy issue",
                "priority": {"name": "High"},
                "issuetype": {"name": "Bug"},
                "customfield_10016": 8,
                "timeoriginalestimate": 57600,
                "timespent": 86400,
            },
        }
    ]

    with patch.object(client, "fetch_issues", return_value=issues):
        rows = client.sync_issues(max_results=20)

    assert len(rows) == 1
    assert rows[0]["Issue_key"] == "RISK-1"
    assert rows[0]["Priority"] == "High"


def test_jira_client_requires_auth_mode():
    with patch.object(JiraAPIClient, "load_cached_tokens", return_value={}):
        with pytest.raises(JiraConnectionError):
            JiraAPIClient(
                base_url="https://example.atlassian.net",
                project_key="RISK",
            )
