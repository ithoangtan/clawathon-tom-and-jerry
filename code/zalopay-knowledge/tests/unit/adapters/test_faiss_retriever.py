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


def test_search_label_filter_keeps_only_matching(
    adapter_settings: Settings,
    populated_index: MetaStore,
    mock_embedder: MagicMock,
) -> None:
    retriever = _make_retriever(adapter_settings, mock_embedder)

    results = retriever.search(
        department=RISK_DEPT,
        query="policy question",
        k=5,
        filters={"labels": ["runbook"]},
    )

    assert [r.chunk_id for r in results] == ["chunk-active-2"]


def test_search_label_filter_is_and_across_labels(
    adapter_settings: Settings,
    populated_index: MetaStore,
    mock_embedder: MagicMock,
) -> None:
    """No chunk carries both labels, so the AND filter returns nothing."""
    retriever = _make_retriever(adapter_settings, mock_embedder)

    results = retriever.search(
        department=RISK_DEPT,
        query="policy question",
        k=5,
        filters={"labels": ["policy", "runbook"]},
    )

    assert results == []


def test_search_non_label_field_filter_is_or(
    adapter_settings: Settings,
    populated_index: MetaStore,
    mock_embedder: MagicMock,
) -> None:
    retriever = _make_retriever(adapter_settings, mock_embedder)

    results = retriever.search(
        department=RISK_DEPT,
        query="policy question",
        k=5,
        filters={"doc_type": ["Operation", "Security"]},
    )

    assert [r.chunk_id for r in results] == ["chunk-active-2"]


def test_get_page_chunks_returns_only_that_page(
    adapter_settings: Settings,
    populated_index: MetaStore,
    mock_embedder: MagicMock,
) -> None:
    retriever = _make_retriever(adapter_settings, mock_embedder)

    results = retriever.get_page_chunks(department=RISK_DEPT, page_id="page-a")

    assert [r.chunk_id for r in results] == ["chunk-active-0"]
    assert all(r.score == 1.0 for r in results)


def test_get_page_chunks_excludes_sunset(
    adapter_settings: Settings,
    populated_index: MetaStore,
    mock_embedder: MagicMock,
) -> None:
    retriever = _make_retriever(adapter_settings, mock_embedder)

    assert retriever.get_page_chunks(department=RISK_DEPT, page_id="page-sunset") == []


def test_get_page_chunks_orders_by_position(
    adapter_settings: Settings,
    meta_store: MetaStore,
    mock_embedder: MagicMock,
) -> None:
    """Chunks of one page are returned in document (vec_pos) order, not insert order."""
    rows = [
        {
            "chunk_id": "m-2", "department": "grow_enablement", "vec_pos": 2,
            "doc_type": "Operation", "title": "WF", "source": "page-multi",
            "url": "https://x/wf", "anchor": None, "section": "Step 2", "space": "WF",
            "labels": "[]", "last_modified": None, "author": None,
            "acl": '["all-employees"]', "lifecycle_state": "active",
            "source_type": "confluence", "page": None, "text": "second",
        },
        {
            "chunk_id": "m-0", "department": "grow_enablement", "vec_pos": 0,
            "doc_type": "Operation", "title": "WF", "source": "page-multi",
            "url": "https://x/wf", "anchor": None, "section": "Step 1", "space": "WF",
            "labels": "[]", "last_modified": None, "author": None,
            "acl": '["all-employees"]', "lifecycle_state": "active",
            "source_type": "confluence", "page": None, "text": "first",
        },
    ]
    meta_store.replace_department_chunks("grow_enablement", rows)
    retriever = _make_retriever(adapter_settings, mock_embedder)

    results = retriever.get_page_chunks(department="grow_enablement", page_id="page-multi")

    assert [r.chunk_id for r in results] == ["m-0", "m-2"]
    assert " ".join(r.text for r in results) == "first second"


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
