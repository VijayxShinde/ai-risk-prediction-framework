# Architecture — AI-Driven Risk Prediction Framework

**Version:** 2.1.0 | **Status:** Production-Ready

---

## System Overview

The framework follows a **3-layer architecture**: Streamlit presentation, domain-first ML/AI intelligence, and external services.

---

## Directory Structure (Actual — Post Audit & Codebase Fixes)

```
ai-risk-prediction-framework/
├── app/                            # Streamlit frontend
│   ├── main.py                     # Entry point (login gate + OAuth callback)
│   ├── pages/                      # 7 Streamlit MPA pages
│   │   ├── 1_Dashboard.py
│   │   ├── 2_Forecasting.py        # Phase 2-A
│   │   ├── 3_Anomaly_Detection.py  # Phase 2-B
│   │   ├── 4_What_If_Simulation.py # Phase 2-D
│   │   ├── 5_Settings.py
│   │   ├── 6_Jira_Sync.py          # Phase 2-E/F
│   │   └── 7_Ticket_Auditor.py
│   ├── views/                      # Page view logic
│   │   ├── dashboard.py            # Dashboard + Forecasting + Anomaly views
│   │   ├── auditor.py
│   │   ├── what_if.py
│   │   ├── jira_sync.py
│   │   ├── login.py
│   │   └── settings.py
│   ├── components/                 # Reusable UI components
│   │   ├── genai_auditor.py
│   │   ├── ieee_metrics.py         # IEEE publication metric panels
│   │   ├── shap_visuals.py
│   │   ├── simulation_viewer.py
│   │   ├── ticket_viewer.py
│   │   └── audit_trail_viewer.py
│   └── utils/
│       ├── styles.py               # Design system (COLORS dict, CSS, headers)
│       ├── routes.py               # Safe page navigation
│       ├── sidebar.py
│       ├── audit_storage.py
│       └── env.py
│
├── src/                            # Backend — domain-first architecture
│   ├── config.py                   # Path constants (Paths class) + env helpers
│   ├── database/
│   │   └── auth_db.py              # SQLite auth (PBKDF2, role-based lookup)
│   ├── preprocessing/
│   │   ├── data_pipeline.py        # Jira API + CSV data ingestion pipeline
│   │   ├── feature_engineering.py  # Canonical preprocessing for all paths
│   │   └── feature_alignment.py    # Single-row inference-time preprocessing
│   ├── training/
│   │   ├── train.py                # XGBoost + RF training pipeline
│   │   └── generate_paper_plots.py # IEEE ROC-AUC + Confusion Matrix
│   ├── xai/
│   │   └── shap_explainer.py       # SHAP TreeExplainer
│   ├── mitigation/
│   │   └── llm_agent.py            # Qwen 3.5 GenAI agent (NVIDIA API)
│   ├── forecasting/
│   │   ├── forecast.py             # ProjectForecaster (Prophet)
│   │   └── generate_forecast_figure.py
│   ├── anomaly/
│   │   ├── anomaly_detector.py     # AnomalyEngine (Isolation Forest)
│   │   ├── generate_anomaly_roc.py
│   │   └── generate_severity_histogram.py
│   ├── nlp/
│   │   └── nlp_risk_engine.py      # RiskNLPEngine (spaCy + TF-IDF)
│   ├── simulation/
│   │   └── what_if_simulator.py    # WhatIfSimulator
│   └── integrations/
│       ├── jira_client.py          # JiraAPIClient (REST v3)
│       └── oauth_handler.py        # JiraOAuthHandler (3LO OAuth 2.0)
│
├── scripts/                        # Admin & maintenance scripts
│   ├── bootstrap_admin.py          # SQLite admin user creation
│   ├── generate_curated_anomalies.py
│   └── test_llm_connection.py
│
├── models/                         # Serialized artefacts
│   ├── xgb_model.pkl
│   ├── rf_model.pkl
│   ├── isolation_forest.pkl
│   └── feature_columns.pkl
│
├── tests/
│   ├── unit/                       # 5 files, 73 tests
│   └── integration/                # 4 files, 9 tests
│
├── docs/                           # PRDs, architecture, compliance
└── reports/                        # Phase 2 diagnostic figures
```

---

## Key Modules

| Class | Module | Purpose |
|-------|--------|---------|
| `ProjectForecaster` | `src/forecasting/forecast.py` | Prophet + 14-day sprint seasonality |
| `AnomalyEngine` | `src/anomaly/anomaly_detector.py` | Isolation Forest, severity tiers, z-score contributions |
| `RiskNLPEngine` | `src/nlp/nlp_risk_engine.py` | spaCy entity extraction + TF-IDF risk scoring |
| `WhatIfSimulator` | `src/simulation/what_if_simulator.py` | Timeline/budget/efficiency scenario deltas |
| `JiraAPIClient` | `src/integrations/jira_client.py` | REST API v3, pagination, token auto-refresh |
| `JiraOAuthHandler` | `src/integrations/oauth_handler.py` | 3-legged OAuth 2.0, token refresh, cloud ID lookup |
| `generate_mitigation_strategy` | `src/mitigation/llm_agent.py` | Qwen 3.5 via NVIDIA, exponential backoff |

---

## Import Patterns

```python
# Domain-specific (recommended)
from src.anomaly import AnomalyEngine
from src.nlp import RiskNLPEngine
from src.forecasting import ProjectForecaster
from src.simulation.what_if_simulator import WhatIfSimulator
from src.integrations.jira_client import JiraAPIClient
from src.integrations.oauth_handler import JiraOAuthHandler
from src.mitigation.llm_agent import generate_mitigation_strategy
from src.database.auth_db import create_user, verify_user, get_user
from src.preprocessing.feature_engineering import preprocess_features
from src.config import Paths

# Main package re-exports
from src import RiskNLPEngine, AnomalyEngine
```

---

## Authentication & Security

| Component | Implementation |
|-----------|---------------|
| Password Hashing | PBKDF2 with SHA-256, 120K iterations, 16-byte salt |
| Session Auth | `st.session_state["authenticated"]` (client-side, Streamlit limitation) |
| Admin Bootstrap | `scripts/bootstrap_admin.py` via `.env` variables |
| Jira OAuth | Atlassian 3LO flow, tokens cached in `.jira_tokens.json` |
| Token Refresh | Auto-refresh with 60-second skew buffer before expiry |

---

## Testing

```bash
# Full suite (82/82 passing)
.venv\Scripts\python.exe -m pytest tests/ -v

# Unit tests only
.venv\Scripts\python.exe -m pytest tests/unit/ -v

# Integration tests only
.venv\Scripts\python.exe -m pytest tests/integration/ -v

# With coverage
.venv\Scripts\python.exe -m pytest tests/ --cov=src --cov-report=html
```

---

## Design Principles

1. **Domain-first** — modules named by domain, not by type
2. **Lazy imports** — `app/views/__init__.py` uses `__getattr__` to prevent cascade failures
3. **Graceful degradation** — all external API failures return safe fallbacks
4. **TTL caching** — GenAI recommendations cached for 600s in session state
5. **Unified design system** — all styling via `app/utils/styles.py` `COLORS` dict
6. **Single-source preprocessing** — `src/preprocessing/feature_engineering.py` is the canonical preprocessor for training, SHAP, and prediction paths
7. **No inverted dependencies** — `src/` never imports from `app/`