"""
NLP-based risk detection engine for Jira comment analysis.
"""

from __future__ import annotations

import logging
import os
import re
import time
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import spacy
except Exception:  # pragma: no cover - dependency/runtime availability
    spacy = None

try:
    from transformers import AutoTokenizer, pipeline
except Exception:  # pragma: no cover - dependency/runtime availability
    AutoTokenizer = None
    pipeline = None


class RiskNLPEngine:
    """NLP risk detection engine with NER, sentiment, and aggregation."""

    SPACY_MODEL = "en_core_web_sm"
    SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
    LOG_FORMAT = (
        "%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s"
    )
    LOG_PATH = "logs/nlp_audit.log"
    CONTEXT_WINDOW = 50

    ENTITY_PATTERNS: Dict[str, List[Tuple[str, float]]] = {
        "DEADLINE": [
            (r"\bby end of\b", 0.95),
            (r"\bmust finish\b", 0.95),
            (r"\btarget date\b", 0.92),
            (r"\bdeadline\b", 0.90),
            (r"\bdue\b", 0.85),
            (r"\beta\b", 0.88),
        ],
        "BLOCKER": [
            (r"\bcannot proceed\b", 0.95),
            (r"\bblocked\b", 0.92),
            (r"\bblocking\b", 0.90),
            (r"\bhalted\b", 0.90),
            (r"\bstuck\b", 0.88),
            (r"\bwaiting for\b", 0.82),
        ],
        "DEPENDENCY": [
            (r"\bdepends on\b", 0.95),
            (r"\bcontingent on\b", 0.92),
            (r"\brequires\b", 0.88),
            (r"\bneeds\b", 0.85),
            (r"\bwaiting for\b", 0.80),
        ],
        "RESOURCE": [
            (r"\bresource\b", 0.88),
            (r"\bbandwidth\b", 0.90),
            (r"\bcapacity\b", 0.90),
            (r"\bheadcount\b", 0.92),
            (r"\bunavailable\b", 0.88),
            (r"\bsick leave\b", 0.92),
        ],
    }

    CATEGORY_KEYWORDS: Dict[str, List[str]] = {
        "SCHEDULE": [
            "deadline",
            "due",
            "eta",
            "timeline",
            "target date",
            "by end of",
            "delay",
            "late",
        ],
        "BUDGET": ["cost", "budget", "overrun", "expense", "financial"],
        "RESOURCE": [
            "resource",
            "unavailable",
            "shortage",
            "capacity",
            "headcount",
            "bandwidth",
        ],
        "TECHNICAL": [
            "bug",
            "error",
            "architecture",
            "integration",
            "system",
            "infrastructure",
            "blocked",
        ],
        "EXTERNAL": [
            "vendor",
            "third-party",
            "client",
            "regulatory",
            "external dependency",
            "depends on",
        ],
    }

    ENTITY_TO_CATEGORY = {
        "DEADLINE": "SCHEDULE",
        "BLOCKER": "TECHNICAL",
        "DEPENDENCY": "EXTERNAL",
        "RESOURCE": "RESOURCE",
    }

    def __init__(self) -> None:
        """Initialize NLP and sentiment models with resilient fallbacks."""
        self.logger = self._setup_logger()
        self.nlp = None
        self.sentiment_pipeline = None
        self.tokenizer = None
        self._load_models()

    def analyze_text_batch(
        self,
        text_list: List[str],
        ticket_id: Optional[str] = None,
        return_aggregated: bool = True,
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Analyze batch of text snippets for risk signals.

        Args:
            text_list: List of comment/text strings to analyze.
            ticket_id: Optional ticket identifier for aggregation.
            return_aggregated: If True, return ticket-level summary; else per-comment list.

        Returns:
            Per-comment analysis list, or ticket-level aggregate dictionary.
        """
        if not text_list:
            self.logger.info("[INFO] Empty input list received; returning empty result")
            return []

        batch_start = time.perf_counter()
        self.logger.info("[INFO] Processing batch of %d comments", len(text_list))

        prepared_texts = [self._prepare_text_for_model(text) for text in text_list]
        sentiment_outputs = self._run_sentiment_batch(prepared_texts)
        docs = self._run_spacy_batch(text_list)

        per_comment_results: List[Dict[str, Any]] = []
        entity_type_counter: Counter[str] = Counter()
        confidence_distribution: Counter[str] = Counter()
        category_distribution: Counter[str] = Counter()
        risk_count = 0

        for idx, text in enumerate(text_list):
            comment_start = time.perf_counter()

            doc = docs[idx] if idx < len(docs) else None
            entities = self._extract_entities(text, doc)
            for entity in entities:
                entity_type_counter[entity["type"]] += 1

            risk_phrases = self._extract_risk_phrases(text, entities)
            sentiment = sentiment_outputs[idx]
            risk_score, is_risk = self._compute_risk_score(sentiment, entities)
            risk_level = self._score_to_level(risk_score)
            risk_category = self._infer_risk_category(text, entities)

            processing_time_ms = (time.perf_counter() - comment_start) * 1000.0

            if processing_time_ms > 1000.0:
                self.logger.warning(
                    "[WARN] Comment exceeded timeout threshold %.2fms; marking as UNCERTAIN",
                    processing_time_ms,
                )
                entities = []
                risk_phrases = []
                risk_score = 0.49
                risk_level = "UNCERTAIN"
                is_risk = False
                risk_category = self._infer_risk_category(text, entities)

            if is_risk:
                risk_count += 1
                category_distribution[risk_category] += 1
            if risk_level == "LOW":
                self.logger.warning(
                    "[WARN] Low confidence risk detected (score=%.2f): %s",
                    risk_score,
                    text[:200],
                )

            confidence_distribution[risk_level] += 1

            per_comment_result: Dict[str, Any] = {
                "text": text,
                "risk_score": round(float(risk_score), 4),
                "risk_level": risk_level,
                "is_risk": bool(is_risk),
                "sentiment": {
                    "label": sentiment["label"],
                    "confidence": round(float(sentiment["confidence"]), 4),
                },
                "entities": [
                    {
                        "text": entity["text"],
                        "type": entity["type"],
                        "confidence": round(float(entity["confidence"]), 4),
                        "start_char": entity["start_char"],
                        "end_char": entity["end_char"],
                    }
                    for entity in entities
                ],
                "risk_category": risk_category,
                "risk_phrases": risk_phrases,
                "processing_time_ms": round(float(processing_time_ms), 3),
            }
            per_comment_results.append(per_comment_result)

        total_processing_time_ms = (time.perf_counter() - batch_start) * 1000.0
        avg_ms_per_comment = total_processing_time_ms / max(len(text_list), 1)
        risk_detection_rate = (risk_count / len(text_list)) * 100.0

        self.logger.info(
            "[PERFORMANCE] Batch completed in %.2f seconds (%.2fms/comment average)",
            total_processing_time_ms / 1000.0,
            avg_ms_per_comment,
        )
        self.logger.info("[INFO] Entity extraction count by type: %s", dict(entity_type_counter))
        self.logger.info(
            "[INFO] Confidence distribution: %s", dict(confidence_distribution)
        )
        self.logger.info(
            "[INFO] Risk detection rate: %.2f%% (%d/%d)",
            risk_detection_rate,
            risk_count,
            len(text_list),
        )

        if return_aggregated:
            return self._aggregate_results(
                per_comment_results=per_comment_results,
                ticket_id=ticket_id,
                total_processing_time_ms=total_processing_time_ms,
                category_distribution=category_distribution,
                confidence_distribution=confidence_distribution,
            )

        return per_comment_results

    def _setup_logger(self) -> logging.Logger:
        """Create file logger for NLP risk auditing."""
        os.makedirs(os.path.dirname(self.LOG_PATH), exist_ok=True)
        logger = logging.getLogger(f"{__name__}.RiskNLPEngine")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            file_handler = logging.FileHandler(self.LOG_PATH)
            file_handler.setFormatter(logging.Formatter(self.LOG_FORMAT))
            logger.addHandler(file_handler)
            logger.propagate = False

        return logger

    def _load_models(self) -> None:
        """Load spaCy and transformer models with fallback behavior."""
        load_start = time.perf_counter()

        self._load_spacy_model()
        self._load_transformer_model()

        elapsed_ms = (time.perf_counter() - load_start) * 1000.0
        self.logger.info(
            "[INFO] Engine initialized: spacy model=%s, sentiment model=%s, load_time_ms=%.2f",
            self.SPACY_MODEL if self.nlp is not None else "keyword-only-fallback",
            self.SENTIMENT_MODEL
            if self.sentiment_pipeline is not None
            else "neutral-fallback",
            elapsed_ms,
        )

    def _load_spacy_model(self) -> None:
        """Load spaCy model for NER, otherwise fallback to keyword-only extraction."""
        if spacy is None:
            self.logger.warning("[WARN] spaCy dependency unavailable; using keyword-only fallback")
            self.nlp = None
            return

        try:
            self.nlp = spacy.load(
                self.SPACY_MODEL,
                disable=["tagger", "parser", "attribute_ruler", "lemmatizer"],
            )
        except Exception as exc:
            self.nlp = None
            self.logger.warning(
                "[WARN] Failed to load spaCy model (%s); using keyword-only fallback",
                str(exc),
            )

    def _load_transformer_model(self) -> None:
        """Load transformer sentiment model, otherwise use neutral fallback scoring."""
        if pipeline is None or AutoTokenizer is None:
            self.logger.error(
                "[ERROR] Failed to load transformer model: transformers dependency unavailable"
            )
            self.sentiment_pipeline = None
            self.tokenizer = None
            return

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.SENTIMENT_MODEL)
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.SENTIMENT_MODEL,
                tokenizer=self.tokenizer,
                device=-1,
            )
        except Exception as exc:
            self.logger.error("[ERROR] Failed to load transformer model: %s", str(exc))
            self.sentiment_pipeline = None
            self.tokenizer = None

    def _prepare_text_for_model(self, text: str) -> str:
        """Truncate long input to 512 tokens for transformer compatibility."""
        clean_text = text if isinstance(text, str) else str(text)
        if not clean_text.strip():
            return ""

        if self.tokenizer is None:
            return clean_text

        try:
            original_token_count = len(
                self.tokenizer(clean_text, add_special_tokens=True, truncation=False)[
                    "input_ids"
                ]
            )
            encoded = self.tokenizer(
                clean_text,
                max_length=512,
                truncation=True,
                add_special_tokens=True,
            )
            if original_token_count > 512:
                self.logger.info(
                    "[INFO] Input text truncated from %d to 512 tokens",
                    original_token_count,
                )
            return self.tokenizer.decode(encoded["input_ids"], skip_special_tokens=True)
        except Exception as exc:
            self.logger.warning(
                "[WARN] Tokenization failed during truncation; using raw text (%s)",
                str(exc),
            )
            return clean_text

    def _run_sentiment_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Run batched sentiment classification with resilient fallback."""
        if self.sentiment_pipeline is None:
            return [{"label": "NEUTRAL", "confidence": 0.5} for _ in texts]

        try:
            batch_size = min(32, max(len(texts), 1))
            outputs = self.sentiment_pipeline(
                texts,
                truncation=True,
                max_length=512,
                batch_size=batch_size,
            )
            normalized: List[Dict[str, Any]] = []
            for output in outputs:
                model_label = str(output.get("label", "NEUTRAL")).upper()
                model_confidence = float(output.get("score", 0.5))
                if model_confidence < 0.60:
                    normalized.append({"label": "NEUTRAL", "confidence": model_confidence})
                elif "NEGATIVE" in model_label:
                    normalized.append({"label": "NEGATIVE", "confidence": model_confidence})
                else:
                    normalized.append({"label": "POSITIVE", "confidence": model_confidence})
            return normalized
        except Exception as exc:
            self.logger.error("[ERROR] Sentiment inference failed: %s", str(exc))
            return [{"label": "NEUTRAL", "confidence": 0.5} for _ in texts]

    def _run_spacy_batch(self, texts: List[str]) -> List[Any]:
        """Run spaCy analysis in batch mode when model is available."""
        if self.nlp is None:
            return [None for _ in texts]

        try:
            return list(self.nlp.pipe(texts, batch_size=min(64, max(len(texts), 1))))
        except Exception as exc:
            self.logger.warning(
                "[WARN] spaCy batch processing failed; falling back to keyword-only mode (%s)",
                str(exc),
            )
            return [None for _ in texts]

    def _extract_entities(self, text: str, doc: Any) -> List[Dict[str, Any]]:
        """Extract risk entities from spaCy NER and risk keyword patterns."""
        entities: List[Dict[str, Any]] = []
        seen: set[Tuple[int, int, str]] = set()

        if doc is not None:
            for ent in doc.ents:
                mapped_type = None
                confidence = 0.70
                if ent.label_ in {"DATE", "TIME"}:
                    mapped_type = "DEADLINE"
                    confidence = 0.75
                if mapped_type is None:
                    continue
                key = (ent.start_char, ent.end_char, mapped_type)
                if key in seen:
                    continue
                seen.add(key)
                entities.append(
                    {
                        "text": ent.text,
                        "type": mapped_type,
                        "confidence": confidence,
                        "start_char": ent.start_char,
                        "end_char": ent.end_char,
                    }
                )

        lowered = text.lower()
        for entity_type, pattern_specs in self.ENTITY_PATTERNS.items():
            for pattern, confidence in pattern_specs:
                for match in re.finditer(pattern, lowered, flags=re.IGNORECASE):
                    start_char, end_char = match.span()
                    key = (start_char, end_char, entity_type)
                    if key in seen:
                        continue
                    seen.add(key)
                    entities.append(
                        {
                            "text": text[start_char:end_char],
                            "type": entity_type,
                            "confidence": confidence,
                            "start_char": start_char,
                            "end_char": end_char,
                        }
                    )

        entities.sort(key=lambda item: item["start_char"])
        return entities

    def _extract_risk_phrases(
        self, text: str, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build context-rich risk phrase highlights around extracted entities."""
        phrases: List[Dict[str, Any]] = []
        for entity in entities:
            start = max(0, int(entity["start_char"]) - self.CONTEXT_WINDOW)
            end = min(len(text), int(entity["end_char"]) + self.CONTEXT_WINDOW)
            phrases.append(
                {
                    "phrase": entity["text"],
                    "context": text[start:end],
                    "entity_type": entity["type"],
                    "confidence": round(float(entity["confidence"]), 4),
                }
            )
        return phrases

    def _compute_risk_score(
        self, sentiment: Dict[str, Any], entities: List[Dict[str, Any]]
    ) -> Tuple[float, bool]:
        """Map sentiment and entities into a normalized risk score and risk flag."""
        label = sentiment["label"]
        confidence = float(sentiment["confidence"])

        if label == "NEGATIVE":
            risk_score = confidence
            is_risk = True
        elif label == "NEUTRAL":
            risk_score = 0.60 if entities else 0.45
            is_risk = bool(entities)
        else:
            risk_score = max(0.0, 1.0 - confidence)
            is_risk = False

        if is_risk and entities:
            risk_score += min(0.15, 0.05 * len(entities))

        risk_score = max(0.0, min(1.0, risk_score))
        return risk_score, is_risk

    def _score_to_level(self, risk_score: float) -> str:
        """Map numeric score to confidence bucket."""
        if risk_score >= 0.85:
            return "HIGH"
        if risk_score >= 0.65:
            return "MEDIUM"
        if risk_score >= 0.50:
            return "LOW"
        return "UNCERTAIN"

    def _infer_risk_category(self, text: str, entities: List[Dict[str, Any]]) -> str:
        """Infer top risk category from entities first, then category keyword rules."""
        if entities:
            for entity in entities:
                mapped = self.ENTITY_TO_CATEGORY.get(entity["type"])
                if mapped:
                    return mapped

        lowered = text.lower()
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                return category
        return "TECHNICAL"

    def _aggregate_results(
        self,
        per_comment_results: List[Dict[str, Any]],
        ticket_id: Optional[str],
        total_processing_time_ms: float,
        category_distribution: Counter[str],
        confidence_distribution: Counter[str],
    ) -> Dict[str, Any]:
        """Aggregate comment-level outputs into ticket-level summary."""
        all_entities: List[Dict[str, Any]] = []
        seen_entities: set[Tuple[str, str]] = set()
        risk_count = 0
        risk_scores: List[float] = []

        for result in per_comment_results:
            risk_scores.append(float(result["risk_score"]))
            if result["is_risk"]:
                risk_count += 1

            for entity in result["entities"]:
                dedupe_key = (entity["text"].lower(), entity["type"])
                if dedupe_key in seen_entities:
                    continue
                seen_entities.add(dedupe_key)
                all_entities.append(entity)

        avg_risk_score = sum(risk_scores) / max(len(risk_scores), 1)
        canonical_categories = ["SCHEDULE", "BUDGET", "RESOURCE", "TECHNICAL", "EXTERNAL"]
        category_counts = {
            category: int(category_distribution.get(category, 0))
            for category in canonical_categories
        }

        dominant_risk_category = "SCHEDULE"
        if any(category_counts.values()):
            dominant_risk_category = max(category_counts, key=category_counts.get)

        confidence_counts = {
            level: int(confidence_distribution.get(level, 0))
            for level in ["HIGH", "MEDIUM", "LOW", "UNCERTAIN"]
        }

        return {
            "ticket_id": ticket_id,
            "comment_count": len(per_comment_results),
            "total_comments_analyzed": len(per_comment_results),
            "risk_count": risk_count,
            "avg_risk_score": round(float(avg_risk_score), 4),
            "dominant_risk_category": dominant_risk_category,
            "risk_distribution": category_counts,
            "all_entities": all_entities,
            "confidence_distribution": confidence_counts,
            "total_processing_time_ms": round(float(total_processing_time_ms), 3),
            "comment_results": per_comment_results,
        }
