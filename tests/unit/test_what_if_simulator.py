"""Unit tests for WhatIfSimulator (Phase 2-D).

Modernized test suite using pd.Series inputs and nested comparison payloads.
Tests mathematical guardrails for timeline, budget, and team efficiency logic.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.simulation.what_if_simulator import WhatIfSimulator


pytestmark = pytest.mark.unit


@pytest.fixture
def mock_model():
    """Create mock XGBoost model."""
    model = MagicMock()
    model.predict.side_effect = [np.array([2]), np.array([1])]
    model.predict_proba.side_effect = [
        np.array([[0.10, 0.30, 0.60]]),
        np.array([[0.20, 0.50, 0.30]]),
    ]
    return model


@pytest.fixture
def sample_dataset():
    """Create minimal training dataset for preprocessing."""
    return pd.DataFrame(
        {
            "Priority": ["High", "Medium", "Low"],
            "Issue_Type": ["Bug", "Task", "Epic"],
            "Assignee_Seniority": ["Junior", "Mid", "Senior"],
            "Story_Points": [5, 8, 13],
            "Estimated_Days": [10, 15, 20],
            "Budget_Allocated": [5000, 7500, 10000],
            "Risk_Level": ["High", "Medium", "Low"],
        }
    )


@pytest.fixture
def sample_ticket():
    """Create sample ticket row (pd.Series)."""
    return pd.Series(
        {
            "Priority": "High",
            "Issue_Type": "Bug",
            "Assignee_Seniority": "Junior",
            "Story_Points": 8,
            "Estimated_Days": 10,
            "Budget_Allocated": 5000,
            "Risk_Level": "High",
        }
    )


@pytest.fixture
def simulator(mock_model, sample_dataset):
    """Create WhatIfSimulator instance."""
    return WhatIfSimulator(model=mock_model, dataset=sample_dataset, daily_burn_rate=500.0)


class TestApplyDeltasTimeline:
    """Test timeline extension logic."""

    def test_apply_deltas_timeline_extension_positive(self, simulator, sample_ticket):
        deltas = {
            "timeline_extension_days": 5.0,
            "budget_multiplier": 1.0,
            "team_efficiency": 1.0,
            "timeline_changed": True,
            "budget_changed": False,
        }
        result = simulator.apply_deltas(sample_ticket, deltas)

        baseline_days = float(sample_ticket["Estimated_Days"])
        expected_days = baseline_days + 5.0
        assert float(result["Estimated_Days"]) == pytest.approx(expected_days)

    def test_apply_deltas_timeline_extension_negative(self, simulator, sample_ticket):
        deltas = {
            "timeline_extension_days": -3.0,
            "budget_multiplier": 1.0,
            "team_efficiency": 1.0,
            "timeline_changed": True,
            "budget_changed": False,
        }
        result = simulator.apply_deltas(sample_ticket, deltas)

        baseline_days = float(sample_ticket["Estimated_Days"])
        expected_days = baseline_days - 3.0
        assert float(result["Estimated_Days"]) == pytest.approx(expected_days)

    def test_apply_deltas_timeline_minimum_floor_one_day(self, simulator, sample_ticket):
        sample_ticket["Estimated_Days"] = 2
        deltas = {
            "timeline_extension_days": -5.0,
            "budget_multiplier": 1.0,
            "team_efficiency": 1.0,
            "timeline_changed": True,
            "budget_changed": False,
        }
        result = simulator.apply_deltas(sample_ticket, deltas)

        assert float(result["Estimated_Days"]) >= 1.0


class TestApplyDeltasBudget:
    """Test budget logic (independent vs. auto-derived)."""

    def test_apply_deltas_budget_timeline_only_auto_derives(self, simulator, sample_ticket):
        baseline_budget = float(sample_ticket["Budget_Allocated"])
        deltas = {
            "timeline_extension_days": 2.0,
            "budget_multiplier": 1.0,
            "team_efficiency": 1.0,
            "timeline_changed": True,
            "budget_changed": False,
        }
        result = simulator.apply_deltas(sample_ticket, deltas)

        expected_budget = baseline_budget + (2.0 * 500.0)
        assert float(result["Budget_Allocated"]) == pytest.approx(expected_budget)

    def test_apply_deltas_budget_explicit_override_wins(self, simulator, sample_ticket):
        baseline_budget = float(sample_ticket["Budget_Allocated"])
        deltas = {
            "timeline_extension_days": 2.0,
            "budget_multiplier": 1.5,
            "team_efficiency": 1.0,
            "timeline_changed": True,
            "budget_changed": True,
        }
        result = simulator.apply_deltas(sample_ticket, deltas)

        expected_budget = baseline_budget * 1.5
        assert float(result["Budget_Allocated"]) == pytest.approx(expected_budget)

    def test_apply_deltas_budget_multiplier_scales_independently(self, simulator, sample_ticket):
        baseline_budget = float(sample_ticket["Budget_Allocated"])
        deltas = {
            "timeline_extension_days": 0.0,
            "budget_multiplier": 1.2,
            "team_efficiency": 1.0,
            "timeline_changed": False,
            "budget_changed": True,
        }
        result = simulator.apply_deltas(sample_ticket, deltas)

        expected_budget = baseline_budget * 1.2
        assert float(result["Budget_Allocated"]) == pytest.approx(expected_budget)

    def test_apply_deltas_budget_never_negative(self, simulator, sample_ticket):
        deltas = {
            "timeline_extension_days": 0.0,
            "budget_multiplier": 0.0,
            "team_efficiency": 1.0,
            "timeline_changed": False,
            "budget_changed": True,
        }
        result = simulator.apply_deltas(sample_ticket, deltas)

        assert float(result["Budget_Allocated"]) >= 0.0


class TestApplyDeltasEfficiency:
    """Test team efficiency (timeline-only impact, inverse multiplier)."""

    def test_apply_deltas_efficiency_inverse_multiplier_slowing(self, simulator, sample_ticket):
        baseline_days = float(sample_ticket["Estimated_Days"])
        deltas = {
            "timeline_extension_days": 0.0,
            "budget_multiplier": 1.0,
            "team_efficiency": 0.8,
            "timeline_changed": False,
            "budget_changed": False,
        }
        result = simulator.apply_deltas(sample_ticket, deltas)

        expected_days = baseline_days / 0.8
        assert float(result["Estimated_Days"]) == pytest.approx(expected_days)

    def test_apply_deltas_efficiency_inverse_multiplier_speeding(self, simulator, sample_ticket):
        baseline_days = float(sample_ticket["Estimated_Days"])
        deltas = {
            "timeline_extension_days": 0.0,
            "budget_multiplier": 1.0,
            "team_efficiency": 1.25,
            "timeline_changed": False,
            "budget_changed": False,
        }
        result = simulator.apply_deltas(sample_ticket, deltas)

        expected_days = baseline_days / 1.25
        assert float(result["Estimated_Days"]) == pytest.approx(expected_days)

    def test_apply_deltas_efficiency_combined_with_timeline(self, simulator, sample_ticket):
        baseline_days = float(sample_ticket["Estimated_Days"])
        deltas = {
            "timeline_extension_days": 2.0,
            "budget_multiplier": 1.0,
            "team_efficiency": 0.8,
            "timeline_changed": True,
            "budget_changed": False,
        }
        result = simulator.apply_deltas(sample_ticket, deltas)

        expected_days = (baseline_days + 2.0) / 0.8
        assert float(result["Estimated_Days"]) == pytest.approx(expected_days)

    def test_apply_deltas_efficiency_floor_at_1_0(self, simulator, sample_ticket):
        baseline_days = float(sample_ticket["Estimated_Days"])
        deltas = {
            "timeline_extension_days": 0.0,
            "budget_multiplier": 1.0,
            "team_efficiency": 0.0,
            "timeline_changed": False,
            "budget_changed": False,
        }
        result = simulator.apply_deltas(sample_ticket, deltas)

        assert float(result["Estimated_Days"]) == pytest.approx(baseline_days)


class TestApplyDeltasCategoricalOverrides:
    """Test optional categorical overrides."""

    def test_apply_deltas_priority_override(self, simulator, sample_ticket):
        deltas = {
            "timeline_extension_days": 0.0,
            "budget_multiplier": 1.0,
            "team_efficiency": 1.0,
            "timeline_changed": False,
            "budget_changed": False,
            "priority_override": "Low",
        }
        result = simulator.apply_deltas(sample_ticket, deltas)

        assert result["Priority"] == "Low"

    def test_apply_deltas_seniority_override(self, simulator, sample_ticket):
        deltas = {
            "timeline_extension_days": 0.0,
            "budget_multiplier": 1.0,
            "team_efficiency": 1.0,
            "timeline_changed": False,
            "budget_changed": False,
            "seniority_override": "Senior",
        }
        result = simulator.apply_deltas(sample_ticket, deltas)

        assert result["Assignee_Seniority"] == "Senior"

    def test_apply_deltas_issue_type_override(self, simulator, sample_ticket):
        deltas = {
            "timeline_extension_days": 0.0,
            "budget_multiplier": 1.0,
            "team_efficiency": 1.0,
            "timeline_changed": False,
            "budget_changed": False,
            "issue_type_override": "Epic",
        }
        result = simulator.apply_deltas(sample_ticket, deltas)

        assert result["Issue_Type"] == "Epic"

    def test_apply_deltas_no_override_preserves_original(self, simulator, sample_ticket):
        deltas = {
            "timeline_extension_days": 0.0,
            "budget_multiplier": 1.0,
            "team_efficiency": 1.0,
            "timeline_changed": False,
            "budget_changed": False,
            "priority_override": None,
            "seniority_override": None,
            "issue_type_override": None,
        }
        result = simulator.apply_deltas(sample_ticket, deltas)

        assert result["Priority"] == sample_ticket["Priority"]
        assert result["Assignee_Seniority"] == sample_ticket["Assignee_Seniority"]
        assert result["Issue_Type"] == sample_ticket["Issue_Type"]


class TestApplyDeltasStoryPoints:
    """Test optional story points adjustment."""

    def test_apply_deltas_story_points_delta(self, simulator, sample_ticket):
        baseline_points = float(sample_ticket["Story_Points"])
        deltas = {
            "timeline_extension_days": 0.0,
            "budget_multiplier": 1.0,
            "team_efficiency": 1.0,
            "timeline_changed": False,
            "budget_changed": False,
            "story_points_delta": 5.0,
        }
        result = simulator.apply_deltas(sample_ticket, deltas)

        expected_points = baseline_points + 5.0
        assert float(result["Story_Points"]) == pytest.approx(expected_points)

    def test_apply_deltas_story_points_floor_one(self, simulator, sample_ticket):
        sample_ticket["Story_Points"] = 2
        deltas = {
            "timeline_extension_days": 0.0,
            "budget_multiplier": 1.0,
            "team_efficiency": 1.0,
            "timeline_changed": False,
            "budget_changed": False,
            "story_points_delta": -5.0,
        }
        result = simulator.apply_deltas(sample_ticket, deltas)

        assert float(result["Story_Points"]) >= 1.0


class TestCompareScenarios:
    """Test scenario comparison payload generation."""

    @patch("src.simulation.what_if_simulator.shap.TreeExplainer")
    @patch("src.simulation.what_if_simulator.WhatIfSimulator._preprocess_for_model")
    def test_compare_scenarios_returns_expected_schema(
        self,
        mock_preprocess,
        mock_explainer_class,
        simulator,
        sample_ticket,
    ):
        processed_df = pd.DataFrame(
            {
                "Estimated_Days": [10.0],
                "Budget_Allocated": [5000.0],
                "Story_Points": [8.0],
            }
        )
        mock_preprocess.return_value = processed_df

        mock_explainer = MagicMock()
        mock_explainer.shap_values.return_value = np.array(
            [[[0.01, 0.02, 0.03], [0.11, 0.12, 0.13], [0.21, 0.22, 0.23]]],
            dtype=float,
        )
        mock_explainer_class.return_value = mock_explainer

        deltas = {
            "timeline_extension_days": 2.0,
            "budget_multiplier": 1.0,
            "team_efficiency": 1.0,
            "timeline_changed": True,
            "budget_changed": False,
        }
        simulated_ticket = simulator.apply_deltas(sample_ticket, deltas)
        comparison = simulator.compare_scenarios(sample_ticket, simulated_ticket)

        assert set(comparison.keys()) == {"original", "simulated", "delta", "artifacts"}
        assert set(comparison["original"].keys()) == {
            "risk_label",
            "confidence_pct",
            "high_risk_pct",
            "top_drivers",
        }
        assert set(comparison["simulated"].keys()) == {
            "risk_label",
            "confidence_pct",
            "high_risk_pct",
            "top_drivers",
        }
        assert set(comparison["delta"].keys()) == {
            "high_risk_pct_change",
            "confidence_pct_change",
            "budget_delta",
            "timeline_delta",
            "new_drivers",
            "mitigated_drivers",
        }
        assert set(comparison["artifacts"].keys()) == {"original_features", "simulated_features"}

    @patch("src.simulation.what_if_simulator.shap.TreeExplainer")
    @patch("src.simulation.what_if_simulator.WhatIfSimulator._preprocess_for_model")
    def test_compare_scenarios_risk_label_difference(
        self,
        mock_preprocess,
        mock_explainer_class,
        simulator,
        sample_ticket,
    ):
        processed_df = pd.DataFrame(
            {
                "Estimated_Days": [10.0],
                "Budget_Allocated": [5000.0],
                "Story_Points": [8.0],
            }
        )
        mock_preprocess.return_value = processed_df

        mock_explainer = MagicMock()
        mock_explainer.shap_values.return_value = np.array(
            [[[0.01, 0.02, 0.03], [0.11, 0.12, 0.13], [0.21, 0.22, 0.23]]],
            dtype=float,
        )
        mock_explainer_class.return_value = mock_explainer

        deltas = {
            "timeline_extension_days": 0.0,
            "budget_multiplier": 0.5,
            "team_efficiency": 1.0,
            "timeline_changed": False,
            "budget_changed": True,
        }
        simulated_ticket = simulator.apply_deltas(sample_ticket, deltas)
        comparison = simulator.compare_scenarios(sample_ticket, simulated_ticket)

        assert comparison["original"]["risk_label"] == "High"
        assert comparison["simulated"]["risk_label"] == "Medium"

    @patch("src.simulation.what_if_simulator.shap.TreeExplainer")
    @patch("src.simulation.what_if_simulator.WhatIfSimulator._preprocess_for_model")
    def test_compare_scenarios_budget_delta_calculation(
        self,
        mock_preprocess,
        mock_explainer_class,
        simulator,
        sample_ticket,
    ):
        processed_df = pd.DataFrame(
            {
                "Estimated_Days": [10.0],
                "Budget_Allocated": [5000.0],
                "Story_Points": [8.0],
            }
        )
        mock_preprocess.return_value = processed_df

        mock_explainer = MagicMock()
        mock_explainer.shap_values.return_value = np.array(
            [[[0.01, 0.02, 0.03], [0.11, 0.12, 0.13], [0.21, 0.22, 0.23]]],
            dtype=float,
        )
        mock_explainer_class.return_value = mock_explainer

        deltas = {
            "timeline_extension_days": 2.0,
            "budget_multiplier": 1.0,
            "team_efficiency": 1.0,
            "timeline_changed": True,
            "budget_changed": False,
        }
        simulated_ticket = simulator.apply_deltas(sample_ticket, deltas)
        comparison = simulator.compare_scenarios(sample_ticket, simulated_ticket)

        baseline_budget = float(sample_ticket["Budget_Allocated"])
        expected_delta = (baseline_budget + 1000.0) - baseline_budget
        assert comparison["delta"]["budget_delta"] == pytest.approx(expected_delta)

    @patch("src.simulation.what_if_simulator.shap.TreeExplainer")
    @patch("src.simulation.what_if_simulator.WhatIfSimulator._preprocess_for_model")
    def test_compare_scenarios_timeline_delta_calculation(
        self,
        mock_preprocess,
        mock_explainer_class,
        simulator,
        sample_ticket,
    ):
        processed_df = pd.DataFrame(
            {
                "Estimated_Days": [10.0],
                "Budget_Allocated": [5000.0],
                "Story_Points": [8.0],
            }
        )
        mock_preprocess.return_value = processed_df

        mock_explainer = MagicMock()
        mock_explainer.shap_values.return_value = np.array(
            [[[0.01, 0.02, 0.03], [0.11, 0.12, 0.13], [0.21, 0.22, 0.23]]],
            dtype=float,
        )
        mock_explainer_class.return_value = mock_explainer

        deltas = {
            "timeline_extension_days": 3.0,
            "budget_multiplier": 1.0,
            "team_efficiency": 1.0,
            "timeline_changed": True,
            "budget_changed": False,
        }
        simulated_ticket = simulator.apply_deltas(sample_ticket, deltas)
        comparison = simulator.compare_scenarios(sample_ticket, simulated_ticket)

        assert comparison["delta"]["timeline_delta"] == pytest.approx(3.0)


class TestIntegrationEndToEnd:
    """Integration tests for full workflow."""

    @patch("src.simulation.what_if_simulator.shap.TreeExplainer")
    @patch("src.simulation.what_if_simulator.WhatIfSimulator._preprocess_for_model")
    def test_end_to_end_realistic_scenario(
        self,
        mock_preprocess,
        mock_explainer_class,
        simulator,
        sample_ticket,
    ):
        processed_df = pd.DataFrame(
            {
                "Estimated_Days": [10.0],
                "Budget_Allocated": [5000.0],
                "Story_Points": [8.0],
            }
        )
        mock_preprocess.return_value = processed_df

        mock_explainer = MagicMock()
        mock_explainer.shap_values.return_value = np.array(
            [[[0.01, 0.02, 0.03], [0.11, 0.12, 0.13], [0.21, 0.22, 0.23]]],
            dtype=float,
        )
        mock_explainer_class.return_value = mock_explainer

        deltas = {
            "timeline_extension_days": 3.0,
            "budget_multiplier": 1.0,
            "team_efficiency": 1.1,
            "timeline_changed": True,
            "budget_changed": False,
            "priority_override": None,
            "seniority_override": "Senior",
        }

        simulated = simulator.apply_deltas(sample_ticket, deltas)
        comparison = simulator.compare_scenarios(sample_ticket, simulated)

        baseline_days = float(sample_ticket["Estimated_Days"])
        expected_days = round((baseline_days + 3.0) / 1.1, 2)
        assert float(simulated["Estimated_Days"]) == pytest.approx(expected_days)
        assert simulated["Assignee_Seniority"] == "Senior"
        assert comparison["delta"]["timeline_delta"] > 0
        assert isinstance(comparison["original"]["top_drivers"], list)
        assert isinstance(comparison["simulated"]["top_drivers"], list)
