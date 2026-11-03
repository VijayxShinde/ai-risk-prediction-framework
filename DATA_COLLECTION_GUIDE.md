# Data Collection Implementation Guide

Quick reference for extracting data from each source.

## 1. Apache Jira REST API (Apache Projects)

```python
#!/usr/bin/env python3
"""
Extract issues from Apache Jira instances
"""

import requests
import json
import pandas as pd
from typing import List, Dict
from datetime import datetime
import time

class ApacheJiraExtractor:
    def __init__(self, jira_url: str = "https://issues.apache.org/jira"):
        self.jira_url = jira_url
        self.session = requests.Session()
        self.rate_limit_delay = 0.5  # seconds
    
    def fetch_issues(self, project_key: str, max_results: int = None) -> List[Dict]:
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
            changelog = issue.get("changelog", {})
            
            # Extract status history for time-to-resolution
            time_to_resolution = None
            if fields.get("resolved"):
                created = datetime.fromisoformat(
                    fields.get("created", "").replace("Z", "+00:00")
                )
                resolved = datetime.fromisoformat(
                    fields.get("resolutiondate", "").replace("Z", "+00:00")
                )
                time_to_resolution = (resolved - created).days
            
            normalized.append({
                "id": issue.get("key"),
                "title": fields.get("summary", ""),
                "description": fields.get("description", ""),
                "issue_type": fields.get("issuetype", {}).get("name"),
                "status": fields.get("status", {}).get("name"),
                "priority": fields.get("priority", {}).get("name"),
                "component": (fields.get("components", [{}])[0].get("name") 
                            if fields.get("components") else None),
                "created_timestamp": int(
                    datetime.fromisoformat(
                        fields.get("created", "").replace("Z", "+00:00")
                    ).timestamp()
                ),
                "resolved_timestamp": (
                    int(datetime.fromisoformat(
                        fields.get("resolutiondate", "").replace("Z", "+00:00")
                    ).timestamp())
                    if fields.get("resolutiondate") else None
                ),
                "assigned_to": fields.get("assignee", {}).get("name"),
                "reported_by": fields.get("reporter", {}).get("name"),
                "labels": [l.get("name", l) for l in fields.get("labels", [])],
                "resolution": fields.get("resolution", {}).get("name"),
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
        issues = extractor.fetch_issues(project, max_results=5000)
        df = extractor.normalize_issues(issues)
        all_issues.append(df)
        
        print(f"  Collected {len(df)} issues")
    
    # Combine and save
    combined = pd.concat(all_issues, ignore_index=True)
    combined.to_csv("apache_jira_issues.csv", index=False)
    print(f"\nTotal: {len(combined)} issues saved to apache_jira_issues.csv")
```

---

## 2. GitHub Issues API

```python
#!/usr/bin/env python3
"""
Extract issues from GitHub repositories
"""

import requests
import pandas as pd
from typing import List, Dict
from datetime import datetime
import os

class GitHubIssueExtractor:
    def __init__(self, token: str = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.session = requests.Session()
        if self.token:
            self.session.headers.update(
                {"Authorization": f"token {self.token}"}
            )
    
    def fetch_issues(self, owner: str, repo: str, 
                    state: str = "all") -> List[Dict]:
        """Fetch all issues from a repository"""
        issues = []
        page = 1
        
        while True:
            url = f"https://api.github.com/repos/{owner}/{repo}/issues"
            params = {
                "state": state,
                "page": page,
                "per_page": 100,
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
        
        return issues
    
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
        ("torvalds", "linux"),
    ]
    
    all_issues = []
    
    for owner, repo in repos:
        print(f"\nFetching {owner}/{repo}...")
        issues = extractor.fetch_issues(owner, repo)
        df = extractor.normalize_issues(issues, f"{owner}/{repo}")
        all_issues.append(df)
        print(f"  Collected {len(df)} issues")
    
    combined = pd.concat(all_issues, ignore_index=True)
    combined.to_csv("github_issues.csv", index=False)
    print(f"\nTotal: {len(combined)} issues saved")
```

---

## 3. BugSwarm Dataset Download

```python
#!/usr/bin/env python3
"""
Download and extract BugSwarm dataset
"""

import requests
import pandas as pd
import json
from typing import List, Dict

class BugSwarmExtractor:
    def __init__(self):
        self.api_base = "https://www.bugswarm.org/api"
    
    def fetch_artifacts(self, limit: int = 1000) -> List[Dict]:
        """Fetch BugSwarm artifacts metadata"""
        artifacts = []
        offset = 0
        
        while True:
            url = f"{self.api_base}/artifacts"
            params = {
                "limit": 100,
                "offset": offset
            }
            
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code != 200:
                break
            
            data = resp.json()
            batch = data.get("artifacts", [])
            
            if not batch:
                break
            
            artifacts.extend(batch)
            print(f"Fetched {len(artifacts)} artifacts...")
            
            if len(artifacts) >= limit:
                artifacts = artifacts[:limit]
                break
            
            offset += 100
        
        return artifacts
    
    def normalize_artifacts(self, artifacts: List[Dict]) -> pd.DataFrame:
        """Convert BugSwarm artifacts to normalized DataFrame"""
        normalized = []
        
        for artifact in artifacts:
            normalized.append({
                "id": artifact.get("image_tag"),
                "title": artifact.get("image_tag", ""),
                "description": None,
                "issue_type": "Bug",
                "status": "Fixed",
                "priority": None,
                "component": artifact.get("repo", "").split("/")[1] if artifact.get("repo") else None,
                "created_timestamp": int(artifact.get("created_at", 0)),
                "resolved_timestamp": int(artifact.get("fixed_at", 0)) if artifact.get("fixed_at") else None,
                "assigned_to": None,
                "reported_by": None,
                "labels": ["reproducible", "real-world"],
                "resolution": "Fixed",
                "time_to_resolution_days": artifact.get("time_to_resolution_days"),
                "source_platform": "BugSwarm",
                "source_project": artifact.get("repo", ""),
                "reproducibility_score": artifact.get("reproducibility", 0),
                "language": artifact.get("language"),
                "build_system": artifact.get("build_system"),
            })
        
        return pd.DataFrame(normalized)

# Usage
if __name__ == "__main__":
    extractor = BugSwarmExtractor()
    
    print("Fetching BugSwarm artifacts...")
    artifacts = extractor.fetch_artifacts(limit=3600)
    df = extractor.normalize_artifacts(artifacts)
    
    df.to_csv("bugswarm_artifacts.csv", index=False)
    print(f"\nTotal: {len(df)} artifacts saved to bugswarm_artifacts.csv")
    print(f"\nLanguages: {df['language'].value_counts()}")
    print(f"Build systems: {df['build_system'].value_counts()}")
```

---

## 4. Combining and Feature Engineering

```python
#!/usr/bin/env python3
"""
Combine datasets and engineer features for risk prediction
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from typing import Tuple

class RiskPredictionDataPrep:
    def __init__(self):
        self.label_encoders = {}
    
    def load_datasets(self, file_paths: list) -> pd.DataFrame:
        """Load and combine multiple datasets"""
        dfs = []
        for path in file_paths:
            print(f"Loading {path}...")
            df = pd.read_csv(path)
            dfs.append(df)
        
        combined = pd.concat(dfs, ignore_index=True)
        print(f"Combined size: {len(combined)} issues")
        return combined
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove near-duplicates"""
        # Simple exact duplicate removal
        df = df.drop_duplicates(subset=['title', 'source_platform'], keep='first')
        print(f"After dedup: {len(df)} issues")
        return df
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features for risk prediction model"""
        df = df.copy()
        
        # Text features
        df['title_length'] = df['title'].fillna('').str.len()
        df['description_length'] = df['description'].fillna('').str.len()
        df['title_word_count'] = df['title'].fillna('').str.split().str.len()
        
        # Security/Risk indicators
        security_keywords = [
            'security', 'vulnerability', 'cve', 'exploit',
            'attack', 'breach', 'threat', 'malware', 'ddos'
        ]
        df['is_security_issue'] = df['title'].fillna('').str.lower().str.contains(
            '|'.join(security_keywords)
        ).astype(int)
        
        # Performance/Stability indicators
        perf_keywords = ['performance', 'slow', 'timeout', 'hang', 'crash', 'deadlock']
        df['is_perf_issue'] = df['title'].fillna('').str.lower().str.contains(
            '|'.join(perf_keywords)
        ).astype(int)
        
        # Priority encoding
        priority_map = {
            'Critical': 4, 'Blocker': 4,
            'High': 3, 'Major': 3,
            'Medium': 2, 'Minor': 2,
            'Low': 1,
            'Trivial': 1,
            None: 0
        }
        df['priority_level'] = df['priority'].map(priority_map).fillna(0).astype(int)
        
        # Time-based features
        df['is_resolved'] = df['resolved_timestamp'].notna().astype(int)
        df['time_open_days'] = (df['resolved_timestamp'] - df['created_timestamp']) / (24 * 3600)
        df['time_open_days'] = df['time_open_days'].fillna(
            (pd.Timestamp.now().timestamp() - df['created_timestamp']) / (24 * 3600)
        )
        
        # Assignee features
        df['has_assignee'] = df['assigned_to'].notna().astype(int)
        
        # Label features
        df['num_labels'] = df['labels'].fillna('[]').str.split(',').str.len()
        
        # Issue type encoding
        df['is_bug'] = (df['issue_type'] == 'Bug').astype(int)
        df['is_feature'] = (df['issue_type'] == 'Feature').astype(int)
        
        return df
    
    def create_risk_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create risk labels for supervised learning"""
        df = df.copy()
        
        # Risk assessment based on multiple factors
        risk_score = 0
        
        risk_score += df['is_security_issue'] * 3
        risk_score += df['is_perf_issue'] * 2
        risk_score += df['priority_level']
        risk_score += (df['time_open_days'] > 180).astype(int) * 2  # Old unresolved issues
        
        # Create risk categories
        df['risk_category'] = pd.cut(
            risk_score,
            bins=[0, 2, 5, 10, np.inf],
            labels=['Low', 'Medium', 'High', 'Critical']
        )
        
        # Binary high-risk label
        df['is_high_risk'] = (df['risk_category'].isin(['High', 'Critical'])).astype(int)
        
        return df
    
    def prepare_for_training(self, df: pd.DataFrame,
                            test_size: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Create train/test split (temporal split preferred)"""
        
        # Sort by creation time
        df = df.sort_values('created_timestamp')
        
        # Temporal split
        split_point = int(len(df) * (1 - test_size))
        
        train_df = df.iloc[:split_point].copy()
        test_df = df.iloc[split_point:].copy()
        
        print(f"Train size: {len(train_df)} | Test size: {len(test_df)}")
        
        return train_df, test_df

# Usage
if __name__ == "__main__":
    prep = RiskPredictionDataPrep()
    
    # Load datasets
    files = [
        "apache_jira_issues.csv",
        "github_issues.csv",
        "bugswarm_artifacts.csv"
    ]
    
    df = prep.load_datasets(files)
    df = prep.remove_duplicates(df)
    df = prep.engineer_features(df)
    df = prep.create_risk_labels(df)
    
    # Split for training
    train_df, test_df = prep.prepare_for_training(df)
    
    # Save
    train_df.to_csv("risk_prediction_train.csv", index=False)
    test_df.to_csv("risk_prediction_test.csv", index=False)
    
    print(f"\nRisk distribution (train):")
    print(train_df['risk_category'].value_counts())
    print(f"\nRisk distribution (test):")
    print(test_df['risk_category'].value_counts())
```

---

## 4. requirements.txt

```
requests==2.31.0
pandas==2.1.0
numpy==1.24.0
scikit-learn==1.3.0
google-cloud-bigquery==3.12.0
python-jira==3.13.0
pygithub==2.1.1
python-dateutil==2.8.2
tqdm==4.66.1
```

---

## Quick Start Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Set GitHub token for higher rate limits (optional)
export GITHUB_TOKEN="ghp_your_token_here"

# Run extractors
python apache_jira_extractor.py      # ~15 min
python github_issue_extractor.py     # ~30 min
python bugswarm_extractor.py         # ~5 min

# Combine and prepare
python risk_prediction_prep.py

# Result files
# - risk_prediction_train.csv (training data)
# - risk_prediction_test.csv (test data)
```

---

**Note**: Adjust batch sizes and rate limits based on your system resources and API policies.
