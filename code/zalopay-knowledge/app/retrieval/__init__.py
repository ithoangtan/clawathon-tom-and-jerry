from __future__ import annotations

"""Retrieval refinement — hybrid fusion, reranking, and recency preference.

The FAISS adapter returns a dense candidate pool; this package refines it to the
final top-k chunks passed to the grade gate (MVP: retrieve 30–50 → rerank → 5–8).
"""

from app.retrieval.pipeline import refine_candidates

__all__ = ["refine_candidates"]
