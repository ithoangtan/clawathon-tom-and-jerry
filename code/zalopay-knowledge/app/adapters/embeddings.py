from __future__ import annotations

"""Embedder — calls VNG MaaS embeddings API (baai/bge-m3, hosted).

Uses the same endpoint and API key as the LLM adapter. No local model
download, no hf-cache, no sentence_transformers dependency.

bge-m3 does not use query/passage prefixes (those are for intfloat/e5).
"""

import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

_BGE_M3_DIM = 1024
_BATCH_SIZE = 64


class Embedder:
    """Calls the MaaS embeddings endpoint for bge-m3 dense vectors."""

    def __init__(
        self,
        model_name: str,
        *,
        base_url: str = "",
        api_key: str = "",
        cache_dir: str | Path | None = None,  # kept for API compat, unused
    ) -> None:
        self._model_name = model_name
        self._base_url = (base_url or "").rstrip("/")
        self._api_key = api_key

    @property
    def dimension(self) -> int:
        return _BGE_M3_DIM

    def encode_query(self, text: str) -> np.ndarray:
        """Embed a single query. Returns shape (dim,)."""
        return self._encode([text])[0]

    def encode_passages(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of passages. Returns shape (len(texts), dim)."""
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)
        return self._encode(texts)

    def _encode(self, texts: list[str]) -> np.ndarray:
        """POST to /v1/embeddings in batches, return float32 matrix."""
        import httpx

        url = f"{self._base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        all_vecs: list[list[float]] = []
        for i in range(0, len(texts), _BATCH_SIZE):
            batch = texts[i : i + _BATCH_SIZE]
            payload: dict[str, Any] = {
                "model": self._model_name,
                "input": batch,
                "encoding_format": "dense",
            }
            resp = httpx.post(url, json=payload, headers=headers, timeout=60.0)
            resp.raise_for_status()
            data = resp.json()
            batch_vecs = [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
            all_vecs.extend(batch_vecs)

        mat = np.asarray(all_vecs, dtype=np.float32)
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        return mat / norms
