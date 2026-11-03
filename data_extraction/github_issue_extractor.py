#!/usr/bin/env python3
"""
Extract issues from GitHub repositories
"""

import requests
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
import os

class GitHubIssueExtractor:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.session = requests.Session()
        if self.token:
            self.session.headers.update(
                {"Authorization": f"token {self.token}"}
            )
    
    def fetch_issues(self, owner: str, repo: str, 
                    state: str = "all", max_results: int = 200) -> List[Dict]:
        """Fetch all issues from a repository"""
        issues = []
        page = 1
        
        while len(issues) < max_results:
            url = f"https://api.github.com/repos/{owner}/{repo}/issues"
            params = {
                "state": state,
                "page": page,
                "per_page": min(100, max_results - len(issues)),
                "sort": "created",
                "direction": "asc"
            }
            
            resp = self.session.get(url, params=params, timeout=30)
            
            if resp.status_code == 404:
                print(f"Repository not found: {owner}/{repo}")
                break
            elif resp.status_code != 200:
                print(f"Error: {resp.status_code}")
                break
            
            data = resp.json()
            if not data:
                break
            
            issues.extend(data)
            print(f"Fetched page {page} ({len(issues)} total)")
            
            # Check for rate limit
            remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
            if remaining < 10:
                print("Rate limit approaching, exiting early")
                break
            
            page += 1
        
        return issues[:max_results]
    
    def normalize_issues(self, issues: List[Dict], 
                        repo_name: str) -> pd.DataFrame:
        """Convert GitHub issues to normalized DataFrame"""
        normalized = []
        
        for issue in issues:
            # Skip pull requests
            if "pull_request" in issue:
                continue
            
            closed_at = None
            if issue.get("closed_at"):
                closed_at = int(
                    datetime.fromisoformat(
                        issue["closed_at"].replace("Z", "+00:00")
                    ).timestamp()
                )
            
            created_at = int(
                datetime.fromisoformat(
                    issue["created_at"].replace("Z", "+00:00")
                ).timestamp()
            )
            
            time_to_resolution = None
            if closed_at:
                time_to_resolution = (closed_at - created_at) / (24 * 3600)
            
            normalized.append({
                "id": f"gh-{issue['number']}",
                "title": issue.get("title", ""),
                "description": issue.get("body", ""),
                "issue_type": "Bug",  # GitHub doesn't have types by default
                "status": "Closed" if issue.get("closed_at") else "Open",
                "priority": None,
                "component": None,
                "created_timestamp": created_at,
                "resolved_timestamp": closed_at,
                "assigned_to": issue.get("assignee", {}).get("login") if issue.get("assignee") else None,
                "reported_by": issue.get("user", {}).get("login"),
                "labels": [l.get("name") for l in issue.get("labels", [])],
                "resolution": None,
                "time_to_resolution_days": time_to_resolution,
                "source_platform": "GitHub",
                "source_project": repo_name,
            })
        
        return pd.DataFrame(normalized)

# Usage
if __name__ == "__main__":
    extractor = GitHubIssueExtractor()
    
    # Major projects
    repos = [
        ("kubernetes", "kubernetes"),
        ("nodejs", "node"),
        ("python", "cpython"),
    ]
    
    all_issues = []
    
    for owner, repo in repos:
        print(f"\nFetching {owner}/{repo}...")
        issues = extractor.fetch_issues(owner, repo, max_results=200)
        df = extractor.normalize_issues(issues, f"{owner}/{repo}")
        all_issues.append(df)
        print(f"  Collected {len(df)} issues")
    
    import os
    os.makedirs("data/raw", exist_ok=True)
    combined = pd.concat(all_issues, ignore_index=True)
    combined.to_csv("data/raw/github_issues.csv", index=False)
    print(f"\nTotal: {len(combined)} issues saved to data/raw/github_issues.csv")
