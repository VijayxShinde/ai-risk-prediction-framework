"""
Time-Series Forecasting Module
AI-Driven Risk Prediction Framework - Phase 2

Prophet-based forecasting engine for project risk metrics.
"""

from .forecast import (
    ProjectForecaster,
    InsufficientDataError,
    ProphetFittingError,
    InvalidMetricColumnError,
)

__all__ = [
    "ProjectForecaster",
    "InsufficientDataError",
    "ProphetFittingError",
    "InvalidMetricColumnError",
]

__version__ = "2.0.0"
