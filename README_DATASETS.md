# Jira & Bug Tracking Datasets - Master Index

**Last Updated**: May 7, 2026  
**Total Documents**: 3 comprehensive guides  
**Total Resources Identified**: 15+ publicly available datasets

---

## 📚 Documentation Overview

This package contains **3 comprehensive guides** to help you identify, access, and prepare Jira and bug tracking datasets for AI risk prediction model training.

### 📄 Guide 1: JIRA_DATASETS_GUIDE.md
**Purpose**: Comprehensive directory of all available datasets  
**Length**: ~21,900 words  
**Best For**: Research, understanding all options

**Contents**:
- Jira-native datasets (Apache Foundation projects)
- GitHub Issues datasets (alternative to Jira)
- Academic research datasets (BugSwarm, MSR collections)
- Open source project datasets (Linux, Mozilla, Apache, Eclipse)
- Public bug tracking systems (Chromium, GnuBug)
- Kaggle datasets with issue tracking data
- Commercial solutions
- Data collection strategies
- Compliance & licensing information

**Key Takeaway**:
> **150,000+ issues** available immediately from Tier 1 sources (BugSwarm, Apache Jira, GitHub)

---

### 📄 Guide 2: DATA_COLLECTION_GUIDE.md
**Purpose**: Step-by-step implementation with code examples  
**Length**: ~11,000 words  
**Best For**: Developers, implementation

**Contents**:
- Python scripts for Apache Jira extraction
- Python scripts for GitHub Issues extraction
- Python scripts for BugSwarm dataset download
- Data combination and feature engineering
- Risk prediction label creation
- Train/test split strategies
- Requirements.txt for quick setup
- Quick start commands

**Key Resources**:
- 4 production-ready Python classes
- 5+ runnable example scripts
- Feature engineering pipeline
- Risk categorization system

**Quick Start**:
```bash
pip install -r requirements.txt
export GITHUB_TOKEN="your_token"
python apache_jira_extractor.py &
python github_issue_extractor.py &
python risk_prediction_prep.py
```

---

### 📄 Guide 3: DATASET_COMPARISON_MATRIX.md
**Purpose**: Quick reference and comparison tables  
**Length**: ~7,500 words  
**Best For**: Decision-making, quick lookup

**Contents**:
- Executive summary comparison table
- Detailed feature completeness matrix
- API & access methods comparison
- Feature richness scoring
- Time estimates for collection
- Storage & processing requirements
- Risk prediction model suitability matrix
- Tier 1 vs. Tier 2 dataset selection
- Quick decision tree
- Sampling strategies
- Validation checklist

**Key Tables**:
| Metric | Best | Runner-up |
|--------|------|-----------|
| Ease of Setup | BugSwarm (2 hrs) | GitHub API (6 hrs) |
| Data Quality | BugSwarm | Mozilla Bugzilla |
| Issue Volume | Mozilla (500k) | GitHub (100k+) |
| Feature Richness | BugSwarm | Apache Jira |
| Access Cost | Free | Free |
| Best for Production | Apache Jira | GitHub |

---

## 🎯 Quick Decision Guide

### **I want to START IMMEDIATELY** ⚡
**→ Use: Tier 1 Dataset (12 hours setup)**
1. BugSwarm (Docker images)
2. Apache Jira REST API
3. GitHub Issues API

Files: `DATASET_COMPARISON_MATRIX.md` (Tier 1 section) + `DATA_COLLECTION_GUIDE.md`

### **I need COMPREHENSIVE COVERAGE** 📊
**→ Use: Tier 1 + Tier 2 Datasets (48 hours setup)**
Add to above:
4. GHArchive BigQuery
5. Eclipse Project Bugs
6. Full Chromium tracker

Files: All 3 guides

### **I need SECURITY-FOCUSED DATA** 🔒
**→ Use: Mozilla + Linux + Apache combination**
1. Mozilla Firefox Bugzilla (500k issues with security tags)
2. Linux Kernel Bugzilla (150k mission-critical issues)
3. Apache Security projects

Files: `JIRA_DATASETS_GUIDE.md` (sections 9-11) + relevant extraction code

### **I need ACADEMIC PUBLICATION DATA** 📚
**→ Use: BugSwarm + MSR datasets**
1. BugSwarm (ICSE 2019, 3,600 artifacts)
2. Defects4J
3. Research datasets from Zenodo

Files: `JIRA_DATASETS_GUIDE.md` (section: Academic Research Datasets)

### **I need PRODUCTION ENTERPRISE DATA** 💼
**→ Use: Apache Jira projects + Internal instances**
1. Apache Foundation Jira (50k+ issues, proven at scale)
2. Custom Jira extraction from your instances
3. GitHub Issues (modern alternative)

Files: `DATA_COLLECTION_GUIDE.md` (Apache Jira section) + `JIRA_DATASETS_GUIDE.md` (Jira-native section)

---

## 📈 Expected Results by Dataset Selection

### Tier 1 (Recommended Starting Point)
```
Total Issues Collected: 150,000+
Setup Time: 12 hours
Model Type: Binary classification (High risk / Low risk)
Expected Accuracy: 75-85%
Time-to-value: 24 hours
```

**Composition**:
- BugSwarm: 3,600 (reproducible failures + builds + tests)
- Apache Jira: 50,000+ (enterprise experience)
- GitHub: 30,000-50,000 (modern practices, larger community)
- Mozilla: 10,000-20,000 (security/stability focus)
- Linux Kernel: 10,000-15,000 (mission-critical systems)

### Tier 2 (Comprehensive)
```
Total Issues Collected: 800,000+
Setup Time: 48 hours
Model Type: Multi-class risk categorization
Expected Accuracy: 70-80%
Time-to-value: 72 hours
```

**Additional Sources**:
- GHArchive: 100,000+ temporal events
- Eclipse: 100,000+ enterprise Java
- Chromium: 500,000+ large-scale

---

## 🔧 Implementation Roadmap

### Week 1: Setup & Collection
- [ ] Day 1: Review all 3 guides (4 hours)
- [ ] Day 2-3: Set up environment, configure credentials (8 hours)
- [ ] Day 4-5: Run data collection scripts in parallel (12 hours)
- [ ] Day 6-7: Validate, deduplicate, store (8 hours)

### Week 2: Feature Engineering & Preparation
- [ ] Day 8-9: Feature engineering pipeline (8 hours)
- [ ] Day 10: Create risk labels & train/test split (4 hours)
- [ ] Day 11: Data validation & quality checks (4 hours)
- [ ] Day 12-14: Create baseline model & evaluate (12 hours)

**Total First 2 Weeks**: ~60 hours productive work

---

## 📊 Dataset Statistics At-a-Glance

### By Size (Number of Issues)
1. **Chromium**: 1,000,000+ issues
2. **Mozilla Firefox Bugzilla**: 500,000+ issues
3. **GitHub Issues (via GHArchive)**: 100,000,000+ events
4. **Eclipse Project Bugs**: 400,000+ issues
5. **Linux Kernel Bugzilla**: 150,000+ issues
6. **Apache Jira Projects**: 50,000+ issues (combined)
7. **GitHub Major Projects**: 30,000-50,000 issues (each)
8. **BugSwarm**: 3,600 artifacts (but with most features)

### By Jira-Native Authenticity ✓
1. **Apache Foundation Jira** - Direct Jira instances
2. **Atlassian Research** - Anonymized Jira Cloud data
3. (All others are alternatives: GitHub, Bugzilla, etc.)

### By Data Quality for Risk Prediction ⭐
1. **BugSwarm** (5/5) - Real builds, tests, diffs, reproducibility
2. **Mozilla Bugzilla** (4.5/5) - Security expertise, comprehensive tracking
3. **Apache Jira** (4.5/5) - Rich fields, enterprise experience
4. **Linux Kernel Bugzilla** (4/5) - Mission-critical, detailed severity
5. **GitHub Issues** (3.5/5) - Good but lacks priority/severity fields

### By Ease of Access 🚀
1. **GitHub Issues API** - No auth required (limited), OAuth simple
2. **Apache Jira REST API** - No auth required, unlimited
3. **BugSwarm Docker** - Docker pull, done
4. **Mozilla Bugzilla API** - REST, no auth required
5. **Chromium Tracker** - Rate limited, harder to bulk export

---

## 📦 File Organization

After completing the guides, you'll have:

```
project_root/
├── JIRA_DATASETS_GUIDE.md                 ← START HERE (overview)
├── DATASET_COMPARISON_MATRIX.md           ← Use for decisions
├── DATA_COLLECTION_GUIDE.md               ← Use for implementation
│
├── data_extraction/
│   ├── apache_jira_extractor.py
│   ├── github_issue_extractor.py
│   ├── bugswarm_extractor.py
│   ├── mozilla_bugzilla_extractor.py
│   └── risk_prediction_prep.py
│
├── data/
│   ├── raw/
│   │   ├── apache_jira_issues.csv
│   │   ├── github_issues.csv
│   │   ├── bugswarm_artifacts.csv
│   │   └── mozilla_bugzilla_issues.csv
│   │
│   └── processed/
│       ├── combined_issues.csv
│       ├── risk_prediction_train.csv
│       └── risk_prediction_test.csv
│
└── results/
    ├── dataset_statistics.json
    ├── risk_distribution.png
    └── model_baseline_performance.txt
```

---

## 🎓 Learning Outcomes

After working through these guides, you'll understand:

1. **Where** to find Jira-native and alternative bug tracking datasets
2. **How** to access each dataset programmatically
3. **What** fields are available in each source
4. **Why** certain datasets are better for specific risk prediction tasks
5. **When** to use Tier 1 vs. Tier 2 vs. full collection
6. **How much** time and resources each approach requires
7. **Code examples** for extracting, processing, and preparing data
8. **Comparison metrics** to select the best dataset for your use case
9. **Best practices** for combining multiple data sources
10. **Validation techniques** to ensure data quality

---

## 🔍 Cross-Reference Quick Links

### By Use Case

**Risk Prediction (General)**
- Start: `DATASET_COMPARISON_MATRIX.md` → "Risk Prediction Model Suitability"
- Implementation: `DATA_COLLECTION_GUIDE.md` → "Combining and Feature Engineering"

**Security Risk Detection**
- Overview: `JIRA_DATASETS_GUIDE.md` → "Mozilla Firefox Bugzilla" section
- Data: Mozilla, Linux Kernel, Apache Security projects

**Time-to-Resolution Prediction**
- Overview: `JIRA_DATASETS_GUIDE.md` → "Apache Foundation Projects" section
- Implementation: `DATA_COLLECTION_GUIDE.md` → "Time-based features" section

**Reproducibility Analysis**
- Data: BugSwarm Dataset (`JIRA_DATASETS_GUIDE.md` → "BugSwarm Dataset")
- Implementation: `DATA_COLLECTION_GUIDE.md` → "BugSwarm Dataset Download"

**Academic Research**
- Overview: `JIRA_DATASETS_GUIDE.md` → "Academic Research Datasets" section
- Resources: Links to Zenodo, GitHub, university repositories

### By Access Method

**REST API Access**
- `JIRA_DATASETS_GUIDE.md`: Apache Jira, GitHub, Mozilla Bugzilla, Linux Kernel sections
- `DATA_COLLECTION_GUIDE.md`: Implementation code for all API-based sources

**Docker/Binary Download**
- `JIRA_DATASETS_GUIDE.md`: BugSwarm Dataset section
- `DATA_COLLECTION_GUIDE.md`: "BugSwarm Dataset Download" section

**SQL Query (BigQuery)**
- `JIRA_DATASETS_GUIDE.md`: "GHArchive Project History Dataset" section
- Example SQL queries included

**Bulk XML Export**
- `JIRA_DATASETS_GUIDE.md`: Bugzilla instances section
- Apache Jira, Mozilla Bugzilla, Linux Kernel, Eclipse

### By Data Size

**Quick Start (< 50 issues, demo)**
- Use GitHub single repo API

**Small Dataset (10k-50k issues)**
- BugSwarm + single Apache project + GitHub single repo

**Medium Dataset (50k-200k issues, RECOMMENDED)**
- Tier 1 selection (`DATASET_COMPARISON_MATRIX.md`)

**Large Dataset (200k-800k+ issues)**
- Tier 2 selection (`DATASET_COMPARISON_MATRIX.md`)

---

## ⚠️ Important Notes

1. **Licensing**: Always verify license compliance for your intended use
   - Academic: Mostly CC-BY-4.0 (free)
   - Open Source: Various (usually commercial-friendly)
   - Internal/Commercial: Requires permissions

2. **Rate Limiting**: Be respectful of API limits
   - GitHub: 5,000 requests/hour (authenticated)
   - Apache Jira: Fair use policy (usually generous)
   - Mozilla: Unlimited (but be reasonable)

3. **Data Privacy**: 
   - Public repositories are publicly available
   - Don't republish internal/private issue data
   - Remove sensitive information before sharing datasets

4. **Temporal Considerations**:
   - Older issues may have incomplete data
   - Recent issues may not have resolution data yet
   - Use temporal train/test split (not random)

5. **Reproducibility**:
   - Document all data extraction steps
   - Version control your scripts
   - Record timestamps and parameters used
   - Save raw data in addition to processed

---

## 🚀 Next Steps

1. **Read** `JIRA_DATASETS_GUIDE.md` (30 min) for comprehensive overview
2. **Review** `DATASET_COMPARISON_MATRIX.md` (15 min) to select your tier
3. **Implement** `DATA_COLLECTION_GUIDE.md` (12-48 hours) based on tier selection
4. **Validate** using the checklist in `DATASET_COMPARISON_MATRIX.md`
5. **Start training** your risk prediction model!

---

## 📞 Support & Resources

### If You Need Help With...

**Understanding Jira fields**: See `JIRA_DATASETS_GUIDE.md` → "Available Fields" sections

**API authentication**: See `DATA_COLLECTION_GUIDE.md` → individual extractor classes

**Feature engineering**: See `DATA_COLLECTION_GUIDE.md` → "RiskPredictionDataPrep" class

**Choosing datasets**: See `DATASET_COMPARISON_MATRIX.md` → "Quick Decision Tree"

**Handling large datasets**: See `DATASET_COMPARISON_MATRIX.md` → "Sampling Strategy"

**Validating data**: See `DATASET_COMPARISON_MATRIX.md` → "Validation Checklist"

---

## 📝 Citation

If you use these guides in academic work, please cite:

```bibtex
@misc{jira_datasets_guide_2026,
  title={Comprehensive Guide to Publicly Available Jira and Bug Tracking Datasets},
  author={AI Risk Prediction Framework Team},
  year={2026},
  url={https://github.com/your-org/ai-risk-prediction-framework}
}
```

---

**Document Version**: 1.0  
**Created**: May 7, 2026  
**Status**: Complete and Ready for Use  
**Maintenance**: Regular updates planned as new datasets emerge
