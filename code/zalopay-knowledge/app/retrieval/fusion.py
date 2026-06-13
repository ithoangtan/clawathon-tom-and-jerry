from __future__ import annotations

"""Score fusion helpers for hybrid retrieval."""

from app.ports.types import RetrievedChunk


def reciprocal_rank_fusion(
    dense: list[RetrievedChunk],
    lexical_scores: list[float],
    *,
    k: int = 60,
) -> list[RetrievedChunk]:
    """Fuse dense rank order with BM25 scores via RRF.

    Args:
        dense: Candidates sorted by dense score (descending).
        lexical_scores: BM25 scores aligned 1:1 with *dense*.
        k: RRF constant (default 60).
    """
    if not dense:
        return []

    dense_rank = {c.chunk_id: rank for rank, c in enumerate(dense)}
    lexical_order = sorted(
        range(len(dense)),
        key=lambda i: lexical_scores[i] if i < len(lexical_scores) else 0.0,
        reverse=True,
    )
    lexical_rank = {dense[i].chunk_id: rank for rank, i in enumerate(lexical_order)}

    fused: list[tuple[float, RetrievedChunk]] = []
    for chunk in dense:
        dr = dense_rank.get(chunk.chunk_id, len(dense))
        lr = lexical_rank.get(chunk.chunk_id, len(dense))
        score = 1.0 / (k + dr + 1) + 1.0 / (k + lr + 1)
        updated = RetrievedChunk(**{**chunk.__dict__, "score": score})
        fused.append((score, updated))

    fused.sort(key=lambda pair: pair[0], reverse=True)
    return [chunk for _, chunk in fused]
