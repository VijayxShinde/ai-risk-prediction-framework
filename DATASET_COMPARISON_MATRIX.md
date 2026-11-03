# Dataset Comparison & Quick Reference Matrix

## Executive Summary Table

| Rank | Source | Type | # Issues | Setup Time | Data Quality | Ease of Access | Cost | Best For |
|------|--------|------|----------|------------|--------------|-----------------|------|----------|
| 1 | BugSwarm | Real bugs with fixes | 3,600 | 2 hrs | EXCELLENT | Easy | Free | Reproducible failures, build data |
| 2 | Apache Jira | Jira-native | 50,000+ | 4 hrs | HIGH | Easy | Free | Production issue tracking, long history |
| 3 | GitHub Issues (Major Projects) | GitHub Issues | 100,000+ | 6 hrs | HIGH | Easy | Free | Large community projects, modern practices |
| 4 | Mozilla Bugzilla | Bugzilla | 500,000+ | 8 hrs | HIGH | Medium | Free | Security/stability expertise, volume |
| 5 | Linux Kernel | Bugzilla | 150,000+ | 6 hrs | HIGH | Medium | Free | Mission-critical systems |
| 6 | GHArchive | Complete GitHub history | 4B+ events | 4 hrs | VERY HIGH | Easy | Free | Temporal analysis, complete history |
| 7 | Eclipse Bugs | Bugzilla | 400,000+ | 6 hrs | HIGH | Medium | Free | Enterprise Java, IDE development |
| 8 | Chromium | Monorail | 1,000,000+ | 10 hrs | HIGH | Hard | Free | Large-scale tracking, browser dev |

---

## Detailed Comparison Matrix

### Data Completeness

| Field | Apache Jira | GitHub Issues | BugSwarm | Mozilla Bugzilla | Linux Bugzilla |
|-------|------------|---------------|----------|------------------|-----------------|
| Issue ID | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| Title/Summary | ✓✓✓ | ✓✓✓ | ✓✓ | ✓✓✓ | ✓✓✓ |
| Description | ✓✓✓ | ✓✓✓ | ✓✓ | ✓✓✓ | ✓✓✓ |
| Status | ✓✓✓ | ✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| Priority | ✓✓✓ | ✗ | ✗ | ✓✓✓ | ✓✓✓ |
| Severity | ✓✓✓ | ✗ | ✗ | ✓✓✓ | ✓✓✓ |
| Component/Category | ✓✓✓ | ✗ | ✓✓ | ✓✓✓ | ✓✓✓ |
| Assignee | ✓✓✓ | ✓✓ | ✗ | ✓✓✓ | ✓✓✓ |
| Reporter | ✓✓✓ | ✓✓ | ✗ | ✓✓✓ | ✓✓✓ |
| Created Date | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| Updated Date | ✓✓✓ | ✓✓✓ | ✓✓ | ✓✓✓ | ✓✓✓ |
| Resolved Date | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| Resolution Type | ✓✓✓ | ✗ | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| Labels/Tags | ✓✓✓ | ✓✓✓ | ✓✓ | ✓✓✓ | ✓✓✓ |
| Comments | ✓✓✓ | ✓✓✓ | ✗ | ✓✓ | ✓✓ |
| Linked Issues | ✓✓✓ | ✓ | ✗ | ✓✓ | ✓✓ |
| Source Code Diff | ✗ | ✗ | ✓✓✓ | ✗ | ✗ |
| Build Logs | ✗ | ✗ | ✓✓✓ | ✗ | ✗ |
| Test Results | ✗ | ✗ | ✓✓✓ | ✗ | ✗ |

**Legend**: ✓✓✓ = Complete | ✓✓ = Partial | ✓ = Limited | ✗ = Not available

---

### API & Access Methods

| Source | API Type | Rate Limit | Authentication | Bulk Export | Notes |
|--------|----------|-----------|-----------------|------------|-------|
| Apache Jira | REST v2 | Unlimited* | None | Yes (XML) | *With fair use policy |
| GitHub Issues | REST v3 + GraphQL | 5,000/hr (auth) | OAuth token | Yes (GraphQL) | Rate limit per user/token |
| BugSwarm | REST + Docker | Unlimited | None | Yes (Docker) | Pre-packaged, easiest setup |
| Mozilla Bugzilla | REST | Unlimited | Optional | Yes | Well-documented API |
| Linux Kernel | Bugzilla | Unlimited | None | Yes | Direct XML export available |
| GHArchive | BigQuery | Depends on GQ | None | Yes (CSV) | Free tier: 1TB/month |
| Eclipse | Bugzilla | Unlimited | None | Yes | Mirror of Bugzilla |
| Chromium | REST | Rate limited | None | No direct export | Requires scraping |

---

### Feature Richness for Risk Prediction

| Dimension | Score | Details |
|-----------|-------|---------|
| **BugSwarm** | ⭐⭐⭐⭐⭐ | Source code diffs, build logs, test results, reproducibility info |
| **Apache Jira** | ⭐⭐⭐⭐ | Custom fields, component tracking, priority/severity, detailed history |
| **Mozilla Bugzilla** | ⭐⭐⭐⭐ | Security focus, severity, keywords, comprehensive tracking |
| **GitHub Issues** | ⭐⭐⭐ | Labels, pull request linkage, reactions, but lacks priority/severity |
| **Linux Kernel** | ⭐⭐⭐⭐ | Severity, component tracking, but fewer metadata fields |
| **GHArchive** | ⭐⭐⭐ | Temporal completeness, but limited per-issue granularity |
| **Eclipse Bugs** | ⭐⭐⭐ | Similar to other Bugzilla instances, good component tracking |

---

## Data Collection Time Estimates

### Sequential Collection (Single Machine)
```
Apache Jira (50k issues)        : 4 hrs
GitHub (100k issues)            : 6 hrs  
BugSwarm (3.6k artifacts)       : 2 hrs
Mozilla Bugzilla (500k issues)  : 8 hrs
Linux Kernel (150k issues)      : 6 hrs
─────────────────────────────────────────
TOTAL (sequential)              : 26 hrs
```

### Parallel Collection (Recommended)
```
Apache Jira (4 hrs)     ┐
GitHub (6 hrs)          ├─ Run in parallel
BugSwarm (2 hrs)        ├─ Takes ~6 hrs total
Mozilla (8 hrs)         │
Linux Kernel (6 hrs)    ┘

Data combination/cleaning: 4 hrs
Feature engineering       : 4 hrs
─────────────────────────────────────────
TOTAL (parallel)         : 14 hrs
```

---

## Storage & Processing Requirements

### Raw Data Storage
| Source | Raw Size | Compressed | Type |
|--------|----------|-----------|------|
| Apache Jira (50k) | 2-3 GB | 200-400 MB | JSON |
| GitHub (100k) | 3-5 GB | 300-600 MB | JSON |
| BugSwarm (3.6k) | 50-100 GB | N/A (Docker) | Docker images |
| Mozilla (500k) | 15-20 GB | 1.5-2 GB | XML/JSON |
| Linux Kernel (150k) | 5-8 GB | 500-800 MB | XML |
| GHArchive (1M events) | 50-100 GB | 5-10 GB | JSON (parquet) |
| **TIER 1 TOTAL** | ~10-15 GB | 1-1.5 GB | - |
| **TIER 1+2 TOTAL** | ~75-130 GB | 8-15 GB | - |

### Processing Power Needed
- **Data download**: Single CPU core (I/O limited)
- **JSON parsing**: 2-4 CPU cores (CPU limited)
- **Deduplication**: 4+ cores (memory intensive)
- **Feature engineering**: 8+ cores recommended
- **RAM required**: 8-16 GB minimum, 32+ GB recommended for full dataset

---

## Risk Prediction Model Suitability

### Which Dataset for What?

#### 🎯 For Binary Classification (High Risk vs. Low Risk)
**Best Datasets**: Apache Jira, GitHub, BugSwarm
- Reason: Clear issue classification, good temporal data
- Features: Priority, time-to-resolution, type, component
- Expected Accuracy: 75-85%

#### 🎯 For Multi-Class Risk Categorization (Low/Medium/High/Critical)
**Best Datasets**: Mozilla Bugzilla + Apache Jira
- Reason: Rich severity/priority fields, domain expertise
- Features: Severity, priority, security/performance indicators
- Expected Accuracy: 65-80%

#### 🎯 For Time-to-Resolution Prediction
**Best Datasets**: Apache Jira + GitHub Issues
- Reason: Large historical dataset with clear timestamps
- Features: Issue type, component, assignee, description length
- Expected MAE: ±7-14 days

#### 🎯 For Bug Reproducibility/Severity Prediction
**Best Datasets**: BugSwarm (primary), Mozilla Bugzilla (secondary)
- Reason: BugSwarm has actual reproducibility data
- Features: Build logs, test results, code diffs
- Expected Accuracy: 80-90%

#### 🎯 For Security Risk Detection
**Best Datasets**: Mozilla Bugzilla + Linux Kernel + Apache Jira
- Reason: Security expertise, CVE tracking, detailed histories
- Features: Keywords, severity, component, historical patterns
- Expected Recall: 85-95%

---

## Hybrid Dataset Approach (Recommended)

### Tier 1: Quick Start (Best ROI for Time)
```
Total Issues: 150,000+
Setup Time: 12 hours
Data Quality: EXCELLENT
Recommended Model: Binary classification (high/low risk)

1. BugSwarm          (3,600 - structural data)
2. Apache Jira       (50,000 - enterprise experience)
3. GitHub (3 repos)  (30,000 - modern practices)
4. Mozilla (subset)  (20,000 - security focus)
5. Linux Kernel      (15,000 - stability focus)
```

**Script**:
```bash
#!/bin/bash
# Run in parallel with background jobs
python apache_jira_extractor.py &
python github_issue_extractor.py &
python bugswarm_extractor.py &
python mozilla_bugzilla_extractor.py &
python linux_bugzilla_extractor.py &

wait  # Wait for all to complete
python risk_prediction_prep.py
```

### Tier 2: Production Grade (Maximum Coverage)
```
Total Issues: 800,000+
Setup Time: 48 hours
Data Quality: EXCELLENT
Recommended Model: Multi-class risk categorization

Add to Tier 1:
6. GHArchive        (100,000+ for temporal patterns)
7. Eclipse Bugs     (100,000+ for enterprise Java)
8. Full Chromium    (500,000+ for scale/complexity)
```

---

## Quick Decision Tree

```
                     START HERE
                          |
                    What is your use case?
                    /          |         \
                   /           |          \
            Academic      Production      Demo/POC
             Research     System             |
             /                \             |
            /                  \            |
    Use BugSwarm +         Use Apache +  Use GitHub
    GitHub Issues          Jira + Mozilla  Issues API
    (1 week)               (2 weeks)       (1 day)
       |                      |              |
    Multi-class              Binary      Binary
    classification          classification classification
    Risk model              Risk model   Risk model
```

---

## Sampling Strategy (If Data Too Large)

### For 100,000 issue limit:
```python
import pandas as pd

# Load full dataset
df = pd.read_csv("combined_issues.csv")

# Stratified sampling by issue type and source
sample = df.groupby(['issue_type', 'source_platform'], 
                     group_keys=False).apply(
    lambda x: x.sample(frac=0.2, random_state=42)  # 20% of each stratum
)

# Ensure temporal coverage
sample = sample.sort_values('created_timestamp').sample(frac=1).reset_index(drop=True)

sample.to_csv("sampled_100k_issues.csv", index=False)
```

---

## Validation Checklist

Before training your model, verify:

- [ ] **Data Completeness**: < 20% missing values in key fields
- [ ] **Temporal Distribution**: Issues span multiple years
- [ ] **Class Balance**: Risk categories well-represented
- [ ] **No Data Leakage**: Test set doesn't overlap train
- [ ] **Duplicate Removal**: < 1% duplicate issues
- [ ] **Feature Scaling**: Applied to numeric features
- [ ] **Encoding**: Categorical variables properly encoded
- [ ] **Documentation**: Data lineage recorded
- [ ] **License Compliance**: Verified for each source
- [ ] **Privacy**: No sensitive PII in dataset

---

## Resources & Tools

### Data Collection
- `python-jira`: https://jira.readthedocs.io/
- `pygithub`: https://pygithub.readthedocs.io/
- `bugbug`: https://github.com/mozilla/bugbug
- `google-cloud-bigquery`: https://cloud.google.com/bigquery/docs

### Processing & Analysis
- `pandas`: https://pandas.pydata.org/
- `Apache Spark`: https://spark.apache.org/
- `Dask`: https://dask.org/
- `Polars`: https://www.pola.rs/

### Visualization
- `matplotlib/seaborn`: https://seaborn.pydata.org/
- `plotly`: https://plotly.com/python/
- `grafana`: https://grafana.com/

---

**Last Updated**: May 6, 2026
