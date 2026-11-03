# Module Overview — AI-Driven Risk Prediction Framework

Each module in `src/` is self-contained and follows the domain-first architecture.

---

## `src/preprocessing/` — Data Pipeline & Feature Engineering
- **`data_pipeline.py`**: Loads data from live Jira API (with OAuth) or falls back to local CSV. Engineers features (budget overrun %, schedule overrun %, efficiency score), computes risk labels, outputs `data/ml_ready_data.csv`.
- **`feature_engineering.py`**: Canonical feature preprocessing pipeline shared by training, SHAP, and prediction paths. Handles target leakage removal, one-hot encoding, and feature name sanitization.
- **`feature_alignment.py`**: Single-row preprocessing utility for real-time prediction alignment with training columns.

## `src/training/` — Model Training
- **`train.py`**: Trains XGBoost and RandomForest classifiers with leakage prevention, stratified splits, and class imbalance handling. Saves `xgb_model.pkl`, `rf_model.pkl`, `feature_columns.pkl`.
- **`generate_paper_plots.py`**: Generates IEEE-ready ROC-AUC curve and Confusion Matrix heatmap at 300 DPI. Outputs to `app/components/`.

## `src/database/` — Authentication & Persistence
- **`auth_db.py`**: SQLite-backed authentication with PBKDF2-hashed passwords (120K iterations). Supports user creation, verification, role-based lookup, and email lookup. Admin bootstrap via `scripts/bootstrap_admin.py`.

## `src/xai/` — Explainable AI
- **`shap_explainer.py`**: Wraps `shap.TreeExplainer` for XGBoost. Normalizes raw SHAP values to percentage-of-influence format. Generates global summary and local force plots. Outputs to `app/components/shap_summary.png`.

## `src/mitigation/` — GenAI Advisory
- **`llm_agent.py`**: Routes high-risk predictions to **Qwen 3.5** via NVIDIA Inference API. Prompt includes risk level + top 5 SHAP drivers. Parses reasoning and strategy XML tags. 3-attempt exponential backoff.

## `src/forecasting/` — Time-Series Forecasting
- **`forecast.py`** (`ProjectForecaster`): Facebook Prophet with 14-day sprint Fourier seasonality (order 3). 80/20 train-test split. Computes MAPE, RMSE, R². Returns forecast DataFrame with confidence intervals.
- **`generate_forecast_figure.py`**: Standalone script generating publication-quality Prophet forecast figure at 300 DPI.

## `src/anomaly/` — Anomaly Detection
- **`anomaly_detector.py`** (`AnomalyEngine`): Isolation Forest (n_estimators=100). Severity binning to High / Medium / Low / Normal. Feature contributions via z-score deviation. ROC-AUC evaluation against domain-derived labels.
- **`generate_anomaly_roc.py`**: Standalone ROC-AUC evaluation and figure generation for anomaly pipeline.
- **`generate_severity_histogram.py`**: Standalone severity distribution histogram generator.

## `src/nlp/` — NLP Risk Engine
- **`nlp_risk_engine.py`** (`RiskNLPEngine`): spaCy `en_core_web_sm` entity extraction. 5 risk signal categories (deadline, technical, dependency, resource, budget). Returns risk score [0,1], confidence level, risk tier, and entity list. Graceful fallback to keyword-only mode if spaCy unavailable.

## `src/simulation/` — What-If Simulation
- **`what_if_simulator.py`** (`WhatIfSimulator`): Applies deltas to a baseline ticket row (timeline extension, budget multiplier, team efficiency, categorical overrides). `compare_scenarios()` returns structured comparison with new/mitigated risk drivers.

## `src/integrations/` — External Integrations
- **`jira_client.py`** (`JiraAPIClient`): Jira REST API v3. JQL filtering, automatic pagination, HTTP 410 fallback, OAuth token auto-refresh. Maps Jira fields to model-ready columns.
- **`oauth_handler.py`** (`JiraOAuthHandler`): Atlassian 3-legged OAuth 2.0. Authorization URL generation (with CSRF state), code exchange, token refresh (60s skew buffer), Cloud ID retrieval. Token caching to `.jira_tokens.json`.