# Import Guide - AI-Driven Risk Prediction Framework

## Quick Start

The most common way to import classes from the framework:

```python
from src import RiskNLPEngine, AnomalyEngine, ProjectForecaster
```

## Main Package Imports

The main `src/__init__.py` exports the most commonly used classes for convenient access.

### Recommended Imports

```python
# Core Models
from src import RiskNLPEngine, AnomalyEngine

# Forecasting
from src import ProjectForecaster
```

## Module-Specific Imports

Import directly from specific modules for more fine-grained control:

### Models Module (`src.models`)

```python
from src.models import RiskNLPEngine, AnomalyEngine

# Or directly
from src.models.nlp_risk_engine import RiskNLPEngine
from src.models.anomaly_detector import AnomalyEngine
from src.models.risk_classifier import RiskClassifier
```

### Forecasting Module (`src.forecasting`)

```python
from src.forecasting import ProjectForecaster, InsufficientDataError

# Or directly
from src.forecasting.forecast import ProjectForecaster
```

### NLP Module (`src.nlp`)

```python
from src.nlp import RiskTextDetector

# Or directly
from src.nlp.text_risk_detector import RiskTextDetector
```

### Preprocessing Module (`src.preprocessing`)

```python
from src.preprocessing import DataPipeline, preprocess_data

# Or directly
from src.preprocessing.data_pipeline import DataPipeline
from src.preprocessing.preprocess import preprocess_data
```

### XAI Module (`src.xai`)

```python
from src.xai import SHAPExplainer

# Or directly
from src.xai.shap_explainer import SHAPExplainer
```

### Mitigation Module (`src.mitigation`)

```python
from src.mitigation import MitigationAgent

# Or directly
from src.mitigation.llm_agent import MitigationAgent
```

## Example Usage

### Complete Workflow Example

```python
from src import RiskNLPEngine, AnomalyEngine
from src.preprocessing import DataPipeline
from src.xai import SHAPExplainer

# Initialize components
nlp_engine = RiskNLPEngine()
anomaly_engine = AnomalyEngine()
shap_explainer = SHAPExplainer()

# Analyze text
result = nlp_engine.analyze_text("We are blocked on API integration")

# Detect anomalies
anomalies = anomaly_engine.detect(data)

# Explain predictions
explanations = shap_explainer.explain(model, data)
```

## Testing Imports

In test files, use the same import patterns:

```python
import pytest
from src import RiskNLPEngine
from src.preprocessing import DataPipeline

@pytest.fixture()
def nlp_engine():
    return RiskNLPEngine()

def test_something(nlp_engine):
    result = nlp_engine.analyze_text("sample text")
    assert result is not None
```

## Phase 2 (Future) Imports

Placeholder modules are prepared for Phase 2 features:

```python
# Phase 2-B: Anomaly Detection (coming soon)
from src.anomaly import AnomalyDetector

# Phase 2-D: What-If Simulation (coming soon)
from src.simulation import WhatIfEngine

# Phase 2-E/F: Integrations (coming soon)
from src.integrations import JiraClient, OAuthProvider
```

## Troubleshooting

### ImportError: Cannot import name 'X' from 'src'

Make sure:
1. The module is installed: `pip install -e .`
2. You're using the correct import path
3. The class is exported in the module's `__init__.py`

### ModuleNotFoundError: No module named 'src'

Make sure:
1. You're running from the project root directory
2. The project is installed in development mode: `pip install -e .`
3. Your PYTHONPATH includes the project root

### Best Practices

1. **Use main package imports when possible** - They're simpler and more maintainable
2. **Import only what you need** - Reduces namespace pollution
3. **Avoid circular imports** - The module structure is designed to prevent these
4. **Run tests to verify imports** - Tests validate the import structure

## Configuration

For environment-specific configuration:

```python
from src.config import get_config

config = get_config()
# Access config settings
```

## Migration from Old Import Style

Old (with sys.path hacks):
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.models.nlp_risk_engine import RiskNLPEngine
```

New (clean and simple):
```python
from src import RiskNLPEngine
# or
from src.models import RiskNLPEngine
```

## Additional Resources

- See `docs/ARCHITECTURE.md` for system design details
- Check `src/` module docstrings for detailed API documentation
- Review test files in `tests/` for usage examples
