# AI-Driven Risk Prediction and Mitigation Framework

**Version:** 2.1.0 | **Status:** ✅ Production-Ready | **Python:** 3.10+  
**Final Year Project** — B.E. Computer Engineering  
**IEEE Publication Support:** Phase 1 PRD + ROC-AUC / Confusion Matrix artefacts included

---

## Overview

An end-to-end AI system for **predicting, explaining, and mitigating project risks** from Jira-style ticket data. The framework combines supervised ML classification, time-series forecasting, unsupervised anomaly detection, NLP risk extraction, and a GenAI advisory layer — all surfaced through a Streamlit dashboard with live Jira integration.

---

## ✅ Features (Phase 1 + Phase 2 — Complete)

| Feature | Module | Status |
|---------|--------|--------|
| XGBoost Risk Classifier (Low / Medium / High) | `src/training/` | ✅ |
| SHAP Explainability (global + local) | `src/xai/` | ✅ |
| GenAI Auditor — Qwen 3.5 via NVIDIA API | `src/mitigation/` | ✅ |
| Exponential Backoff & Retry (3 attempts) | `src/mitigation/` | ✅ |
| Prophet Time-Series Forecasting | `src/forecasting/` | ✅ |
| Isolation Forest Anomaly Detection | `src/anomaly/` | ✅ |
| NLP Risk Detection — spaCy + TF-IDF | `src/nlp/` | ✅ |
| What-If Scenario Simulation | `src/simulation/` | ✅ |
| Jira REST API Integration (pagination + backoff) | `src/integrations/` | ✅ |
| OAuth 2.0 (3-Legged) Authentication | `src/integrations/` | ✅ |
| Streamlit Dashboard (7 pages) | `app/` | ✅ |
| SQLite-Based Authentication (PBKDF2) | `src/database/` | ✅ |
| Settings persistence across sessions | `app/views/settings.py` | ✅ |
| IEEE-Ready Paper Plots (ROC-AUC, Confusion Matrix, SHAP) | `src/training/` | ✅ |

---

## 🚀 Quick Start

```bash
# 1. Clone and create virtual environment
git clone <repo-url>
cd ai-risk-prediction-framework
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 3. Configure environment
cp env.example.md .env          # then fill in your API keys

# 4. Generate dataset & train models (first run only)
python src/preprocessing/data_pipeline.py
python src/training/train.py

# 5. Launch dashboard
streamlit run app/main.py
```

**Default login:** `admin` / `admin`

---

## 📁 Repository Structure

```
ai-risk-prediction-framework/
├── app/                        # Streamlit frontend
│   ├── main.py                 # Entry point (login gate)
│   ├── pages/                  # 7 MPA pages (Dashboard → Jira Sync)
│   ├── views/                  # Page-level view logic
│   ├── components/             # Reusable UI components (SHAP, GenAI, etc.)
│   └── utils/                  # Routing, sidebar, styles, audit storage
├── src/                        # Backend / ML layer
│   ├── preprocessing/          # Data pipeline & feature engineering
│   ├── training/               # XGBoost training + IEEE paper plots
│   ├── xai/                    # SHAP explainer
│   ├── mitigation/             # GenAI LLM agent (Qwen 3.5 / NVIDIA)
│   ├── forecasting/            # Prophet forecaster (14-day sprint seasonality)
│   ├── anomaly/                # Isolation Forest anomaly detector
│   ├── nlp/                    # NLP risk engine (spaCy + TF-IDF)
│   ├── simulation/             # What-If scenario simulator
│   └── integrations/           # Jira REST client + OAuth 2.0 handler
├── models/                     # Serialized model artefacts (.pkl)
├── data/                       # Datasets (ml_ready_data.csv, raw_jira_data.csv)
├── tests/                      # 82 tests (82 passing)
│   ├── unit/                   # 5 unit test files
│   └── integration/            # 4 integration test files
├── docs/                       # PRDs, architecture & compliance docs
├── reports/                    # Phase 2 diagnostic figures
└── logs/                       # Runtime logs & user data store
```

---

## 🧪 Running Tests

```bash
# Full suite
.venv\Scripts\python.exe -m pytest tests/ -v

# Unit tests only
.venv\Scripts\python.exe -m pytest tests/unit/ -v

# Integration tests only
.venv\Scripts\python.exe -m pytest tests/integration/ -v

# With coverage
.venv\Scripts\python.exe -m pytest tests/ --cov=src --cov-report=html
```

**Current:** 82/82 passing ✅

---

## 🔑 Environment Variables

See `env.example.md` for the full list. Minimum required:

| Variable | Purpose |
|----------|---------|
| `NVIDIA_API_KEY` | GenAI auditor (Qwen 3.5 via NVIDIA) |
| `JIRA_URL` | Jira instance base URL |
| `JIRA_OAUTH_CLIENT_ID` | Atlassian OAuth app client ID |
| `JIRA_OAUTH_CLIENT_SECRET` | Atlassian OAuth app client secret |
| `JIRA_OAUTH_REDIRECT_URI` | OAuth callback (default: http://localhost:8501) |

---

## 📊 Model Performance

| Metric | Target | Status |
|--------|--------|--------|
| Multi-Class Accuracy | > 80% | ✅ Validated |
| Macro ROC-AUC | > 0.85 | ✅ Validated |
| Weighted F1-Score | > 0.78 | ✅ Validated |
| Anomaly ROC-AUC (vs domain labels) | > 0.75 | ✅ 0.776 |
| Forecast MAPE | Displayed | ✅ Computed |
| NLP Throughput | ≥ 20 tickets/sec | ✅ Benchmarked |

---

## 📖 Documentation

| Document | Location |
|----------|---------|
| Phase 1 PRD (Core Architecture) | `docs/PRD_Phase1_Core_Architecture.md` |
| Phase 2 PRD (Advanced Analytics) | `docs/PRD_Phase2_Advanced_Analytics.md` |
| Architecture Overview | `docs/ARCHITECTURE.md` |
| Module Overview | `docs/module_overview.md` |
| Requirements Compliance (F2-C) | `docs/F2C_REQUIREMENTS_COMPLIANCE.md` |
| Import Guide | `docs/IMPORT_GUIDE.md` |

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Classifier | XGBoost 2.1.4 |
| Explainability | SHAP (TreeExplainer) |
| Forecasting | Facebook Prophet |
| Anomaly Detection | scikit-learn Isolation Forest |
| NLP | spaCy `en_core_web_sm` + TF-IDF |
| GenAI | Qwen 3.5 via NVIDIA Inference API |
| Dashboard | Streamlit 1.32+ |
| Jira Integration | Atlassian REST API v3 + OAuth 2.0 |
| Language | Python 3.10+ |
