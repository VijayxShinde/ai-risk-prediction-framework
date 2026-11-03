"""What-If simulation backend for Phase 2-D."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import shap


RISK_MAP = {0: "Low", 1: "Medium", 2: "High"}


@dataclass
class ScenarioPrediction:
    """Prediction payload for a single scenario."""

    risk_label: str
    confidence_pct: float
    probabilities: list[float]
    top_drivers: list[str]
    processed_features: pd.DataFrame


class WhatIfSimulator:
    """Apply scenario deltas and simulate risk impact using XGBoost."""

    def __init__(self, model, dataset: pd.DataFrame, daily_burn_rate: float = 500.0) -> None:
        self.model = model
        self.dataset = dataset
        self.daily_burn_rate = daily_burn_rate

    def apply_deltas(
        self,
        baseline_row: pd.Series,
        deltas: dict[str, Any],
    ) -> pd.Series:
        """Apply user deltas to a baseline ticket row.

        Rules:
        - Budget and timeline sliders are independent.
        - If only timeline is changed (budget unchanged), budget is auto-adjusted
          with additive burn-rate logic (+/- days * daily_burn_rate).
        - If both are changed, both explicit inputs are respected.
        - Team efficiency affects timeline only (inverse multiplier).
        """
        updated = baseline_row.copy(deep=True)

        # Ensure we check for missing/NaN values and set safe fallbacks in updated Series
        def clean_val(col, default):
            val = updated.get(col)
            if pd.isna(val) or val is None or val == "":
                updated[col] = default
                return default
            return val

        # Set default fallbacks in updated if missing/NaN
        clean_val("Estimated_Days", 3.0)
        clean_val("Budget_Allocated", 1500.0)
        clean_val("Story_Points", 3.0)
        clean_val("Priority", "Medium")
        clean_val("Assignee_Seniority", "Mid")
        clean_val("Issue_Type", "Task")

        baseline_days = float(updated["Estimated_Days"])
        baseline_budget = float(updated["Budget_Allocated"])

        timeline_extension = float(deltas.get("timeline_extension_days", 0.0))
        budget_multiplier = float(deltas.get("budget_multiplier", 1.0))
        team_efficiency = float(deltas.get("team_efficiency", 1.0))

        budget_changed = bool(deltas.get("budget_changed", False))
        timeline_changed = bool(deltas.get("timeline_changed", False))

        # 1) Timeline slider (explicit)
        new_days = baseline_days + timeline_extension

        # 2) Team efficiency (timeline-only impact, inverse multiplier)
        # Example: 0.8 efficiency -> takes 1/0.8 = 1.25x time
        if team_efficiency <= 0:
            team_efficiency = 1.0
        new_days = new_days / team_efficiency
        new_days = max(1.0, round(new_days, 2))
        updated["Estimated_Days"] = new_days

        # 3) Budget slider behavior
        if budget_changed:
            # Explicit user choice wins
            updated_budget = baseline_budget * budget_multiplier
        elif timeline_changed:
            # Auto budget only for timeline-only change
            updated_budget = baseline_budget + (timeline_extension * self.daily_burn_rate)
        else:
            updated_budget = baseline_budget

        updated["Budget_Allocated"] = max(0.0, updated_budget)

        # Optional direct numeric tuning for scope
        if "story_points_delta" in deltas:
            base_points = float(updated.get("Story_Points", 0.0))
            updated["Story_Points"] = max(1.0, round(base_points + float(deltas["story_points_delta"]), 2))

        # Optional categorical overrides
        if deltas.get("priority_override"):
            updated["Priority"] = str(deltas["priority_override"])
        if deltas.get("seniority_override"):
            updated["Assignee_Seniority"] = str(deltas["seniority_override"])
        if deltas.get("issue_type_override"):
            updated["Issue_Type"] = str(deltas["issue_type_override"])

        return updated

    def predict_row(self, row: pd.Series, top_n: int = 5) -> ScenarioPrediction:
        """Predict risk payload for a ticket row."""
        processed = self._preprocess_for_model(row)

        prediction = int(self.model.predict(processed)[0])
        probabilities = self.model.predict_proba(processed)[0]
        confidence = float(probabilities[prediction] * 100)

        top_drivers = self._extract_top_driver_names(processed, top_n=top_n)

        return ScenarioPrediction(
            risk_label=RISK_MAP.get(prediction, str(prediction)),
            confidence_pct=confidence,
            probabilities=[float(x) for x in probabilities.tolist()],
            top_drivers=top_drivers,
            processed_features=processed,
        )

    def compare_scenarios(
        self,
        baseline_row: pd.Series,
        simulated_row: pd.Series,
    ) -> dict[str, Any]:
        """Return side-by-side scenario comparison payload."""
        original = self.predict_row(baseline_row)
        simulated = self.predict_row(simulated_row)

        original_high = original.probabilities[2] if len(original.probabilities) > 2 else 0.0
        simulated_high = simulated.probabilities[2] if len(simulated.probabilities) > 2 else 0.0

        baseline_budget = float(baseline_row.get("Budget_Allocated", 0.0))
        simulated_budget = float(simulated_row.get("Budget_Allocated", 0.0))
        baseline_days = float(baseline_row.get("Estimated_Days", 0.0))
        simulated_days = float(simulated_row.get("Estimated_Days", 0.0))

        return {
            "original": {
                "risk_label": original.risk_label,
                "confidence_pct": original.confidence_pct,
                "high_risk_pct": original_high * 100,
                "top_drivers": original.top_drivers,
            },
            "simulated": {
                "risk_label": simulated.risk_label,
                "confidence_pct": simulated.confidence_pct,
                "high_risk_pct": simulated_high * 100,
                "top_drivers": simulated.top_drivers,
            },
            "delta": {
                "high_risk_pct_change": (simulated_high - original_high) * 100,
                "confidence_pct_change": simulated.confidence_pct - original.confidence_pct,
                "budget_delta": simulated_budget - baseline_budget,
                "timeline_delta": simulated_days - baseline_days,
                "new_drivers": [d for d in simulated.top_drivers if d not in original.top_drivers],
                "mitigated_drivers": [d for d in original.top_drivers if d not in simulated.top_drivers],
            },
            "artifacts": {
                "original_features": original.processed_features,
                "simulated_features": simulated.processed_features,
            },
        }

    def _preprocess_for_model(self, row: pd.Series) -> pd.DataFrame:
        from src.preprocessing.feature_alignment import preprocess_row

        target_free = row.drop(labels=["Risk_Level"], errors="ignore")
        return preprocess_row(target_free, self.dataset)

    def _extract_top_driver_names(self, processed_features: pd.DataFrame, top_n: int = 5) -> list[str]:
        """Extract top SHAP features targeting High-risk class when available."""
        explainer = shap.TreeExplainer(self.model)
        shap_values = explainer.shap_values(processed_features)

        if isinstance(shap_values, list):
            shap_array = np.array(shap_values)
            if shap_array.ndim == 3:
                target_class = min(2, shap_array.shape[0] - 1)
                shap_abs = np.abs(shap_array[target_class]).flatten()
            else:
                shap_abs = np.abs(shap_array).flatten()
        else:
            shap_array = np.array(shap_values)
            if shap_array.ndim == 3:
                target_class = min(2, shap_array.shape[-1] - 1)
                shap_abs = np.abs(shap_array[0, :, target_class]).flatten()
            elif shap_array.ndim == 2:
                shap_abs = np.abs(shap_array[0]).flatten()
            else:
                shap_abs = np.abs(shap_array).flatten()

        names = list(processed_features.columns)
        ranked = sorted(zip(names, shap_abs), key=lambda item: item[1], reverse=True)
        return [name.replace("_", " ").title() for name, _ in ranked[:top_n]]
