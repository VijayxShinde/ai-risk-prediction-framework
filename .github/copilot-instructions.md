# Copilot Instructions for ai-risk-prediction-framework

## Build, Test, and Lint Commands

- **Install dependencies:**
  - `pip install -r requirements.txt`
  - For development: `pip install -e .[dev]`
- **Run all tests:**
  - `pytest` (runs both unit and integration tests)
- **Run a single test:**
  - `pytest tests/unit/test_nlp_risk_engine.py::test_engine_initialization`
- **Linting:**
  - `flake8 src/`
  - `black --check src/`
  - `mypy src/`
- **Format code:**
  - `black src/`
- **Test config:** See `pytest.ini` and `[tool.pytest.ini_options]` in `pyproject.toml` for markers and options.

## High-Level Architecture

- **src/**: Core logic modules
  - `anomaly/`: Isolation Forest anomaly detection
  - `forecasting/`: Prophet-based time-series forecasting
  - `nlp/`: NLP risk detection (NER, sentiment, aggregation)
  - `mitigation/`: LLM-based mitigation strategy generator (NVIDIA Qwen 3.5 integration)
  - `xai/`: SHAP explainability and feature importance
  - `preprocessing/`: Data pipeline, leakage prevention, feature engineering
  - `integrations/`: Jira API client, config
- **app/**: Streamlit UI
  - `main.py`: Entry point, sets up session state, routing, and custom styles
  - `views/`, `components/`, `pages/`: Modular UI pages (dashboard, forecasting, anomaly, auditor, login, settings)
  - `utils/`: Sidebar, routing, and style helpers
- **tests/**: Unit and integration tests (see `pytest.ini` for structure)
- **models/**, **data/**, **logs/**, **reports/**: Artifacts, datasets, logs, and generated figures

## Key Conventions

- **ML Pipeline:** Strict flow: load → sample → inject metadata → compute features → drop leakage columns → encode categoricals → train/test split → train with class weights.
- **Target Leakage Prevention:** Always drop columns: `Actual_Days`, `Cost_Consumed`, `Summary`, `Description`, `Developer_Comments`, `Issue_ID`, `Issue_key` before training. Drop categoricals with >15 unique values.
- **Streamlit UI:**
  - Always call `st.set_page_config()` first in `main.py` and page modules.
  - Use custom styles and initialize `st.session_state` for authentication.
  - Route via sidebar; cache GenAI results in `st.session_state`.
- **GenAI Integration:** NVIDIA Qwen 3.5 API uses exponential backoff/retry. High-risk predictions are routed to LLM auditor for mitigation.
- **Testing:**
  - Unit tests: `tests/unit/`
  - Integration tests: `tests/integration/`
  - Use pytest markers: `unit`, `integration`, `slow`, `benchmark`
- **Config:**
  - Python 3.10+ recommended
  - Dependencies managed via `requirements.txt` and `pyproject.toml`
  - Dev tools: `pytest`, `pytest-cov`, `black`, `flake8`, `mypy`

---

This file summarizes build/test commands, architecture, and key conventions for Copilot and future contributors. Would you like to adjust anything or add coverage for additional areas (e.g., deployment, CI/CD, or API usage)?
