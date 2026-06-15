from __future__ import annotations

"""Embedder — calls OpenAI embeddings API (text-embedding-3-large).

Switched from VNG MaaS (baai/bge-m3) to OpenAI.  The previous VNG MaaS
implementation with model-catalogue fallback and daily-quota tracking is
commented out at the bottom of this file for reference.

text-embedding-3-large produces 3072-dimensional vectors.
The OpenAI SDK reads OPENAI_API_KEY from the environment when api_key is not
explicitly provided — useful for local dev.
"""

import logging

import numpy as np
from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

_OPENAI_EMBED_DIM = 3072  # text-embedding-3-large
_BATCH_SIZE = 512          # OpenAI allows up to 2048 inputs per call
_MAX_ATTEMPTS = 3


def _is_transient(exc: BaseException) -> bool:
    if isinstance(exc, RateLimitError):
        try:
            retry_after = float(exc.response.headers.get("Retry-After", "0"))
        except Exception:  # noqa: BLE001
            retry_after = 0.0
        return retry_after < 3600  # short rate-limit only; daily quota is not retried
    return isinstance(exc, (APITimeoutError, APIConnectionError, InternalServerError))


class EmbeddingUnavailable(RuntimeError):
    """Raised when the OpenAI embeddings call fails after retries."""


class Embedder:
    """OpenAI embeddings client (text-embedding-3-large).

    Keeps the same public interface as the previous VNG MaaS implementation so
    all callers (FaissRetriever, OpenSearchRetriever, OpenSearchIndexBuilder, etc.)
    work unchanged.
    """

    def __init__(
        self,
        model_name: str,
        *,
        api_key: str = "",
        base_url: str = "",   # kept for call-site compatibility; pass "" for OpenAI default
        cache_dir=None,       # kept for call-site compatibility; unused
    ) -> None:
        self._model = model_name
        self._client = OpenAI(
            api_key=api_key or "missing",    # "missing" → will fail only on actual call
            base_url=base_url or None,       # None → https://api.openai.com/v1
        )

    @property
    def dimension(self) -> int:
        return _OPENAI_EMBED_DIM

    def encode_query(self, text: str) -> np.ndarray:
        """Embed a single query. Returns shape (dim,)."""
        return self._encode([text])[0]

    def encode_passages(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of passages. Returns shape (len(texts), dim)."""
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)
        return self._encode(texts)

    # ── internals ────────────────────────────────────────────────────────────

    def _encode(self, texts: list[str]) -> np.ndarray:
        all_vecs: list[list[float]] = []
        for i in range(0, len(texts), _BATCH_SIZE):
            batch = texts[i : i + _BATCH_SIZE]
            all_vecs.extend(self._encode_batch(batch))
        mat = np.asarray(all_vecs, dtype=np.float32)
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        return mat / norms

    def _encode_batch(self, texts: list[str]) -> list[list[float]]:
        @retry(
            stop=stop_after_attempt(_MAX_ATTEMPTS),
            wait=wait_exponential(multiplier=0.5, max=8),
            retry=retry_if_exception(_is_transient),
            reraise=True,
        )
        def _call() -> list[list[float]]:
            resp = self._client.embeddings.create(model=self._model, input=texts)
            return [item.embedding for item in sorted(resp.data, key=lambda x: x.index)]

        try:
            return _call()
        except Exception as exc:  # noqa: BLE001
            logger.error("Embedder model=%s request failed after retries: %s", self._model, exc)
            raise EmbeddingUnavailable(str(exc)) from exc


# =============================================================================
# VNG MaaS (legacy) — commented out
# =============================================================================
#
# The implementation below called the VNG MaaS embeddings endpoint
# (baai/bge-m3, 1024 dims) with automatic model-catalogue fallback and
# daily-quota tracking via GET /v1/models.  Replaced by OpenAI above.
#
# import threading
# import time
# import httpx
#
# _BGE_M3_DIM = 1024
# _DAILY_QUOTA_RETRY_AFTER_THRESHOLD = 3600
# _MODELS_CACHE_TTL = 600
# _quota_exhausted_until: dict[str, float] = {}
#
# class Embedder:  # VNG MaaS version
#     def __init__(self, model_name, *, base_url="", api_key="", cache_dir=None):
#         self._primary = model_name
#         self._base_url = (base_url or "").rstrip("/")
#         self._api_key = api_key
#         self._models_cache: list[str] = []
#         self._models_cache_ts: float = 0.0
#         self._models_cache_lock = threading.Lock()
#
#     @property
#     def dimension(self) -> int:
#         return _BGE_M3_DIM
#
#     def _fetch_embedding_models(self) -> list[str]:
#         # GET /v1/models → filter model_type=="embedding" && status=="enabled"
#         ...
#
#     def _encode_with_model(self, model, texts):
#         # POST /v1/embeddings with encoding_format="dense"
#         ...
# =============================================================================
