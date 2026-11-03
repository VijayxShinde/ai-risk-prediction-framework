import json
import os
from typing import Any, Dict, List
import pytest
from src.nlp import RiskNLPEngine


@pytest.fixture(scope="session")
def engine() -> RiskNLPEngine:
    return RiskNLPEngine()


@pytest.fixture()
def sample_workflow_data() -> List[Dict[str, Any]]:
    return [
        {
            "id": "TEST-1",
            "comments": [
                "We are blocked on API integration and cannot proceed until next week.",
                "This depends on backend team delivery; waiting for their sign-off.",
                "Resource bandwidth is limited; team is at capacity this sprint.",
                "Deadline is by end of Friday; target date is next Monday.",
                "Everything is on track and moving smoothly.",
            ],
        }
    ]


def test_end_to_end_workflow(
    engine: RiskNLPEngine, sample_workflow_data: List[Dict[str, Any]]
):
    """Test the complete end-to-end workflow with sample data"""
    # Test data setup
    ticket_data = sample_workflow_data[0]
    comments = ticket_data["comments"]

    # Run the full workflow analysis
    result = engine.analyze_text_batch(
        text_list=comments, ticket_id=ticket_data["id"], return_aggregated=True
    )

    # Verify the results
    assert result is not None
    assert 0.0 < float(result["avg_risk_score"]) < 1.0
    assert result["ticket_id"] == ticket_data["id"]
    assert result["comment_count"] == len(comments)
    assert "comment_results" in result
    assert "risk_count" in result
    assert "dominant_risk_category" in result
