from __future__ import annotations

"""End-to-end retrieval refinement: recency → hybrid fusion → cross-encoder rerank."""

import logging
from functools import lru_cache

from app.config import Settings, get_settings
from app.ports.types import RetrievedChunk
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.lexical import bm25_scores
from app.retrieval.recency import prefer_recent_versions
from app.retrieval.reranker import CrossEncoderReranker, RerankFn, rerank_candidates

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _default_reranker(model_name: str, cache_dir: str | None) -> CrossEncoderReranker:
    return CrossEncoderReranker(model_name, cache_dir=cache_dir)


def refine_candidates(
    query: str,
    candidates: list[RetrievedChunk],
    *,
    settings: Settings | None = None,
    reranker: RerankFn | CrossEncoderReranker | None = None,
    keywords: str = "",
) -> list[RetrievedChunk]:
    """Refine a dense candidate pool to the final top-k chunks.

    Pipeline (MVP checklist §2 Retrieval):
    1. Prefer newest ``last_modified`` when URLs collide.
    2. Hybrid: fuse dense rank + BM25 lexical scores (RRF).
       When LLM-extracted ``keywords`` are available they replace the full query
       for BM25 scoring — focused terms improve precision over conversational noise.
    3. Cross-encoder rerank → keep ``topk`` (default 5–8).
    """
    cfg = settings or get_settings()
    if not candidates:
        return []

    pool = prefer_recent_versions(candidates)

    if cfg.hybrid_search_enabled and len(pool) > 1:
        texts = [f"{c.title}\n{c.text}".strip() for c in pool]
        bm25_query = keywords if keywords else query
        lexical = bm25_scores(bm25_query, texts)
        pool = reciprocal_rank_fusion(pool, lexical)

    final_k = min(cfg.topk, len(pool))
    if not cfg.reranker_enabled:
        return pool[:final_k]

    active = reranker
    if active is None:
        cache = f"{cfg.index_dir}/hf-cache" if cfg.index_dir else None
        active = _default_reranker(cfg.reranker_model, cache)

    refined = rerank_candidates(query, pool, final_k=final_k, scorer=active)
    logger.info(
        "retrieval pipeline: %d candidates → %d after hybrid+rerank",
        len(candidates),
        len(refined),
    )
    return refined
