"""Retrieval pipeline tests — hybrid fusion, recency, rerank."""

from __future__ import annotations

from app.config import Settings
from app.ports.types import RetrievedChunk
from app.retrieval.lexical import bm25_scores, tokenize
from app.retrieval.pipeline import refine_candidates
from app.retrieval.recency import prefer_recent_versions
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


class StubReranker:
    """Deterministic reranker for unit tests (no model download)."""

    def score_pairs(self, pairs: list[tuple[str, str]]) -> list[float]:
        # Prefer passages containing "escalation" (lexical signal in query).
        return [1.0 if "escalation" in passage.lower() else 0.1 for _, passage in pairs]


def _chunk(
    *,
    chunk_id: str,
    text: str,
    score: float = 0.5,
    url: str = "https://example.com/doc",
    last_modified: str | None = None,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        department=RISK,
        doc_type="policy",
        title="Policy",
        url=url,
        section=None,
        last_modified=last_modified,
        lifecycle_state="active",
        source_type="confluence",
        page=None,
        text=text,
        score=score,
    )


def test_tokenize_vietnamese_diacritics():
    tokens = tokenize("Quy trình leo thang rủi ro")
    assert "quy" in tokens
    assert "leo" in tokens


def test_bm25_prefers_matching_terms():
    scores = bm25_scores(
        "escalation policy",
        ["unrelated merchant onboarding", "risk escalation requires approval"],
    )
    assert scores[1] > scores[0]


def test_prefer_recent_versions_keeps_newest_url():
    older = _chunk(
        chunk_id="old",
        text="old version",
        url="https://example.com/same",
        last_modified="2023-01-01T00:00:00Z",
        score=0.9,
    )
    newer = _chunk(
        chunk_id="new",
        text="new version",
        url="https://example.com/same",
        last_modified="2024-06-01T00:00:00Z",
        score=0.7,
    )
    out = prefer_recent_versions([older, newer])
    assert len(out) == 1
    assert out[0].chunk_id == "new"


def test_refine_candidates_applies_hybrid_and_rerank():
    settings = Settings(
        topk=2,
        retrieve_pool=10,
        hybrid_search_enabled=True,
        reranker_enabled=True,
    )
    candidates = [
        _chunk(chunk_id="a", text="merchant growth playbook", score=0.95, url="https://a"),
        _chunk(
            chunk_id="b",
            text="risk escalation requires manager approval",
            score=0.5,
            url="https://b",
        ),
        _chunk(chunk_id="c", text="bank settlement SLA", score=0.4, url="https://c"),
    ]
    out = refine_candidates(
        "escalation policy",
        candidates,
        settings=settings,
        reranker=StubReranker(),
    )
    assert len(out) == 2
    assert out[0].chunk_id == "b"


def test_refine_candidates_empty_pool():
    settings = Settings(topk=8)
    assert refine_candidates("q", [], settings=settings) == []
