#!/usr/bin/env python3
"""
Extract issues from Apache Jira instances
"""

import requests
import json
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
import time

def parse_jira_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    # Fix timezone representation (e.g. +0000 -> +00:00)
    if len(date_str) > 5 and date_str[-5] in ('+', '-'):
        if ':' not in date_str[-4:]:
            date_str = date_str[:-2] + ':' + date_str[-2:]
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        try:
            from dateutil.parser import parse as parse_date  # type: ignore
            return parse_date(date_str)
        except Exception:
            return None

class ApacheJiraExtractor:
    def __init__(self, jira_url: str = "https://issues.apache.org/jira"):
        self.jira_url = jira_url
        self.session = requests.Session()
        self.rate_limit_delay = 0.5  # seconds
    
    def fetch_issues(self, project_key: str, max_results: Optional[int] = None) -> List[Dict]:
        """Fetch all issues from a project"""
        issues = []
        start_at = 0
        batch_size = 50
        
        jql = f"project = {project_key} ORDER BY created DESC"
        
        while True:
            url = f"{self.jira_url}/rest/api/2/search"
            params = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": batch_size,
                "expand": "changelog"
            }
            
            try:
                resp = self.session.get(url, params=params, timeout=30)
                resp.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Error fetching batch at {start_at}: {e}")
                break
            
            data = resp.json()
            batch = data.get("issues", [])
            
            if not batch:
                break
            
            issues.extend(batch)
            print(f"Fetched {len(issues)} issues so far...")
            
            if max_results and len(issues) >= max_results:
                issues = issues[:max_results]
                break
            
            start_at += batch_size
            time.sleep(self.rate_limit_delay)
        
        return issues
    
    def normalize_issues(self, issues: List[Dict]) -> pd.DataFrame:
        """Convert Jira issues to normalized DataFrame"""
        normalized = []
        
        for issue in issues:
            fields = issue.get("fields", {})
            
            # Extract status history for time-to-resolution
            time_to_resolution = None
            resolution_date = fields.get("resolutiondate")
            created_date = fields.get("created")
            
            if resolution_date and created_date:
                created = parse_jira_date(created_date)
                resolved = parse_jira_date(resolution_date)
                if created and resolved:
                    time_to_resolution = (resolved - created).days
            
            created_dt = parse_jira_date(created_date)
            created_ts = int(created_dt.timestamp()) if created_dt else 0
            
            resolved_dt = parse_jira_date(resolution_date)
            resolved_ts = int(resolved_dt.timestamp()) if resolved_dt else None
            
            # Safely handle labels list
            labels_raw = fields.get("labels", [])
            labels_clean = []
            if isinstance(labels_raw, list):
                for item in labels_raw:
                    if isinstance(item, dict):
                        labels_clean.append(item.get("name", str(item)))
                    else:
                        labels_clean.append(str(item))
            
            normalized.append({
                "id": issue.get("key"),
                "title": fields.get("summary", ""),
                "description": fields.get("description", ""),
                "issue_type": fields.get("issuetype", {}).get("name") if fields.get("issuetype") else None,
                "status": fields.get("status", {}).get("name") if fields.get("status") else None,
                "priority": fields.get("priority", {}).get("name") if fields.get("priority") else None,
                "component": (fields.get("components", [{}])[0].get("name") 
                            if fields.get("components") else None),
                "created_timestamp": created_ts,
                "resolved_timestamp": resolved_ts,
                "assigned_to": fields.get("assignee", {}).get("name") if fields.get("assignee") else None,
                "reported_by": fields.get("reporter", {}).get("name") if fields.get("reporter") else None,
                "labels": labels_clean,
                "resolution": fields.get("resolution", {}).get("name") if fields.get("resolution") else None,
                "time_to_resolution_days": time_to_resolution,
                "source_platform": "Apache Jira",
            })
        
        return pd.DataFrame(normalized)

# Usage
if __name__ == "__main__":
    extractor = ApacheJiraExtractor()
    
    # Fetch from multiple projects
    projects = ["HADOOP", "SPARK", "KAFKA"]
    all_issues = []
    
    for project in projects:
        print(f"\nFetching {project}...")
        issues = extractor.fetch_issues(project, max_results=200)
        df = extractor.normalize_issues(issues)
        all_issues.append(df)
        print(f"  Collected {len(df)} issues")
    
    import os
    os.makedirs("data/raw", exist_ok=True)
    combined = pd.concat(all_issues, ignore_index=True)
    combined.to_csv("data/raw/apache_jira_issues.csv", index=False)
    print(f"\nTotal: {len(combined)} issues saved to data/raw/apache_jira_issues.csv")
