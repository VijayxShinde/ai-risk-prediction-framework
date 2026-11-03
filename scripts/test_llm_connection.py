"""Standalone LLM connectivity test for mitigation agent."""

from __future__ import annotations

from src.mitigation.llm_agent import generate_mitigation_strategy


def main() -> None:
    dummy_ticket = {
        "summary": "Implement payment gateway integration for checkout module",
        "priority": "High",
        "assignee_seniority": "Junior",
        "estimated_days": 14,
        "story_points": 21,
        "budget_allocated": 15000,
    }
    dummy_risk = "High"
    dummy_factors = [
        "Assignee_Seniority=Junior",
        "Story_Points=21",
        "Estimated_Days=14",
    ]

    print("=" * 60)
    print("QWEN 3.5 MITIGATION AGENT - TEST EXECUTION")
    print("=" * 60)

    result = generate_mitigation_strategy(
        ticket_details=dummy_ticket,
        risk_level=dummy_risk,
        top_risk_factors=dummy_factors,
    )

    print("\n[IEEE AUDIT TRACE - Reasoning]")
    print("-" * 60)
    print(
        result["reasoning_trace"]
        if result["reasoning_trace"]
        else "(No reasoning trace captured)"
    )
    print("-" * 60)

    print("\n[FINAL MITIGATION STRATEGY]")
    print("-" * 60)
    print(
        result["final_strategy"]
        if result["final_strategy"]
        else "(No strategy generated)"
    )
    print("-" * 60)

    print("\n" + "=" * 60)
    print("EXECUTION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
