from __future__ import annotations

"""Embedder — local multilingual sentence-transformer for query/passage vectors.

Embeddings are produced **locally** (CPU), so they cost zero MaaS tokens — this
is what makes the daily sync pipeline token-free (03-ARCHITECTURE.md §5a).

The default model ``intfloat/multilingual-e5-small`` is an E5 model, which
requires asymmetric prefixes: queries are encoded with ``"query: "`` and corpus
passages with ``"passage: "``.  Mixing them up silently degrades recall, so the
two are separate methods here and both the retriever (queries) and the future
ingestion job (passages) go through this one class.

Vectors are L2-normalized, so a FAISS inner-product (``IndexFlatIP``) search is
equivalent to cosine similarity.

The model is loaded lazily on first use (not at construction) so that importing
the adapter — and starting the container's ``/health`` server — never blocks on
a multi-hundred-MB model download.  ``model.encode`` is guarded by a lock
because the same instance is shared across concurrent department branches.
"""

import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:  # avoid importing the heavy package at module import time
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_QUERY_PREFIX = "query: "
_PASSAGE_PREFIX = "passage: "


class Embedder:
    """Lazy, thread-safe wrapper around a SentenceTransformer model."""

    def __init__(self, model_name: str, *, cache_dir: str | Path | None = None) -> None:
        """Configure (but do not load) the embedding model.

        Args:
            model_name: HuggingFace model id, e.g. ``intfloat/multilingual-e5-small``.
            cache_dir: Where to cache downloaded model weights.  Defaults to the
                HF default; the retriever points this at ``{index_dir}/hf-cache``.
        """
        self._model_name = model_name
        self._cache_dir = str(cache_dir) if cache_dir else None
        self._model: "SentenceTransformer | None" = None
        self._load_lock = threading.Lock()
        self._encode_lock = threading.Lock()

    # ── Lazy load ─────────────────────────────────────────────────────────────

    def _get_model(self) -> "SentenceTransformer":
        """Load the model on first use (double-checked under a lock)."""
        if self._model is not None:
            return self._model
        with self._load_lock:
            if self._model is None:
                from sentence_transformers import SentenceTransformer

                logger.info(
                    "Loading embedding model %s (cache=%s)",
                    self._model_name,
                    self._cache_dir or "<default>",
                )
                self._model = SentenceTransformer(
                    self._model_name, cache_folder=self._cache_dir
                )
        return self._model

    @property
    def dimension(self) -> int:
        """Embedding dimensionality (loads the model if needed)."""
        return int(self._get_model().get_sentence_embedding_dimension())

    # ── Encoding ──────────────────────────────────────────────────────────────

    def encode_query(self, text: str) -> np.ndarray:
        """Encode a single search *query* into a normalized float32 vector.

        Returns a 1-D array of shape ``(dim,)``.
        """
        return self._encode([_QUERY_PREFIX + text])[0]

    def encode_passages(self, texts: list[str]) -> np.ndarray:
        """Encode corpus *passages* into a normalized float32 matrix.

        Used by the ingestion job.  Returns shape ``(len(texts), dim)``.
        """
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)
        return self._encode([_PASSAGE_PREFIX + t for t in texts])

    def _encode(self, prefixed: list[str]) -> np.ndarray:
        """Run the model and return L2-normalized float32 vectors."""
        model = self._get_model()
        with self._encode_lock:
            vecs = model.encode(
                prefixed,
                convert_to_numpy=True,
                normalize_embeddings=True,  # L2 → inner product == cosine
            )
        return np.asarray(vecs, dtype=np.float32)
