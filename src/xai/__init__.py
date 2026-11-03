"""
XAI Module - Explainable AI for Model Interpretability
SHAP-based model explanations and feature importance analysis.
"""

from .shap_explainer import (
    preprocess_for_shap,
    patch_booster_base_score,
    run_shap_analysis,
)

__all__ = [
    "preprocess_for_shap",
    "patch_booster_base_score",
    "run_shap_analysis",
]
