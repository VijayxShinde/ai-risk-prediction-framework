# Comprehensive Guide to Publicly Available Jira & Bug Tracking Datasets

**Last Updated**: May 6, 2026  
**Purpose**: Identifies real-world datasets suitable for training AI risk prediction models  
**Focus**: Prioritized by Jira-native data, size, features, and accessibility

---

## Table of Contents
1. [Jira-Native Datasets (Priority 1)](#jira-native-datasets)
2. [GitHub Issues Datasets (Alternative to Jira)](#github-issues-datasets)
3. [Academic Research Datasets](#academic-research-datasets)
4. [Open Source Project Datasets](#open-source-project-datasets)
5. [Public Bug Tracking Systems](#public-bug-tracking-systems)
6. [Kaggle Datasets](#kaggle-datasets)
7. [Commercial/Proprietary Solutions](#commercial-solutions)
8. [Data Collection Strategies](#data-collection-strategies)

---

## JIRA-NATIVE DATASETS

### 1. **Apache Foundation Projects (Jira-Based)**

**Source**: Apache JIRA Instance + GitHub Mirror  
**URL**: https://issues.apache.org/jira/browse/  
**Projects Available**: Hadoop, Spark, Kafka, Cassandra, HBase, Hive, Storm, etc.

| Aspect | Details |
|--------|---------|
| **Type** | True Jira export data |
| **# Issues** | 50,000+ across major projects (Hadoop: 15,000+) |
| **Available Fields** | Issue Key, Type, Status, Priority, Summary, Description, Components, Assignee, Reporter, Created, Updated, Resolved, Labels, Custom Fields |
| **Quality** | High - Well-maintained, categorized issues with detailed resolution history |
| **Access Method** | Public REST API (with rate limits), Jira export XML, GitHub mirror |
| **License** | Apache 2.0 - Free for commercial use |
| **Prep Time** | 3-6 hours (API pagination required) |

**Data Extraction:**
```bash
# Via Jira REST API (public access)
curl "https://issues.apache.org/jira/rest/api/2/search?jql=project=HADOOP&maxResults=1000"

# Via GitHub mirror (faster)
git clone https://github.com/apache/hadoop.git
# Issues available in GitHub REST API
```

**Risk Prediction Value:**
- Rich issue classification (Bug, Task, Feature, Subtask)
- Component-level tracking
- Priority levels
- Resolution types (Fixed, Won't Fix, Duplicate)
- Time-to-resolution metrics
- Committer/contributor patterns

**Notable Projects**:
- **Apache Hadoop**: ~15,000 issues spanning 15+ years
- **Apache Spark**: ~10,000 issues
- **Apache Kafka**: ~8,000 issues
- **Apache Cassandra**: ~7,000 issues

---

### 2. **Atlassian Cloud Public Datasets**

**Source**: Atlassian Research Program  
**URL**: https://www.atlassian.com/research

| Aspect | Details |
|--------|---------|
| **Type** | Anonymized Jira Cloud data |
| **# Issues** | Varies by dataset (1,000-50,000+) |
| **Available Fields** | Full Jira schema when available |
| **Quality** | High (when available) - directly from Atlassian |
| **Access Method** | Research partnership, request required |
| **License** | Restricted - Academic use only |
| **Prep Time** | 2-4 weeks (requires approval process) |

**Characteristics:**
- Limited public availability (mostly academic partnerships)
- Anonymized company data
- Direct from Jira Cloud platform
- Request requires academic institution affiliation

---

## GITHUB ISSUES DATASETS

### 3. **GitHub Issues API + GraphQL**

**Source**: GitHub REST API v3 & GraphQL API v4  
**URL**: https://api.github.com, https://github.com/graphql

| Aspect | Details |
|--------|---------|
| **Type** | GitHub Issues (Jira alternative) |
| **# Issues** | Unlimited access to public repos (millions available) |
| **Available Fields** | Issue ID, Title, Body, State, Assignee, Labels, Milestones, Created, Updated, Closed, Reactions, Comments |
| **Quality** | High - Direct from authoritative source |
| **Access Method** | Free API (60 req/hr unauthenticated, 5000 req/hr authenticated) |
| **License** | Follows each repository's license (mostly MIT/Apache 2.0) |
| **Prep Time** | 8-12 hours for large projects (rate limiting, pagination) |

**Major Projects with Rich Issue Histories:**
- **Kubernetes** (~122k stars): 1,800+ open issues, comprehensive history
- **Node.js**: 15,000+ closed issues
- **React**: 10,000+ closed issues
- **Vue.js**: 5,000+ closed issues
- **TensorFlow**: 20,000+ closed issues

**Python Script to Extract**:
```python
import requests
import pandas as pd
from datetime import datetime

def fetch_github_issues(owner, repo, token=None):
    headers = {"Authorization": f"token {token}"} if token else {}
    issues = []
    page = 1
    
    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        params = {
            "state": "all",
            "page": page,
            "per_page": 100,
            "sort": "created"
        }
        
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            break
            
        data = resp.json()
        if not data:
            break
            
        for issue in data:
            issues.append({
                "id": issue["id"],
                "number": issue["number"],
                "title": issue["title"],
                "body": issue["body"],
                "state": issue["state"],
                "labels": [l["name"] for l in issue["labels"]],
                "created_at": issue["created_at"],
                "updated_at": issue["updated_at"],
                "closed_at": issue["closed_at"],
                "assignee": issue["assignee"]["login"] if issue["assignee"] else None,
                "comments": issue["comments"]
            })
        page += 1
    
    return pd.DataFrame(issues)

# Example usage
df = fetch_github_issues("kubernetes", "kubernetes", token="ghp_YOUR_TOKEN")
```

---

### 4. **GHArchive Project History Dataset**

**Source**: GHArchive.org (Google BigQuery)  
**URL**: https://www.gharchive.org/

| Aspect | Details |
|--------|---------|
| **Type** | GitHub event archive (issues, PRs, commits) |
| **# Records** | 4+ billion events (2011-present) |
| **Available Fields** | Event type, actor, repo, timestamp, payload |
| **Quality** | Comprehensive - Complete GitHub activity history |
| **Access Method** | Google BigQuery (free tier: 1TB/month), CSV downloads |
| **License** | Free for research and analysis |
| **Prep Time** | 4-8 hours (SQL query + export) |

**Sample BigQuery Query**:
```sql
SELECT
  repo.name,
  actor.login,
  created_at,
  payload.issue.number,
  payload.issue.title,
  payload.issue.state,
  payload.issue.labels
FROM `githubarchive.day.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20200101' AND '20231231'
  AND type = 'IssuesEvent'
  AND repo.name IN ('kubernetes/kubernetes', 'torvalds/linux', 'nodejs/node')
LIMIT 1000000
```

---

## ACADEMIC RESEARCH DATASETS

### 5. **BugSwarm Dataset**

**Source**: UC Davis - ICSE 2019  
**Repository**: https://github.com/BugSwarm/bugswarm  
**Website**: https://www.bugswarm.org/dataset

| Aspect | Details |
|--------|---------|
| **Type** | Real failing & passing build pairs from CI/CD |
| **# Artifacts** | 3,600+ reproducible bug-fix pairs |
| **Languages** | Java (70%), Python (30%) |
| **Available Fields** | Source code diffs, build logs, test results, CI configuration, reproducibility info |
| **Quality** | **EXCELLENT** - Reproducible, validated failures with fixes |
| **Access Method** | Docker images (hub.docker.com/r/bugswarm/cached-images), REST API |
| **License** | Academic (check per-project licenses) |
| **Prep Time** | 2-3 hours (download Docker images) |

**Citation**: Tomassi et al., "BugSwarm: Mining and Continuously Growing a Dataset of Reproducible Failures and Fixes", ICSE 2019

**Key Features for Risk Prediction**:
- Real, reproducible failures
- Classified as: Build, Code, or Test failures
- Test coverage information
- CI system metadata
- Build system details (Maven, Gradle, etc.)

**Data Extraction**:
```bash
# List available artifacts
curl https://www.bugswarm.org/api/artifacts?limit=100

# Pull Docker images
docker pull bugswarm/cached-images:alibaba-dubbo-e1e4c7e

# Access metadata via REST API
curl https://www.bugswarm.org/api/artifacts/alibaba-dubbo-e1e4c7e
```

---

### 6. **MSR (Mining Software Repositories) Datasets**

**Source**: Various conferences (ICSE, FSE, MSR, ASE)  
**Aggregator**: https://zenodo.org/ (search "mining software repositories")

| Aspect | Details |
|--------|---------|
| **Type** | Heterogeneous - Various bug/issue tracking datasets |
| **# Issues** | 10,000 - 100,000+ depending on dataset |
| **Available Fields** | Varies (typically include issue ID, status, resolution, time-to-fix) |
| **Quality** | High - Peer-reviewed research datasets |
| **Access Method** | Direct download from Zenodo or university archives |
| **License** | CC-BY-4.0 or similar (free for all uses) |
| **Prep Time** | 2-4 hours |

**Notable MSR Datasets**:
- **Defects4J**: 395 bugs from 6 Java projects (JFreeChart, Closure, Commons Lang, etc.)
- **BugLocalization Datasets**: From multiple bug localization research papers
- **Issue Duplication Datasets**: For issue linking/deduplication models

---

### 7. **Software Engineering Benchmark Datasets**

**Source**: University of Toronto, University of Washington, CMU  
**URL**: https://zenodo.org/ (search "bug dataset" or "issue classification")

**Notable Collections**:
- **Bug Localization Benchmark**: ~500 bugs with gold-standard bug locations
- **Issue Classification Dataset**: 2,000+ issues labeled by type
- **Time-to-Fix Prediction Dataset**: 5,000+ issues with resolution times

---

## OPEN SOURCE PROJECT DATASETS

### 8. **Linux Kernel Bugzilla**

**Source**: https://bugzilla.kernel.org/  
**URL**: https://bugzilla.kernel.org/

| Aspect | Details |
|--------|---------|
| **Type** | Bugzilla export |
| **# Issues** | 150,000+ bugs |
| **Available Fields** | Bug ID, Summary, Status, Priority, Severity, Component, Assigned to, Created, Modified, Resolution |
| **Quality** | High - Mission-critical software |
| **Access Method** | Bugzilla REST API, XML export |
| **License** | Various (mostly GPL) |
| **Prep Time** | 6-12 hours |

**Data Extraction**:
```bash
# Bugzilla REST API
curl "https://bugzilla.kernel.org/rest/bug?product=Linux%20Kernel&limit=10000"

# XML export (if available)
wget "https://bugzilla.kernel.org/show_bug.cgi?ctype=xml&product=Linux%20Kernel"
```

---

### 9. **Mozilla Firefox Bugzilla**

**Source**: https://bugzilla.mozilla.org/  
**URL**: https://bugzilla.mozilla.org/

| Aspect | Details |
|--------|---------|
| **Type** | Bugzilla export |
| **# Issues** | 500,000+ bugs across all Mozilla projects |
| **Available Fields** | Bug ID, Summary, Status, Priority, Severity, Component, Keywords, Created, Modified, Resolution |
| **Quality** | Excellent - Professional bug tracking |
| **Access Method** | Bugzilla REST API, BugBug dataset (Mozilla's ML project) |
| **License** | Various per-project |
| **Prep Time** | 8-16 hours (large dataset) |

**Mozilla BugBug Project**: https://github.com/mozilla/bugbug
- Pre-processed Mozilla Bugzilla data
- Available as CSV/Parquet
- Includes ML predictions for classification

```bash
# BugBug data repository
git clone https://github.com/mozilla/bugbug.git
cd bugbug
# Download preprocessed data
python -m bugbug.data download bugs
```

---

### 10. **Apache ASF Bugzilla Instances**

**Source**: Various Apache projects running Bugzilla  
**Projects**: Apache HTTP Server, Apache OpenOffice, Apache OFBiz, etc.

| Aspect | Details |
|--------|---------|
| **Type** | Bugzilla export |
| **# Issues** | 5,000 - 50,000 per project |
| **Available Fields** | Standard Bugzilla fields |
| **Quality** | Medium-High |
| **Access Method** | Public Bugzilla API |
| **License** | Apache 2.0 |
| **Prep Time** | 4-8 hours per project |

---

## PUBLIC BUG TRACKING SYSTEMS

### 11. **Chromium/Google Chrome Issue Tracker**

**Source**: https://bugs.chromium.org/  
**URL**: https://bugs.chromium.org/p/chromium/issues/list

| Aspect | Details |
|--------|---------|
| **Type** | Monorail issue tracker |
| **# Issues** | 1,000,000+ issues |
| **Available Fields** | Issue ID, Title, Description, Labels, Status, Priority, Assigned to, Components, Created, Modified, Resolved |
| **Quality** | Excellent |
| **Access Method** | Public API, HTML scraping |
| **License** | Various per-project |
| **Prep Time** | 12-24 hours (large dataset) |

**Note**: Rate limiting enforced. Recommend respectful scraping or API usage.

---

### 12. **Eclipse Project Bugs**

**Source**: https://bugs.eclipse.org/  
**URL**: https://bugs.eclipse.org/bugs/

| Aspect | Details |
|--------|---------|
| **Type** | Bugzilla-based |
| **# Issues** | 400,000+ bugs |
| **Available Fields** | Standard Bugzilla schema |
| **Quality** | High |
| **Access Method** | Bugzilla REST API |
| **License** | EPL-2.0 (free) |
| **Prep Time** | 6-10 hours |

---

### 13. **GnuBug Tracker (Free Software Projects)**

**Source**: https://debbugs.gnu.org/  
**Projects**: GNU Emacs, GNU Coreutils, GNU Make, GCC, etc.

| Aspect | Details |
|--------|---------|
| **Type** | Debbugs format |
| **# Issues** | 10,000 - 100,000+ per major project |
| **Available Fields** | Bug ID, Title, Status, Severity, Owner, Created, Modified |
| **Quality** | Medium-High |
| **Access Method** | Mail interface, SOAP API, direct file system access |
| **License** | Various GNU licenses |
| **Prep Time** | 4-6 hours |

---

## KAGGLE DATASETS

### 14. **Kaggle Bug & Issue Datasets**

**URL**: https://www.kaggle.com/datasets?search=bug+issue

**Search Results** (as of 2026):
| Dataset Name | Size | Fields | License |
|--------------|------|--------|---------|
| "GitHub Issues Dataset" | Varies | Issues, PRs, comments | CC0 |
| "Software Bug Datasets" | 5,000-10,000 issues | Issue metadata, status, type | CC-BY-4.0 |
| "Stack Overflow Tags & Questions" | 20M+ Q&A | Title, body, tags, score, creation date | CC-BY-SA-4.0 |

**Kaggle API Access**:
```bash
# Install Kaggle CLI
pip install kaggle

# Configure credentials
# Place kaggle.json in ~/.kaggle/

# Download dataset
kaggle datasets download -d <dataset-slug>
```

---

## COMMERCIAL SOLUTIONS

### 15. **Jira Cloud Data Export (Limited)**

**Source**: Atlassian Cloud  
**URL**: https://www.atlassian.com/cloud/pricing

| Aspect | Details |
|--------|---------|
| **Type** | Jira Cloud export |
| **# Issues** | Trial/Free account limitations |
| **Available Fields** | Full Jira schema |
| **Quality** | Excellent (if available) |
| **Access Method** | Cloud instance export, REST API |
| **License** | Proprietary (with terms) |
| **Prep Time** | 1-2 hours |

**Note**: Creating trial Jira Cloud instances with sample data is possible for testing.

---

### 16. **Atlassian Marketplace Plugins**

**Source**: https://marketplace.atlassian.com/

**Relevant Tools for Data Export**:
- **Jira Data Center Export Tools**: Bulk export of issues
- **Analytics for Jira**: Pre-aggregated issue data
- **Tempo Timesheets**: Issue resolution time data

---

## DATA COLLECTION STRATEGIES

### Strategy 1: Multi-Source Aggregation (Recommended for AI Training)

**Combine**:
1. BugSwarm (3,600+ artifacts with builds/tests)
2. Apache Jira projects (50,000+ issues)
3. GitHub Issues from major projects (100,000+ issues)
4. Mozilla Firefox Bugzilla (500,000+ issues)

**Estimated Total**: 650,000+ issues across diverse contexts

**Preparation Steps**:
```python
import pandas as pd
from typing import List, Dict

# Step 1: Normalize all datasets to common schema
COMMON_SCHEMA = {
    "id": str,
    "title": str,
    "description": str,
    "issue_type": str,  # Bug, Feature, Task, etc.
    "status": str,  # Open, Closed, Resolved, etc.
    "priority": str,  # High, Medium, Low, None
    "component": str,  # Optional
    "created_timestamp": int,  # Unix timestamp
    "resolved_timestamp": int,  # Unix timestamp (null if unresolved)
    "assigned_to": str,  # Assignee identifier
    "reported_by": str,  # Reporter identifier
    "labels": List[str],
    "resolution": str,  # Fixed, Won't Fix, Duplicate, etc.
    "severity": str,  # If available
    "time_to_resolution_days": float,  # Computed
    "source_project": str,  # For identification
    "source_platform": str,  # Jira, GitHub, Bugzilla, etc.
}

# Step 2: Feature engineering for risk prediction
def engineer_features(dataset: pd.DataFrame) -> pd.DataFrame:
    df = dataset.copy()
    
    # Calculate features relevant to risk prediction
    df['days_open'] = (df['resolved_timestamp'] - df['created_timestamp']) / (24 * 3600)
    df['is_high_priority'] = (df['priority'] == 'High').astype(int)
    df['is_security_related'] = df['labels'].str.contains('security|vulnerability|cve', case=False, na=False).astype(int)
    df['description_length'] = df['description'].fillna('').str.len()
    df['has_assignee'] = df['assigned_to'].notna().astype(int)
    df['title_length'] = df['title'].str.len()
    df['component_complexity'] = calculate_component_complexity(df['component'])
    
    # Label for training (risk levels)
    df['risk_level'] = categorize_risk(df)
    
    return df

# Step 3: Validation and deduplication
def deduplicate_issues(datasets: List[pd.DataFrame]) -> pd.DataFrame:
    combined = pd.concat(datasets, ignore_index=True)
    
    # Remove near-duplicates using title/description similarity
    # (implement with fuzzy matching or embeddings)
    
    return combined.drop_duplicates(subset=['title', 'source_platform'])
```

---

### Strategy 2: Real-Time Streaming Collection

**For continuous model training**:
1. Set up GitHub Actions workflow to export issues
2. Use Apache Airflow + Python scripts for scheduled Jira/Bugzilla scraping
3. Store in cloud data warehouse (BigQuery, Snowflake)
4. Retrain models monthly/quarterly

---

### Strategy 3: Focused Domain Collection

**For specific risk prediction use case**:
- Focus on Security-related issues (search for "security", "vulnerability", "CVE")
- Focus on Performance issues (search for "performance", "timeout", "slowness")
- Focus on Stability issues (search for "crash", "hang", "deadlock")

---

## RECOMMENDED DATASET SELECTION PRIORITY

### Tier 1 (Start Here - Quick Setup)
1. **BugSwarm Dataset** - Real, reproducible failures (3,600 artifacts)
2. **Apache Jira Projects** - Large, well-maintained (50,000+ issues)
3. **GitHub Issues API** - Major projects (100,000+ issues across multiple projects)

**Estimated Preparation**: 8-12 hours  
**Total Issues**: 150,000+  
**Training Data Quality**: EXCELLENT

### Tier 2 (Extended Coverage)
4. **Mozilla Bugzilla** - Domain expertise (500,000 issues)
5. **GHArchive** - Complete GitHub history (billions of events)
6. **Linux Kernel Bugzilla** - Mission-critical software (150,000 issues)

**Additional Preparation**: 20-30 hours  
**Additional Issues**: 650,000+  
**Training Data Quality**: VERY GOOD

### Tier 3 (Specialized Use Cases)
7. Chromium Issue Tracker
8. Eclipse Project Bugs
9. Kaggle datasets
10. Commercial Jira instances (if available)

---

## DATA PREPARATION CHECKLIST

- [ ] Download/export raw data from each source
- [ ] Normalize field names and values across sources
- [ ] Parse timestamps and calculate time-to-resolution
- [ ] Extract and tag risk indicators (security, performance, stability)
- [ ] Remove duplicates and near-duplicates
- [ ] Handle missing/null values
- [ ] Create train/validation/test splits (temporal split recommended)
- [ ] Generate feature vectors for risk prediction
- [ ] Document data lineage and version control
- [ ] Create data validation tests

---

## COMPLIANCE & LICENSING NOTES

### Legal Considerations
- **Apache 2.0** projects: Full commercial use allowed ✓
- **GPL projects**: Carefully review derivative work requirements
- **Academic datasets**: Typically CC-BY-4.0 - free for all uses ✓
- **Proprietary (Jira Cloud)**: Follows Atlassian ToS - check your instance

### Data Privacy
- Most public repositories are anonymized
- Respect rate limits (GitHub: 5,000 req/hr, etc.)
- Cache downloaded data locally to minimize API calls
- Do not republish sensitive/internal issue data

---

## TOOLS & LIBRARIES

### Data Collection
- `pygithub` - GitHub API wrapper (Python)
- `python-jira` - Jira API wrapper (Python)
- `bugbug` - Mozilla's bug classification library (Python)
- `google-cloud-bigquery` - Query GHArchive data (Python)

### Data Processing
- `pandas` - Data manipulation
- `dask` - Distributed processing (large datasets)
- `polars` - High-performance DataFrame library
- `Apache Spark` - Large-scale distributed computing

### Machine Learning
- `scikit-learn` - Classical ML algorithms
- `XGBoost`, `LightGBM` - Gradient boosting
- `TensorFlow`, `PyTorch` - Deep learning
- `wandb` - Experiment tracking and reproducibility

---

## ESTIMATED RESOURCE REQUIREMENTS

### Data Storage
- Tier 1 Dataset: 5-10 GB
- Tier 1 + Tier 2: 50-100 GB
- Full (all tiers): 200-500 GB

### Computation Time
- Data collection: 8-48 hours (parallelizable)
- Data normalization: 2-6 hours
- Feature engineering: 4-10 hours
- Model training: 6-48 hours (depends on model size)

**Total Initial Setup**: 20-100 hours (highly parallelizable)

---

## REFERENCES & FURTHER READING

### Key Research Papers
1. Tomassi et al. (2019) - "BugSwarm: Mining and Continuously Growing a Dataset of Reproducible Failures and Fixes" - ICSE
2. Herbold et al. (2017) - "A Study on the Extensibility of Defect Prediction Models" - TSE
3. Just et al. (2014) - "Defects4J: A Database of Existing Faults for Enabling Controlled Testing Studies for Java Programs" - ISSTA

### Resources
- BugSwarm: https://www.bugswarm.org/
- Mozilla BugBug: https://github.com/mozilla/bugbug
- GitHub Octoverse: https://octoverse.github.com/
- GHArchive: https://www.gharchive.org/
- Zenodo Research Data: https://zenodo.org/

---

**Document Version**: 1.0  
**Last Updated**: May 6, 2026  
**Maintainer**: AI Risk Prediction Framework Team
