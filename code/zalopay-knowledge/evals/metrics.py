from __future__ import annotations

"""Offline eval metrics for golden-set regression (Eval MUST 🟢)."""

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def keyword_coverage(text: str, keywords: Sequence[str]) -> float:
    """Fraction of keywords found in *text* (case-insensitive)."""
    if not keywords:
        return 1.0
    norm = _normalize(text)
    hits = sum(1 for kw in keywords if _normalize(kw) in norm)
    return hits / len(keywords)


def context_recall_at_k(
    retrieved_ids: Sequence[str],
    relevant_ids: Iterable[str],
    k: int,
) -> float:
    """Context recall @k — fraction of relevant chunks present in top-k."""
    relevant = set(relevant_ids)
    if not relevant:
        return 1.0
    top_k = set(retrieved_ids[:k])
    return len(top_k & relevant) / len(relevant)


def context_precision_at_k(
    retrieved_ids: Sequence[str],
    relevant_ids: Iterable[str],
    k: int,
) -> float:
    """Context precision @k — fraction of top-k chunks that are relevant."""
    if k <= 0:
        return 0.0
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    relevant = set(relevant_ids)
    hits = sum(1 for cid in top_k if cid in relevant)
    return hits / len(top_k)


def faithfulness_score(answer: str, source_texts: Sequence[str]) -> float:
    """
    Heuristic faithfulness: share of answer sentences with a lexical overlap
    hook in at least one source chunk. MVP offline proxy for entailment.
    """
    sentences = [s.strip() for s in answer.replace("\n", " ").split(".") if s.strip()]
    if not sentences:
        return 0.0
    sources_norm = [_normalize(s) for s in source_texts if s.strip()]
    if not sources_norm:
        return 0.0

    supported = 0
    for sentence in sentences:
        if len(sentence) < 12:
            continue
        words = [w for w in _normalize(sentence).split() if len(w) > 3]
        if not words:
            continue
        for src in sources_norm:
            if any(w in src for w in words[:6]):
                supported += 1
                break
    scorable = sum(1 for s in sentences if len(s) >= 12)
    if scorable == 0:
        return 1.0
    return supported / scorable


def answer_relevance(answer: str, expected_keywords: Sequence[str]) -> float:
    """Answer relevance — keyword coverage against expected answer facets."""
    return keyword_coverage(answer, expected_keywords)


@dataclass
class RefusalCounts:
    true_positive: int = 0
    false_positive: int = 0
    true_negative: int = 0
    false_negative: int = 0

    @property
    def precision(self) -> float:
        denom = self.true_positive + self.false_positive
        return self.true_positive / denom if denom else 1.0

    @property
    def recall(self) -> float:
        denom = self.true_positive + self.false_negative
        return self.true_positive / denom if denom else 1.0


def refusal_counts(
    cases: Sequence[dict[str, Any]],
    actual_status: dict[str, str],
) -> RefusalCounts:
    """Refusal precision/recall from golden ``must_refuse`` labels."""
    counts = RefusalCounts()
    for case in cases:
        case_id = case.get("id", "")
        expect = case.get("expect", {})
        must_refuse = bool(expect.get("must_refuse"))
        predicted_refused = actual_status.get(case_id) == "refused"

        if must_refuse and predicted_refused:
            counts.true_positive += 1
        elif must_refuse and not predicted_refused:
            counts.false_negative += 1
        elif not must_refuse and predicted_refused:
            counts.false_positive += 1
        else:
            counts.true_negative += 1
    return counts


@dataclass
class EvalSummary:
    total: int = 0
    status_pass: int = 0
    context_recall_at_k: dict[int, float] = field(default_factory=dict)
    context_precision_at_k: dict[int, float] = field(default_factory=dict)
    faithfulness: float = 0.0
    answer_relevance: float = 0.0
    refusal_precision: float = 1.0
    refusal_recall: float = 1.0
    over_refusal_rate: float = 0.0
    hallucination_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "status_pass": self.status_pass,
            "context_recall_at_k": self.context_recall_at_k,
            "context_precision_at_k": self.context_precision_at_k,
            "faithfulness": round(self.faithfulness, 4),
            "answer_relevance": round(self.answer_relevance, 4),
            "refusal_precision": round(self.refusal_precision, 4),
            "refusal_recall": round(self.refusal_recall, 4),
            "over_refusal_rate": round(self.over_refusal_rate, 4),
            "hallucination_rate": round(self.hallucination_rate, 4),
        }


def aggregate_eval(
    cases: Sequence[dict[str, Any]],
    results: Sequence[dict[str, Any]],
    k_values: Sequence[int] = (5, 8),
) -> EvalSummary:
    """Aggregate retrieval, generation, and refusal metrics from per-case results."""
    summary = EvalSummary(total=len(cases))
    faith_scores: list[float] = []
    relevance_scores: list[float] = []
    recall_by_k: dict[int, list[float]] = {k: [] for k in k_values}
    precision_by_k: dict[int, list[float]] = {k: [] for k in k_values}
    actual_status: dict[str, str] = {}

    by_id = {r.get("id"): r for r in results}

    for case in cases:
        case_id = case.get("id", "")
        result = by_id.get(case_id, {})
        expect = case.get("expect", {})
        expect_status = expect.get("status")
        actual_status_val = result.get("status", "")
        actual_status[case_id] = actual_status_val

        if expect_status and actual_status_val == expect_status:
            summary.status_pass += 1

        retrieval = case.get("retrieval") or {}
        relevant_ids = retrieval.get("relevant_chunk_ids") or []
        retrieved_ids = result.get("retrieved_chunk_ids") or []
        if relevant_ids and retrieved_ids:
            for k in k_values:
                recall_by_k[k].append(context_recall_at_k(retrieved_ids, relevant_ids, k))
                precision_by_k[k].append(
                    context_precision_at_k(retrieved_ids, relevant_ids, k)
                )

        answer = result.get("answer") or ""
        if answer and not expect.get("must_refuse"):
            keywords = expect.get("answer_keywords") or []
            if keywords:
                relevance_scores.append(answer_relevance(answer, keywords))
            sources = result.get("source_texts") or []
            if sources:
                faith_scores.append(faithfulness_score(answer, sources))

    for k in k_values:
        vals_r = recall_by_k[k]
        vals_p = precision_by_k[k]
        summary.context_recall_at_k[k] = sum(vals_r) / len(vals_r) if vals_r else 0.0
        summary.context_precision_at_k[k] = sum(vals_p) / len(vals_p) if vals_p else 0.0

    summary.faithfulness = sum(faith_scores) / len(faith_scores) if faith_scores else 0.0
    summary.answer_relevance = (
        sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
    )

    refusal = refusal_counts(cases, actual_status)
    summary.refusal_precision = refusal.precision
    summary.refusal_recall = refusal.recall

    answered_when_should = refusal.false_positive
    refused_when_should_answer = refusal.false_negative
    should_answer = answered_when_should + refusal.true_negative
    should_refuse = refusal.true_positive + refused_when_should_answer
    summary.over_refusal_rate = (
        refused_when_should_answer / should_answer if should_answer else 0.0
    )
    summary.hallucination_rate = (
        answered_when_should / should_refuse if should_refuse else 0.0
    )

    return summary
