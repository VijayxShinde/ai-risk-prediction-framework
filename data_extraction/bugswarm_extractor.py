#!/usr/bin/env python3
"""
Download and extract BugSwarm dataset
"""

import requests
import pandas as pd
import json
from typing import List, Dict
from datetime import datetime

class BugSwarmExtractor:
    def __init__(self):
        self.api_base = "http://api.bugswarm.org/v1"
    
    def fetch_artifacts(self, limit: int = 200) -> List[Dict]:
        """Fetch BugSwarm artifacts metadata"""
        artifacts = []
        offset = 0
        
        while len(artifacts) < limit:
            url = f"{self.api_base}/artifacts"
            params = {
                "limit": min(100, limit - len(artifacts)),
                "offset": offset
            }
            
            try:
                resp = requests.get(url, params=params, timeout=30)
                resp.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Error fetching BugSwarm artifacts: {e}")
                break
                
            data = resp.json()
            # Bugswarm API returns a list directly or a dict with an '_items' or 'artifacts' key
            if isinstance(data, list):
                batch = data
            elif isinstance(data, dict):
                batch = data.get("_items", data.get("artifacts", []))
            else:
                batch = []
                
            if not batch:
                break
            
            artifacts.extend(batch)
            print(f"Fetched {len(artifacts)} artifacts...")
            
            offset += len(batch)
        
        return artifacts[:limit]
    
    def normalize_artifacts(self, artifacts: List[Dict]) -> pd.DataFrame:
        """Convert BugSwarm artifacts to normalized DataFrame"""
        normalized = []
        
        for artifact in artifacts:
            image_tag = artifact.get("image_tag", "")
            repo = artifact.get("repo", "")
            
            failed_job = artifact.get("failed_job", {})
            passed_job = artifact.get("passed_job", {})
            created_at_str = failed_job.get("committed_at")
            fixed_at_str = passed_job.get("committed_at")
            
            created_ts = 0
            resolved_ts = None
            time_to_resolution = None
            
            def parse_date(date_str: str) -> datetime | None:
                if not date_str:
                    return None
                if len(date_str) > 5 and date_str[-5] in ('+', '-'):
                    if ':' not in date_str[-4:]:
                        date_str = date_str[:-2] + ':' + date_str[-2:]
                try:
                    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except Exception:
                    try:
                        from dateutil.parser import parse as parse_date_util  # type: ignore
                        return parse_date_util(date_str)
                    except Exception:
                        return None

            if created_at_str:
                dt_created = parse_date(created_at_str)
                if dt_created:
                    created_ts = int(dt_created.timestamp())
                    if fixed_at_str:
                        dt_resolved = parse_date(fixed_at_str)
                        if dt_resolved:
                            resolved_ts = int(dt_resolved.timestamp())
                            diff = (dt_resolved - dt_created).total_seconds() / 86400.0
                            time_to_resolution = max(0.1, round(diff, 2))
            
            normalized.append({
                "id": image_tag,
                "title": image_tag,
                "description": f"Build system: {artifact.get('build_system', 'Unknown')}. Language: {artifact.get('lang', 'Unknown')}.",
                "issue_type": "Bug",
                "status": "Fixed",
                "priority": "High",
                "component": repo.split("/")[1] if repo and "/" in repo else None,
                "created_timestamp": created_ts,
                "resolved_timestamp": resolved_ts,
                "assigned_to": None,
                "reported_by": None,
                "labels": ["reproducible", "real-world"],
                "resolution": "Fixed",
                "time_to_resolution_days": time_to_resolution,
                "source_platform": "BugSwarm",
                "source_project": repo,
                "reproducibility_score": artifact.get("reproduce_successes", 0),
                "language": artifact.get("lang"),
                "build_system": artifact.get("build_system"),
            })
        
        return pd.DataFrame(normalized)

# Usage
if __name__ == "__main__":
    extractor = BugSwarmExtractor()
    
    print("Fetching BugSwarm artifacts...")
    artifacts = extractor.fetch_artifacts(limit=200)
    df = extractor.normalize_artifacts(artifacts)
    
    import os
    os.makedirs("data/raw", exist_ok=True)
    df.to_csv("data/raw/bugswarm_artifacts.csv", index=False)
    print(f"\nTotal: {len(df)} artifacts saved to data/raw/bugswarm_artifacts.csv")
