# PRD Phase 2 — Advanced Analytics & Integrations

**Project:** AI-Driven Risk Prediction and Mitigation Framework  
**Version:** 2.0  
**Phase:** 2 — Advanced Analytics, Simulation & Integrations  
**Authors:** Risk AI Team  
**Status:** Implementation Complete

---

## 1. Overview

Phase 2 extends the core ML risk prediction engine (Phase 1) with six advanced capabilities:

| Feature ID | Name | Status |
|-----------|------|--------|
| F2-A | Time-Series Forecasting Engine (Prophet) | ✅ Complete |
| F2-B | Anomaly Detection Engine (Isolation Forest) | ✅ Complete |
| F2-C | NLP-Based Risk Detection | ✅ Complete |
| F2-D | What-If Scenario Simulation | ✅ Complete |
| F2-E | Jira REST API Integration | ✅ Complete |
| F2-F | OAuth 2.0 (3LO) Authentication | ✅ Complete |

---

## 2. Feature F2-A: Time-Series Forecasting Engine

### 2.1 Objective
Provide project managers with forward-looking cost and timeline risk predictions using a Prophet-based time-series model.

### 2.2 Requirements

| Req ID | Requirement | Acceptance Criteria |
|--------|-------------|---------------------|
| F2-A-01 | System shall train a Prophet model on project cost/timeline metrics | Model fits without error on ≥ 2 data points |
| F2-A-02 | System shall model 14-day sprint seasonality using Fourier series (order 3) | Sprint seasonality coefficient visible in model output |
| F2-A-03 | System shall support configurable forecast horizon (7–90 days) | Forecast output matches selected horizon ± 1 day |
| F2-A-04 | System shall compute forecast accuracy metrics: MAPE, RMSE, R² | Metrics returned in forecast result dictionary |
| F2-A-05 | System shall auto-generate normalized dates when no date column is present | Date column generated from today backwards for `n_rows` days |
| F2-A-06 | System shall display forecast with 80% and 95% confidence intervals | `yhat_lower`, `yhat_upper` present in forecast DataFrame |
| F2-A-07 | System shall provide CSV export of full forecast output | Download button present on Forecasting Lab page |
| F2-A-08 | System shall log forecast events with structured logging | Events written to `logs/forecasting_audit.log` |

### 2.3 Technical Implementation

**Model:** Facebook Prophet v1.x  
**Module:** `src/forecasting/forecast.py` — `ProjectForecaster` class  
**UI Page:** `app/pages/2_Forecasting.py` → `render_forecasting_page()`

**Configuration Constants:**
```python
DEFAULT_CONFIG = {
    'growth': 'linear',
    'changepoint_prior_scale': 0.05,
    'seasonality_prior_scale': 10,
    'daily_seasonality': False,
    'weekly_seasonality': True,
    'yearly_seasonality': False,
    'sprint_period': 14,
    'sprint_fourier_order': 3
}
```

**Error Handling:**
- `InsufficientDataError` — raised when < 2 data points
- `InvalidMetricColumnError` — raised when metric column missing
- `ProphetFittingError` — raised when model training fails

**Validation Strategy:** 80/20 train-test split on historical data; metrics computed on held-out test set.

---

## 3. Feature F2-B: Anomaly Detection Engine

### 3.1 Objective
Identify statistically unusual project tickets (budget overruns, timeline deviations) using unsupervised Isolation Forest.

### 3.2 Requirements

| Req ID | Requirement | Acceptance Criteria |
|--------|-------------|---------------------|
| F2-B-01 | System shall detect anomalies using Isolation Forest algorithm | Predictions include `is_anomaly` boolean column |
| F2-B-02 | System shall require minimum 100 rows for reliable detection | `ValueError` raised with < 100 rows |
| F2-B-03 | System shall classify anomalies into severity tiers: High, Medium, Low, Normal | `severity` column with 4-category `pd.Categorical` |
| F2-B-04 | System shall compute feature contributions using z-scores for each anomaly | `feature_contributions` column showing top-3 features |
| F2-B-05 | System shall support configurable contamination (0.01–0.15) | Contamination parameter accepted; model re-initialised when overridden |
| F2-B-06 | System shall compute ROC-AUC against domain-derived risk labels | AUC score displayed in Anomaly Triage Board |
| F2-B-07 | System shall display severity distribution histogram | Figure shown in `app/pages/3_Anomaly_Detection.py` |
| F2-B-08 | System shall allow CSV export of full anomaly report | Download button present on Anomaly Triage Board |
| F2-B-09 | Processing time shall not exceed 500ms for standard datasets | Warning logged if threshold exceeded |

### 3.3 Technical Implementation

**Algorithm:** Isolation Forest (scikit-learn), n_estimators=100  
**Module:** `src/anomaly/anomaly_detector.py` — `AnomalyEngine` class  
**UI Page:** `app/pages/3_Anomaly_Detection.py` → `render_anomaly_page()`

**Severity Binning:**
```python
bins = [-∞, -0.5, -0.2, 0, +∞]
labels = ["High", "Medium", "Low", "Normal"]
```

**Feature Contribution Method:** Z-score deviation from population mean for each numeric feature; top-3 most deviant features reported.

---

## 4. Feature F2-C: NLP-Based Risk Detection

### 4.1 Objective
Analyse unstructured Jira ticket text (Summary + Description) to detect latent risk signals not captured by numerical features alone.

### 4.2 Requirements

| Req ID | Requirement | Acceptance Criteria |
|--------|-------------|---------------------|
| F2-C-01 | System shall process ticket text using spaCy NLP pipeline | `en_core_web_sm` model loaded and operational |
| F2-C-02 | System shall detect risk signals using keyword matching + TF-IDF scoring | Risk score in [0, 1] range returned per ticket |
| F2-C-03 | System shall classify NLP risk into tiers: None, Low, Medium, High, Critical | Risk tier returned alongside numeric score |
| F2-C-04 | System shall compute performance metrics: Precision, Recall, F1 | Metrics computed against domain-labelled test set |
| F2-C-05 | System shall process 100 tickets in < 5 seconds | Benchmark test passes in CI environment |
| F2-C-06 | System shall provide confidence score per detection | Confidence value between 0.0 and 1.0 |
| F2-C-07 | System shall fall back to keyword-only mode if spaCy unavailable | Graceful degradation without ImportError |

### 4.3 Technical Implementation

**Module:** `src/nlp/nlp_risk_engine.py` — `RiskNLPEngine` class  
**Libraries:** spaCy (`en_core_web_sm`), sklearn TF-IDF

**Risk Signal Categories:**
- Deadline/timeline pressure keywords
- Technical complexity indicators
- Dependency risk keywords
- Resource/staffing risk keywords
- Budget constraint signals

---

## 5. Feature F2-D: What-If Scenario Simulation

### 5.1 Objective
Enable project managers to simulate hypothetical changes to ticket parameters and observe their predicted risk impact in real time.

### 5.2 Requirements

| Req ID | Requirement | Acceptance Criteria |
|--------|-------------|---------------------|
| F2-D-01 | System shall allow timeline extension simulation (0–30 days) | Timeline slider updates `Estimated_Days` in scenario row |
| F2-D-02 | System shall allow budget multiplier adjustment (0.5×–2.0×) | Budget multiplier updates `Budget_Allocated` in scenario row |
| F2-D-03 | System shall allow team efficiency simulation (0.5–1.5) | Efficiency inversely adjusts effective timeline |
| F2-D-04 | System shall allow story points delta (±8 points) | Story points adjusted and reflected in prediction |
| F2-D-05 | System shall allow priority and seniority categorical overrides | Dropdown selectors update categorical values in scenario |
| F2-D-06 | System shall display side-by-side original vs simulated risk comparison | `compare_scenarios()` returns structured comparison dict |
| F2-D-07 | System shall report new and mitigated risk drivers across scenarios | `new_drivers` and `mitigated_drivers` in delta dict |
| F2-D-08 | System shall provide SHAP force plot and table for both scenarios | Both views available via radio button selector |
| F2-D-09 | System shall allow CSV export of scenario comparison | Download button present on What-If page |

### 5.3 Technical Implementation

**Module:** `src/simulation/what_if_simulator.py` — `WhatIfSimulator` class  
**UI Page:** `app/pages/4_What_If_Simulation.py` → `render_what_if_page()`  
**UI Components:** `app/components/simulation_viewer.py`

**Budget/Timeline Logic:**
- If only timeline changed: budget auto-adjusted at `daily_burn_rate` (default $500/day)
- If budget explicitly changed: explicit value wins
- Team efficiency: `new_days = (baseline + extension) / efficiency`

---

## 6. Feature F2-E: Jira REST API Integration

### 6.1 Objective
Enable direct ingestion of live Jira project data into the ML pipeline, replacing or augmenting synthetic dataset generation.

### 6.2 Requirements

| Req ID | Requirement | Acceptance Criteria |
|--------|-------------|---------------------|
| F2-E-01 | System shall fetch Jira issues via REST API with JQL filtering | Issues returned as list of standardised metric dicts |
| F2-E-02 | System shall support pagination for large result sets (> 100 issues) | All pages fetched automatically up to `max_results` |
| F2-E-03 | System shall handle HTTP 410 fallback to `/rest/api/3/search/jql` | Retry with alternate endpoint on 410 response |
| F2-E-04 | System shall implement exponential backoff for rate-limit responses | `handle_rate_limiting()` with configurable retries |
| F2-E-05 | System shall map Jira fields to model-ready metric columns | `extract_metrics()` returns standardised dict |
| F2-E-06 | System shall support both Basic Auth (API token) and OAuth 2.0 | Auth header switches based on `access_token` presence |
| F2-E-07 | System shall merge synced issues into existing dataset (dedup by Issue_key) | No duplicate rows for same issue after merge |
| F2-E-08 | System shall log all Jira API interactions with timestamps | Events written to `logs/jira_integration.log` |

### 6.3 Technical Implementation

**Module:** `src/integrations/jira_client.py` — `JiraAPIClient` class  
**UI Page:** `app/pages/6_Jira_Sync.py` → `render_jira_sync_page()`

**Metric Extraction Mapping:**

| Jira Field | Model Column | Derivation |
|-----------|--------------|------------|
| `customfield_10016` | `Story_Points` | Direct (float) |
| `timeoriginalestimate` | `Estimated_Days` | seconds / 28800 |
| `timespent` | `Actual_Days` | seconds / 28800 |
| `priority.name` | `Priority` | Direct |
| `issuetype.name` | `Issue_Type` | Direct |
| Derived | `Budget_Allocated` | `max(500, story_points * 250)` |
| Derived | `Cost_Consumed` | `max(400, actual_days * 220 + story_points * 40)` |

---

## 7. Feature F2-F: OAuth 2.0 (3LO) Authentication

### 7.1 Objective
Enable secure Jira Cloud authentication via Atlassian OAuth 2.0 Authorization Code Flow (3-Legged OAuth).

### 7.2 Requirements

| Req ID | Requirement | Acceptance Criteria |
|--------|-------------|---------------------|
| F2-F-01 | System shall generate OAuth authorization URL with CSRF state | State token generated via `uuid4().hex` |
| F2-F-02 | System shall exchange authorization code for access + refresh tokens | `exchange_auth_code()` returns token dict with `expires_at` |
| F2-F-03 | System shall automatically refresh expired access tokens | `is_token_expired()` triggers `refresh_access_token()` before API calls |
| F2-F-04 | System shall fetch Atlassian Cloud ID post-authorization | `fetch_cloud_id()` queries accessible resources endpoint |
| F2-F-05 | System shall support manual URI fallback when `requests_oauthlib` unavailable | `get_authorization_url()` falls back to `urllib.parse.urlencode` |
| F2-F-06 | System shall log all OAuth events without exposing tokens | Events written to `logs/jira_oauth.log` |
| F2-F-07 | Token expiry check shall include 60-second skew buffer | `is_token_expired(expires_at, skew_seconds=60)` |

### 7.3 Technical Implementation

**Module:** `src/integrations/oauth_handler.py` — `JiraOAuthHandler` class  
**Atlassian Endpoints:**
- Authorization: `https://auth.atlassian.com/authorize`
- Token: `https://auth.atlassian.com/oauth/token`
- Resources: `https://api.atlassian.com/oauth/token/accessible-resources`

**Required Environment Variables:**
```bash
JIRA_OAUTH_CLIENT_ID=<Atlassian app client ID>
JIRA_OAUTH_CLIENT_SECRET=<Atlassian app client secret>
JIRA_OAUTH_REDIRECT_URI=http://localhost:8501
```

---

## 8. Non-Functional Requirements (Phase 2)

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01 | Anomaly detection processing time | < 500ms for ≤ 10,000 rows |
| NFR-02 | Forecast generation time | < 10s including metric computation |
| NFR-03 | NLP processing throughput | ≥ 20 tickets/second |
| NFR-04 | Jira API pagination | All pages fetched; no page skipped |
| NFR-05 | Dashboard cache TTL | Settings-driven; cache invalidated on model config change |
| NFR-06 | All logs | Structured format: `timestamp | name | level | func:line | message` |

---

## 9. Phase 2 Architecture Overview

```
Phase 2 Modules (src/)
├── forecasting/
│   ├── forecast.py          # ProjectForecaster (F2-A)
│   └── generate_forecast_figure.py
├── anomaly/
│   ├── anomaly_detector.py  # AnomalyEngine (F2-B)
│   ├── generate_anomaly_roc.py
│   └── generate_severity_histogram.py
├── nlp/
│   └── nlp_risk_engine.py   # RiskNLPEngine (F2-C)
├── simulation/
│   └── what_if_simulator.py # WhatIfSimulator (F2-D)
└── integrations/
    ├── jira_client.py       # JiraAPIClient (F2-E)
    └── oauth_handler.py     # JiraOAuthHandler (F2-F)

Phase 2 UI Pages (app/pages/)
├── 2_Forecasting.py         # F2-A
├── 3_Anomaly_Detection.py   # F2-B
├── 4_What_If_Simulation.py  # F2-D
└── 6_Jira_Sync.py           # F2-E + F2-F
```

---

## 10. Compliance & Validation

All Phase 2 features are validated by integration tests in `tests/integration/`:
- `test_phase2_forecasting.py` — F2-A validation
- `test_phase2_anomaly.py` — F2-B validation
- `test_nlp_integration.py` — F2-C validation
- `benchmark_nlp_engine.py` — F2-C performance benchmark

Unit tests in `tests/unit/`:
- `test_anomaly_engine.py` — F2-B unit tests
- `test_what_if_simulator.py` — F2-D unit tests
- `test_jira_oauth_handler.py` — F2-F unit tests