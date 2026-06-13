from __future__ import annotations

"""Cross-encoder reranker — retrieve pool → rerank → final top-k."""

import logging
import threading
from typing import Callable, Protocol

from app.ports.types import RetrievedChunk

logger = logging.getLogger(__name__)


class RerankFn(Protocol):
    """Callable that scores (query, passage) pairs."""

    def __call__(self, pairs: list[tuple[str, str]]) -> list[float]: ...


class CrossEncoderReranker:
    """Lazy-loaded cross-encoder (bge-reranker-v2-m3 class for MVP)."""

    def __init__(self, model_name: str, *, cache_dir: str | None = None) -> None:
        self._model_name = model_name
        self._cache_dir = cache_dir
        self._model = None
        self._lock = threading.Lock()

    def _get_model(self):
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is None:
                from sentence_transformers import CrossEncoder

                logger.info("Loading cross-encoder reranker %s", self._model_name)
                self._model = CrossEncoder(
                    self._model_name,
                    max_length=512,
                    trust_remote_code=True,
                )
        return self._model

    def score_pairs(self, pairs: list[tuple[str, str]]) -> list[float]:
        if not pairs:
            return []
        model = self._get_model()
        with self._lock:
            raw = model.predict(pairs)
        return [float(s) for s in raw]


def rerank_candidates(
    query: str,
    candidates: list[RetrievedChunk],
    *,
    final_k: int,
    scorer: RerankFn | CrossEncoderReranker | None = None,
) -> list[RetrievedChunk]:
    """Rerank *candidates* with a cross-encoder and return top *final_k*."""
    if not candidates:
        return []
    if scorer is None or len(candidates) <= final_k:
        return candidates[:final_k]

    passages = [
        f"{c.title}\n{c.text}".strip() if c.title else c.text
        for c in candidates
    ]
    pairs = [(query, p) for p in passages]
    scores = scorer.score_pairs(pairs)

    ranked = sorted(
        zip(scores, candidates, strict=True),
        key=lambda item: item[0],
        reverse=True,
    )
    out: list[RetrievedChunk] = []
    for score, chunk in ranked[:final_k]:
        out.append(RetrievedChunk(**{**chunk.__dict__, "score": max(0.0, min(1.0, score))}))
    return out
