import json
import os
import re
import time
from typing import Any, Dict, List

import pytest

from src.nlp import RiskNLPEngine


pytestmark = [
    pytest.mark.filterwarnings(
        "ignore:.*cache-system uses symlinks by default.*:UserWarning"
    ),
    pytest.mark.filterwarnings(
        "ignore:Deprecated in 0.9.0:DeprecationWarning"
    ),
]


REQUIRED_PER_COMMENT_KEYS = {
    "text",
    "risk_score",
    "risk_level",
    "is_risk",
    "sentiment",
    "entities",
    "risk_category",
    "risk_phrases",
    "processing_time_ms",
}


@pytest.fixture(scope="session")
def engine() -> RiskNLPEngine:
    return RiskNLPEngine()


@pytest.fixture()
def sample_texts() -> List[str]:
    return [
        "We are blocked on API integration and cannot proceed until next week.",
        "This depends on backend team delivery; waiting for their sign-off.",
        "Resource bandwidth is limited; team is at capacity this sprint.",
        "Deadline is by end of Friday; target date is next Monday.",
        "Everything is on track and moving smoothly.",
        "ETA is unclear; due date may slip.",
        "Vendor dependency might delay the rollout.",
        "Stuck on build pipeline failures; blocked by infrastructure changes.",
        "Headcount shortage and unavailable engineers due to sick leave.",
        "No blockers, budget looks stable, and schedule variance is low.",
    ]


@pytest.fixture(scope="session")
def github_issues() -> List[Dict[str, Any]]:
    path = os.path.join("data", "github_issues_tensorflow.json")
    assert os.path.exists(path), f"Missing required dataset file: {path}"

    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)

    issues = obj.get("issues") if isinstance(obj, dict) else None
    assert isinstance(issues, list), "Dataset must be a dict with an 'issues' list"
    return issues


# A) INITIALIZATION TESTS

def test_engine_initialization(engine: RiskNLPEngine):
    assert engine.logger is not None
    assert hasattr(engine.logger, "handlers")

    # Log file should be created when engine writes; trigger a small batch.
    result = engine.analyze_text_batch(["blocked on API"], return_aggregated=False)
    assert isinstance(result, list)
    assert len(result) == 1


def test_fallback_loading(engine: RiskNLPEngine):
    # If torch is missing, transformer pipeline should fall back.
    if engine.sentiment_pipeline is None:
        assert engine.tokenizer is None

    # If spaCy model isn't installed, nlp can be None.
    assert hasattr(engine, "nlp")


# B) ENTITY EXTRACTION TESTS

def _get_entities(engine: RiskNLPEngine, text: str) -> List[Dict[str, Any]]:
    res = engine.analyze_text_batch([text], return_aggregated=False)[0]
    return res["entities"]


def test_deadline_entity_extraction(engine: RiskNLPEngine):
    entities = _get_entities(engine, "Must finish by end of Friday. Target date next week.")
    assert any(e["type"] == "DEADLINE" for e in entities)


def test_blocker_entity_extraction(engine: RiskNLPEngine):
    entities = _get_entities(engine, "We are blocked on API integration.")
    assert any(e["type"] == "BLOCKER" for e in entities)


def test_dependency_entity_extraction(engine: RiskNLPEngine):
    entities = _get_entities(engine, "This depends on backend delivery.")
    assert any(e["type"] == "DEPENDENCY" for e in entities)


def test_resource_entity_extraction(engine: RiskNLPEngine):
    entities = _get_entities(engine, "Bandwidth is low and capacity is limited.")
    assert any(e["type"] == "RESOURCE" for e in entities)


# C) SENTIMENT/RISK CLASSIFICATION TESTS

def test_negative_sentiment_detected(engine: RiskNLPEngine):
    # Even without transformer sentiment, keyword entities should trigger a risk on neutral.
    res = engine.analyze_text_batch(["critical bug blocking release"], return_aggregated=False)[0]
    assert res["is_risk"] is True


def test_neutral_with_entities(engine: RiskNLPEngine):
    res = engine.analyze_text_batch(["ETA is next week"], return_aggregated=False)[0]
    assert res["is_risk"] is True
    assert len(res["entities"]) >= 1


def test_positive_no_risk(engine: RiskNLPEngine):
    res = engine.analyze_text_batch(["everything on track"], return_aggregated=False)[0]
    assert res["is_risk"] is False


# D) CONFIDENCE THRESHOLDS TESTS

def test_high_confidence_bucket(engine: RiskNLPEngine):
    assert engine._score_to_level(0.85) == "HIGH"


def test_medium_confidence_bucket(engine: RiskNLPEngine):
    assert engine._score_to_level(0.84) == "MEDIUM"
    assert engine._score_to_level(0.65) == "MEDIUM"


def test_low_confidence_bucket(engine: RiskNLPEngine):
    assert engine._score_to_level(0.64) == "LOW"
    assert engine._score_to_level(0.50) == "LOW"


def test_uncertain_confidence_bucket(engine: RiskNLPEngine):
    assert engine._score_to_level(0.49) == "UNCERTAIN"


# E) RISK CATEGORIZATION TESTS

def test_schedule_category(engine: RiskNLPEngine):
    res = engine.analyze_text_batch(["deadline is Friday"], return_aggregated=False)[0]
    assert res["risk_category"] == "SCHEDULE"


def test_technical_category(engine: RiskNLPEngine):
    res = engine.analyze_text_batch(["blocked by architecture issue"], return_aggregated=False)[0]
    assert res["risk_category"] == "TECHNICAL"


def test_external_category(engine: RiskNLPEngine):
    res = engine.analyze_text_batch(["depends on vendor delivery"], return_aggregated=False)[0]
    assert res["risk_category"] == "EXTERNAL"


# F) BATCH PROCESSING TESTS

def test_batch_processing_multiple_comments(engine: RiskNLPEngine, sample_texts: List[str]):
    res = engine.analyze_text_batch(sample_texts[:5], return_aggregated=False)
    assert isinstance(res, list)
    assert len(res) == 5


def test_aggregation_per_comment(engine: RiskNLPEngine, sample_texts: List[str]):
    res = engine.analyze_text_batch(sample_texts[:3], return_aggregated=False)
    assert isinstance(res, list)
    assert all(isinstance(x, dict) for x in res)


def test_aggregation_ticket_level(engine: RiskNLPEngine, sample_texts: List[str]):
    res = engine.analyze_text_batch(sample_texts[:3], ticket_id="PROJ-123", return_aggregated=True)
    assert isinstance(res, dict)
    assert res.get("ticket_id") == "PROJ-123"
    assert res.get("comment_count") == 3


# G) OUTPUT SCHEMA VALIDATION

def test_per_comment_schema(engine: RiskNLPEngine, sample_texts: List[str]):
    res = engine.analyze_text_batch(sample_texts[:2], return_aggregated=False)
    for item in res:
        assert REQUIRED_PER_COMMENT_KEYS.issubset(item.keys())


def test_ticket_summary_schema(engine: RiskNLPEngine, sample_texts: List[str]):
    agg = engine.analyze_text_batch(sample_texts[:4], ticket_id="X", return_aggregated=True)
    required = {
        "ticket_id",
        "comment_count",
        "total_comments_analyzed",
        "risk_count",
        "avg_risk_score",
        "dominant_risk_category",
        "risk_distribution",
        "all_entities",
        "confidence_distribution",
        "total_processing_time_ms",
        "comment_results",
    }
    assert required.issubset(agg.keys())


def test_entity_schema(engine: RiskNLPEngine):
    res = engine.analyze_text_batch(["blocked on API and waiting for vendor"], return_aggregated=False)[0]
    for ent in res["entities"]:
        for key in ("text", "type", "confidence", "start_char", "end_char"):
            assert key in ent
        assert isinstance(ent["start_char"], int)
        assert isinstance(ent["end_char"], int)
        assert 0.0 <= float(ent["confidence"]) <= 1.0


# H) REAL DATA VALIDATION

def test_github_issues_dataset(engine: RiskNLPEngine, github_issues: List[Dict[str, Any]]):
    texts = [x.get("text", "") for x in github_issues[:50]]
    assert len(texts) == 50
    assert all(isinstance(t, str) for t in texts)

    res = engine.analyze_text_batch(texts, ticket_id="TF", return_aggregated=True)
    assert res["comment_count"] == 50


def test_real_data_risk_detection(engine: RiskNLPEngine, github_issues: List[Dict[str, Any]]):
    texts = [x.get("text", "") for x in github_issues[:50]]
    per = engine.analyze_text_batch(texts, return_aggregated=False)
    risk_pct = sum(1 for x in per if x["is_risk"]) / max(len(per), 1)
    assert risk_pct >= 0.30


# I) PERFORMANCE TESTS

def test_batch_throughput_50_comments(engine: RiskNLPEngine):
    comments = ["blocked on API integration" for _ in range(50)]
    start = time.perf_counter()
    res = engine.analyze_text_batch(comments, ticket_id="PERF", return_aggregated=True)
    elapsed = time.perf_counter() - start
    assert res["comment_count"] == 50
    assert elapsed < 2.0


def test_per_comment_latency(engine: RiskNLPEngine):
    comments = ["depends on vendor, waiting for response" for _ in range(50)]
    per = engine.analyze_text_batch(comments, return_aggregated=False)
    avg_ms = sum(float(x["processing_time_ms"]) for x in per) / max(len(per), 1)
    assert avg_ms < 40.0


# J) ERROR HANDLING TESTS

def test_empty_input(engine: RiskNLPEngine):
    assert engine.analyze_text_batch([]) == []


def test_long_text_truncation(engine: RiskNLPEngine):
    long_text = "word " * 700
    res = engine.analyze_text_batch([long_text], return_aggregated=False)[0]
    assert REQUIRED_PER_COMMENT_KEYS.issubset(res.keys())


def test_special_characters(engine: RiskNLPEngine):
    unicode_char = chr(0x2603)  # Snowman
    text = "Blocked on API integration; details: " + unicode_char + " and symbols @$%^&*()"
    res = engine.analyze_text_batch([text], return_aggregated=False)[0]
    assert isinstance(res["text"], str)


# K) LOGGING TESTS

def test_audit_log_creation(engine: RiskNLPEngine):
    path = os.path.join("logs", "nlp_audit.log")
    engine.analyze_text_batch(["blocked on API"], ticket_id="LOG", return_aggregated=True)
    assert os.path.exists(path)
    assert os.path.getsize(path) > 0


def test_log_format(engine: RiskNLPEngine):
    path = os.path.join("logs", "nlp_audit.log")
    engine.analyze_text_batch(["depends on backend"], ticket_id="LOG2", return_aggregated=True)

    with open(path, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f.readlines() if line.strip()]

    assert lines, "Expected log file to have entries"
    last = lines[-1]
    # Example: 2026-04-09 13:36:02,871 | name | INFO | func:line | message
    pattern = re.compile(
        r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \| .+ \| (INFO|WARNING|ERROR) \| .+:\d+ \| .+$"
    )
    assert pattern.match(last)


# Additional coverage tests (keep deterministic)

def test_risk_score_range(engine: RiskNLPEngine, sample_texts: List[str]):
    per = engine.analyze_text_batch(sample_texts[:6], return_aggregated=False)
    for item in per:
        assert 0.0 <= float(item["risk_score"]) <= 1.0


def test_sentiment_schema(engine: RiskNLPEngine):
    res = engine.analyze_text_batch(["blocked on API"], return_aggregated=False)[0]
    assert set(res["sentiment"].keys()) == {"label", "confidence"}
    assert isinstance(res["sentiment"]["label"], str)
    assert 0.0 <= float(res["sentiment"]["confidence"]) <= 1.0


def test_risk_phrases_have_context(engine: RiskNLPEngine):
    res = engine.analyze_text_batch(["blocked on API integration"], return_aggregated=False)[0]
    for phrase in res["risk_phrases"]:
        assert set(phrase.keys()) == {"phrase", "context", "entity_type", "confidence"}
        assert phrase["phrase"] in phrase["context"]


def test_entities_sorted_by_position(engine: RiskNLPEngine):
    text = "blocked then depends on backend and waiting for response"
    res = engine.analyze_text_batch([text], return_aggregated=False)[0]
    starts = [e["start_char"] for e in res["entities"]]
    assert starts == sorted(starts)


def test_aggregate_all_entities_dedupes(engine: RiskNLPEngine):
    comments = ["blocked on API", "blocked on API", "waiting for vendor"]
    agg = engine.analyze_text_batch(comments, return_aggregated=True)
    all_entities = agg["all_entities"]
    seen = set()
    for e in all_entities:
        key = (e["text"].lower(), e["type"])
        assert key not in seen
        seen.add(key)


def test_risk_distribution_has_all_categories(engine: RiskNLPEngine):
    agg = engine.analyze_text_batch(["deadline by end of Friday"], return_aggregated=True)
    dist = agg["risk_distribution"]
    assert set(dist.keys()) == {"SCHEDULE", "BUDGET", "RESOURCE", "TECHNICAL", "EXTERNAL"}


def test_confidence_distribution_has_all_levels(engine: RiskNLPEngine):
    agg = engine.analyze_text_batch(["everything on track"], return_aggregated=True)
    dist = agg["confidence_distribution"]
    assert set(dist.keys()) == {"HIGH", "MEDIUM", "LOW", "UNCERTAIN"}
