from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import faiss
import numpy as np
import pytest

from app.adapters.faiss_retriever import FaissRetriever
from app.config import Settings
from app.ports.errors import RetrieverUnavailable
from app.store.meta import MetaStore

from tests.unit.adapters.conftest import RISK_DEPT


def _make_retriever(
    settings: Settings,
    embedder: MagicMock | None = None,
) -> FaissRetriever:
    with patch("app.adapters.faiss_retriever.Embedder") as mock_cls:
        mock_cls.return_value = embedder or MagicMock()
        return FaissRetriever(settings)


def test_search_returns_ranked_chunks(
    adapter_settings: Settings,
    populated_index: MetaStore,
    mock_embedder: MagicMock,
) -> None:
    retriever = _make_retriever(adapter_settings, mock_embedder)

    results = retriever.search(
        department=RISK_DEPT,
        query="policy question",
        k=2,
    )

    assert len(results) == 2
    assert results[0].chunk_id == "chunk-active-0"
    assert results[1].chunk_id == "chunk-active-2"
    assert all(r.lifecycle_state != "sunset" for r in results)
    assert all(0.0 <= r.score <= 1.0 for r in results)
    mock_embedder.encode_query.assert_called_once_with("policy question")


def test_search_filters_sunset_chunks(
    adapter_settings: Settings,
    populated_index: MetaStore,
    mock_embedder: MagicMock,
) -> None:
    """Sunset chunk at position 1 is skipped even though it ranks highly."""
    retriever = _make_retriever(adapter_settings, mock_embedder)

    results = retriever.search(
        department=RISK_DEPT,
        query="policy question",
        k=3,
    )

    chunk_ids = [r.chunk_id for r in results]
    assert "chunk-sunset-1" not in chunk_ids
    assert chunk_ids == ["chunk-active-0", "chunk-active-2"]


def test_search_empty_query_returns_empty_list(
    adapter_settings: Settings,
    populated_index: MetaStore,
    mock_embedder: MagicMock,
) -> None:
    retriever = _make_retriever(adapter_settings, mock_embedder)

    assert retriever.search(department=RISK_DEPT, query="   ", k=5) == []
    mock_embedder.encode_query.assert_not_called()


def test_search_missing_partition_raises(
    adapter_settings: Settings,
    mock_embedder: MagicMock,
) -> None:
    retriever = _make_retriever(adapter_settings, mock_embedder)

    with pytest.raises(RetrieverUnavailable) as exc_info:
        retriever.search(department=RISK_DEPT, query="hello", k=3)

    assert exc_info.value.department == RISK_DEPT


def test_search_empty_index_raises(
    adapter_settings: Settings,
    empty_faiss_index: Path,
    mock_embedder: MagicMock,
) -> None:
    retriever = _make_retriever(adapter_settings, mock_embedder)

    with pytest.raises(RetrieverUnavailable):
        retriever.search(department=RISK_DEPT, query="hello", k=3)


def test_is_ready_false_without_partitions(adapter_settings: Settings) -> None:
    retriever = _make_retriever(adapter_settings)

    assert retriever.is_ready() is False


def test_is_ready_true_with_index_and_meta(
    adapter_settings: Settings,
    populated_index: MetaStore,
    mock_embedder: MagicMock,
) -> None:
    retriever = _make_retriever(adapter_settings, mock_embedder)

    assert retriever.is_ready() is True


def test_reload_picks_up_new_partition(
    adapter_settings: Settings,
    faiss_index_dir: Path,
    mock_embedder: MagicMock,
) -> None:
    retriever = _make_retriever(adapter_settings, mock_embedder)
    assert RISK_DEPT not in retriever._indexes

    index = faiss.IndexFlatIP(4)
    faiss.write_index(index, str(faiss_index_dir / f"{RISK_DEPT}.faiss"))

    retriever.reload()
    assert RISK_DEPT in retriever._indexes


def test_load_skips_inconsistent_faiss_meta_partition(
    adapter_settings: Settings,
    faiss_index_dir: Path,
    populated_index: MetaStore,
    mock_embedder: MagicMock,
) -> None:
    """Half-built swap: mismatched ntotal vs meta count must not be served."""
    index = faiss.IndexFlatIP(4)
    # populated_index fixture seeds 3 meta rows; write only 1 vector on disk.
    index.add(np.zeros((1, 4), dtype=np.float32))
    faiss.write_index(index, str(faiss_index_dir / f"{RISK_DEPT}.faiss"))

    retriever = _make_retriever(adapter_settings, mock_embedder)

    assert RISK_DEPT not in retriever._indexes
    assert retriever.is_ready() is False
