from __future__ import annotations

"""Embedder — VNG MaaS embeddings (baai/bge-m3, 1024-dim).

bge-m3 is a multilingual bi-encoder fine-tuned for retrieval tasks (BEIR/MTEB),
with strong Vietnamese support — better suited to Zalopay's bilingual internal
docs than OpenAI text-embedding-3-large which is English-centric.

Falls back to the next available model in the MaaS catalogue when the primary
hits its daily quota (tracked per-model via a simple timestamp guard).
"""

import logging
import threading
import time
from typing import Optional

import httpx
import numpy as np
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

_MODEL_DIMS: dict[str, int] = {
    "baai/bge-m3": 1024,
    "text-embedding-3-large": 3072,
    "text-embedding-3-small": 1536,
    "text-embedding-ada-002": 1536,
}
_DEFAULT_DIM = 1024
_BATCH_SIZE = 32           # MaaS embeddings endpoint limit
_MAX_ATTEMPTS = 3
_MODELS_CACHE_TTL = 600    # seconds before re-fetching model catalogue
_DAILY_QUOTA_RETRY_AFTER_THRESHOLD = 3600  # treat Retry-After >= 1 h as daily quota


class EmbeddingUnavailable(RuntimeError):
    """Raised when the embeddings call fails after retries."""


# Per-model timestamp: model key → Unix ts until which the model is considered quota-exhausted.
_quota_exhausted_until: dict[str, float] = {}
_quota_lock = threading.Lock()


def _mark_quota_exhausted(model: str, retry_after_s: float) -> None:
    with _quota_lock:
        _quota_exhausted_until[model] = time.time() + retry_after_s


def _is_quota_exhausted(model: str) -> bool:
    with _quota_lock:
        until = _quota_exhausted_until.get(model, 0.0)
    return time.time() < until


class Embedder:
    """VNG MaaS embeddings client (baai/bge-m3, 1024-dim).

    Keeps the same public interface as the previous OpenAI implementation so
    all callers (FaissRetriever, OpenSearchRetriever, OpenSearchIndexBuilder)
    work unchanged.
    """

    def __init__(
        self,
        model_name: str,
        *,
        base_url: str = "",
        api_key: str = "",
        cache_dir=None,   # unused — kept for call-site compatibility
    ) -> None:
        self._primary = model_name
        self._base_url = (base_url or "").rstrip("/")
        self._api_key = api_key
        self._http = httpx.Client(timeout=60.0)
        self._models_cache: list[str] = []
        self._models_cache_ts: float = 0.0
        self._models_cache_lock = threading.Lock()

    @property
    def dimension(self) -> int:
        return _MODEL_DIMS.get(self._primary, _DEFAULT_DIM)

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
        model = self._pick_model()

        @retry(
            stop=stop_after_attempt(_MAX_ATTEMPTS),
            wait=wait_exponential(multiplier=0.5, max=8),
            retry=retry_if_exception(lambda e: isinstance(e, (httpx.TimeoutException, httpx.NetworkError))),
            reraise=True,
        )
        def _call() -> list[list[float]]:
            url = f"{self._base_url}/embeddings"
            headers: dict[str, str] = {"Content-Type": "application/json"}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            payload = {"model": model, "input": texts, "encoding_format": "dense"}
            resp = self._http.post(url, json=payload, headers=headers)
            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", "0"))
                if retry_after >= _DAILY_QUOTA_RETRY_AFTER_THRESHOLD:
                    _mark_quota_exhausted(model, retry_after)
                    logger.warning("Embedder: daily quota for %s exhausted, marking for %ds", model, int(retry_after))
                    raise EmbeddingUnavailable(f"Daily quota exhausted for {model}")
                raise httpx.TimeoutException(f"rate limited ({retry_after}s)", request=resp.request)
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]

        try:
            return _call()
        except EmbeddingUnavailable:
            # Try next available model
            fallback = self._next_model(exclude=model)
            if fallback and fallback != model:
                logger.info("Embedder: falling back from %s to %s", model, fallback)
                self._primary = fallback
                return self._encode_batch(texts)
            raise
        except Exception as exc:
            logger.error("Embedder model=%s request failed: %s", model, exc)
            raise EmbeddingUnavailable(str(exc)) from exc

    def _pick_model(self) -> str:
        if not _is_quota_exhausted(self._primary):
            return self._primary
        fallback = self._next_model(exclude=self._primary)
        return fallback or self._primary

    def _fetch_embedding_models(self) -> list[str]:
        """Fetch available embedding models from MaaS catalogue (cached 10 min)."""
        now = time.time()
        with self._models_cache_lock:
            if self._models_cache and now - self._models_cache_ts < _MODELS_CACHE_TTL:
                return list(self._models_cache)
        try:
            url = f"{self._base_url}/models"
            headers: dict[str, str] = {}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            resp = self._http.get(url, headers=headers, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            models = [
                m["id"]
                for m in data.get("data", [])
                if m.get("model_type") == "embedding" and m.get("status") == "enabled"
            ]
        except Exception as exc:
            logger.warning("Embedder: failed to fetch model catalogue: %s", exc)
            models = [self._primary]
        with self._models_cache_lock:
            self._models_cache = models
            self._models_cache_ts = time.time()
        return models

    def _next_model(self, *, exclude: Optional[str] = None) -> Optional[str]:
        models = self._fetch_embedding_models()
        for m in models:
            if m != exclude and not _is_quota_exhausted(m):
                return m
        return None


def make_embedder(settings) -> "Embedder":
    """Factory: build Embedder with the right credentials for the configured model.

    MaaS models (baai/bge-m3, etc.) → llm_base_url + effective_llm_api_key.
      On AgentBase, effective_llm_api_key falls back to GREENNODE_API_KEY automatically.
    OpenAI models (text-embedding-*) → openai_base_url + openai_api_key.
    """
    model = settings.embedding_model
    if model.startswith("text-embedding-"):
        base_url = (settings.openai_base_url or "").rstrip("/")
        api_key = (settings.openai_api_key or "").strip()
    else:
        base_url = (settings.llm_base_url or "").rstrip("/")
        api_key = settings.effective_llm_api_key
    return Embedder(model, base_url=base_url, api_key=api_key)
