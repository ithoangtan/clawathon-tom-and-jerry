from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import faiss
import numpy as np
import pytest

from app.common.departments import DepartmentKey
from app.config import Settings
from app.store.meta import MetaStore

# FAISS partition files use string keys (``risk.faiss``), not enum reprs.
RISK_DEPT = DepartmentKey.RISK.value


@pytest.fixture
def adapter_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    """Minimal settings pointing at a writable temp index directory."""
    index_dir = tmp_path / "index"
    index_dir.mkdir(exist_ok=True)
    settings = Settings(
        app_env="local",
        index_dir=str(index_dir),
        embedding_model="test-model",
        llm_api_key="test-key",
        small_model="small-test",
        main_model="main-test",
        log_level="error",
    )
    monkeypatch.setenv("INDEX_DIR", str(index_dir))
    monkeypatch.setenv("APP_ENV", "local")
    return settings


@pytest.fixture
def meta_store(adapter_settings: Settings) -> MetaStore:
    """Empty MetaStore bound to the adapter settings index dir."""
    store = MetaStore(Path(adapter_settings.index_dir) / "meta.db")
    store.ensure_schema()
    return store


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (vectors / norms).astype(np.float32)


@pytest.fixture
def faiss_index_dir(adapter_settings: Settings) -> Path:
    """Directory containing a single ``risk`` FAISS partition (dim=4)."""
    faiss_dir = Path(adapter_settings.index_dir) / "faiss"
    faiss_dir.mkdir(parents=True, exist_ok=True)
    return faiss_dir


@pytest.fixture
def sample_vectors() -> np.ndarray:
    """Three L2-normalized vectors for a tiny IndexFlatIP (dim=4)."""
    raw = np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.99, 0.01, 0.0, 0.0],
            [0.98, 0.02, 0.0, 0.0],
        ],
        dtype=np.float32,
    )
    return _normalize(raw)


@pytest.fixture
def risk_faiss_index(faiss_index_dir: Path, sample_vectors: np.ndarray) -> Path:
    """Write ``risk.faiss`` with three vectors."""
    dim = sample_vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(sample_vectors)
    path = faiss_index_dir / f"{RISK_DEPT}.faiss"
    faiss.write_index(index, str(path))
    return path


@pytest.fixture
def risk_meta_rows() -> list[dict[str, Any]]:
    """Chunk metadata aligned with :func:`sample_vectors` row positions."""
    return [
        {
            "chunk_id": "chunk-active-0",
            "department": RISK_DEPT,
            "vec_pos": 0,
            "doc_type": "policy",
            "title": "Active doc A",
            "url": "https://example.com/a",
            "section": "Intro",
            "last_modified": "2024-01-01T00:00:00Z",
            "lifecycle_state": "active",
            "source_type": "confluence",
            "page": None,
            "text": "Active chunk at position 0",
        },
        {
            "chunk_id": "chunk-sunset-1",
            "department": RISK_DEPT,
            "vec_pos": 1,
            "doc_type": "policy",
            "title": "Sunset doc",
            "url": "https://example.com/sunset",
            "section": None,
            "last_modified": "2023-01-01T00:00:00Z",
            "lifecycle_state": "sunset",
            "source_type": "confluence",
            "page": None,
            "text": "Sunset chunk at position 1",
        },
        {
            "chunk_id": "chunk-active-2",
            "department": RISK_DEPT,
            "vec_pos": 2,
            "doc_type": "runbook",
            "title": "Active doc B",
            "url": "https://example.com/b",
            "section": "Steps",
            "last_modified": "2024-06-01T00:00:00Z",
            "lifecycle_state": "active",
            "source_type": "confluence",
            "page": None,
            "text": "Active chunk at position 2",
        },
    ]


@pytest.fixture
def populated_index(
    meta_store: MetaStore,
    risk_faiss_index: Path,
    risk_meta_rows: list[dict[str, Any]],
) -> MetaStore:
    """FAISS partition + meta rows for the risk department."""
    meta_store.replace_department_chunks(RISK_DEPT, risk_meta_rows)
    return meta_store


@pytest.fixture
def mock_embedder_query_vector(sample_vectors: np.ndarray) -> np.ndarray:
    """Query vector that ranks sample_vectors in index order (0, 1, 2)."""
    return sample_vectors[0].copy()


@pytest.fixture
def mock_embedder(mock_embedder_query_vector: np.ndarray) -> MagicMock:
    """Fake :class:`Embedder` returning a fixed query vector (dim=4)."""
    embedder = MagicMock()
    embedder.dimension = mock_embedder_query_vector.shape[0]
    embedder.encode_query.return_value = mock_embedder_query_vector
    return embedder


@pytest.fixture
def empty_faiss_index(faiss_index_dir: Path) -> Path:
    """Write an empty ``risk.faiss`` partition (ntotal=0)."""
    index = faiss.IndexFlatIP(4)
    path = faiss_index_dir / f"{RISK_DEPT}.faiss"
    faiss.write_index(index, str(path))
    return path
