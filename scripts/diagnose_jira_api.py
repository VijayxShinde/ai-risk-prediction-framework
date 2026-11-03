"""Diagnostic script to test Jira API connectivity and debug HTTP 410 issues."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv()

from src.integrations.jira_client import JiraAPIClient
from src.integrations.oauth_handler import JiraOAuthHandler


def main():
    cached = JiraAPIClient.load_cached_tokens()
    print("[1] Token Cache:", json.dumps({k: v[:20] + "..." if isinstance(v, str) and len(v) > 20 else v for k, v in cached.items()}, indent=2))

    access_token = cached.get("access_token", "")
    cloud_id = cached.get("cloud_id", "")
    refresh_token = cached.get("refresh_token", "")
    expires_at = cached.get("token_expires_at", 0)

    if not access_token:
        print("[ERROR] No cached access token. Run Jira OAuth flow first.")
        return

    handler = JiraOAuthHandler.from_env()
    if handler.is_token_expired(float(expires_at)):
        if refresh_token:
            print("[INFO] Token expired, refreshing...")
            refreshed = handler.refresh_access_token(refresh_token)
            access_token = refreshed.get("access_token", "")
            JiraAPIClient.save_cached_tokens({
                "access_token": access_token,
                "refresh_token": refreshed.get("refresh_token", refresh_token),
                "token_expires_at": refreshed.get("expires_at", 0),
                "cloud_id": cloud_id,
            })
            print("[INFO] Token refreshed successfully.")
        else:
            print("[WARN] Token expired and no refresh token available.")
            print("[WARN] You MUST re-authorize via Jira Sync page to get a fresh token.")
            print("[WARN] For free Atlassian developer apps, access tokens have a 1-hour lifetime with NO refresh.")
            print("[INFO] Proceeding with expired token to test — this will likely fail with 401.")

    jira_url = os.getenv("JIRA_URL", "").strip()
    project_key = os.getenv("JIRA_PROJECT_KEY", "RISK").strip()

    print(f"\n[2] Config: jira_url={jira_url}, project_key={project_key}, cloud_id={cloud_id}")

    import json as _json
    import urllib.request as _req
    import urllib.error as _err

    base_url = f"https://api.atlassian.com/ex/jira/{cloud_id}" if cloud_id else jira_url.rstrip("/")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    search_endpoints = [
        "/rest/api/3/search",
        "/rest/api/3/search/jql",
        "/rest/api/2/search",
    ]

    for endpoint in search_endpoints:
        params = f"jql=project={project_key}&maxResults=5"
        url = f"{base_url}{endpoint}?{params}"
        print(f"\n[3] Trying: GET {url}")
        try:
            req = _req.Request(url, headers=headers, method="GET")
            with _req.urlopen(req, timeout=15) as resp:
                data = _json.loads(resp.read().decode("utf-8"))
                issue_count = len(data.get("issues", []))
                print(f"    HTTP {resp.status}: {issue_count} issues found")
                if issue_count > 0:
                    print(f"    Sample issue keys: {[i.get('key') for i in data.get('issues', [])[:3]]}")
        except _err.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")[:300]
            print(f"    HTTP {exc.code}: {body}")
        except Exception as exc:
            print(f"    ERROR: {exc}")

    print("\n[4] Testing accessible resources:")
    resources_url = "https://api.atlassian.com/oauth/token/accessible-resources"
    req = _req.Request(resources_url, headers=headers, method="GET")
    try:
        with _req.urlopen(req, timeout=15) as resp:
            resources = _json.loads(resp.read().decode("utf-8"))
            for r in resources:
                print(f"    id={r.get('id')}, name={r.get('name')}, url={r.get('url')}, scopes={r.get('scopes', [])}")
    except Exception as exc:
        print(f"    ERROR: {exc}")


if __name__ == "__main__":
    main()