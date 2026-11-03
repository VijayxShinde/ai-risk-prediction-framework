# Live Demo Runbook — Risk Framework

Use this checklist before and during the live demo.

---

## 0) Pre-Flight (5–10 min before)

- Ensure `.env` has: `NVIDIA_API_KEY`, `JIRA_URL`, `JIRA_OAUTH_CLIENT_ID`, `JIRA_OAUTH_CLIENT_SECRET`, `JIRA_OAUTH_REDIRECT_URI`.
- Ensure models exist: `models/xgb_model.pkl`, `models/feature_columns.pkl`.
- Ensure plots exist:
  - `app/components/confusion_matrix.png`
  - `app/components/roc_curve.png`
  - `app/components/shap_summary.png`
- Ensure curated anomalies exist: `data/curated_anomalies.csv`.
- If needed, bootstrap admin: `python scripts/bootstrap_admin.py`.

---

## 1) Start the App

Command:
```bash
streamlit run app/main.py
```

Expected:
- Login screen loads without errors.

---

## 2) Login

- Login with admin credentials (from `.env` or bootstrap output).

Expected:
- Redirect to Dashboard.
- No red error banner.

---

## 3) Dashboard Overview

- Confirm the page title and subtitle render.
- Verify metrics: Global Risk Score, Total Budget, Active Tickets, Detected Anomalies.

Expected:
- Forecast chart (if `reports/fig_phase2_a_prophet_forecast.png` exists).
- Severity figure (if `app/components/severity_breakdown.png` exists).
- IEEE metrics expander shows Confusion Matrix + ROC images.

---

## 4) Jira Sync (OAuth + Live Tickets)

- Navigate to **Jira Sync**.
- Click **Authorize with Jira** → approve in Atlassian.
- Return to Jira Sync.

Expected:
- OAuth status = Connected.
- Cloud ID populated.
- Click **Sync Now** → issues load.

If 0 issues:
- Use JQL: `project = RISK ORDER BY updated DESC`.
- Verify project key and permissions.

---

## 5) Ticket Auditor

- Navigate to **Ticket Auditor**.
- Select a synced Jira ticket.

Expected:
- Risk prediction appears.
- SHAP top drivers appear.
- GenAI mitigation button available.

---

## 6) GenAI Mitigation

- Click **Generate Mitigation Strategy**.

Expected:
- Reasoning + strategy displayed.
- Cache notice shown (TTL).

---

## 7) What-If Simulation

- Open **What-If Simulation**.
- Adjust timeline extension, budget, efficiency, priority.

Expected:
- Side-by-side comparison with delta metrics.
- New/mitigated drivers displayed.

---

## 8) Forecasting Lab

- Open **Forecasting Lab**.
- Click **Regenerate Forecast**.

Expected:
- Forecast plot with confidence intervals.
- MAPE/RMSE/R² metrics shown.
- Download CSV button works.

---

## 9) Anomaly Triage

- Open **Anomaly Triage Board**.

Expected:
- Anomaly table renders.
- Severity counts match chart.
- Download CSV works.

---

## 10) Post-Demo Checks (Optional)

- Confirm logs updated:
  - `logs/jira_integration.log`
  - `logs/jira_oauth.log`
  - `logs/nlp_audit.log`

---

## Common Issues & Fixes

- **Dashboard error: forecasting/anomaly failed** → restart Streamlit; ensure models exist.
- **Jira 401/410** → re-authorize Jira; token expired.
- **No SHAP output** → run `python src/xai/shap_explainer.py`.
- **Missing ROC/CM images** → run `python src/training/generate_paper_plots.py`.
