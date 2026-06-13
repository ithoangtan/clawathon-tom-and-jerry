from __future__ import annotations

from unittest.mock import MagicMock, patch

import faiss
import pytest

from app.config import Settings
from app.store.meta import MetaStore
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


def test_atomic_faiss_swap_uses_temp_then_replace(
    faiss_index_dir,
    sample_chunks,
    mock_encode_passages,
    index_builder_cls,
):
    IndexBuilder = index_builder_cls
    settings = Settings(index_dir=str(faiss_index_dir))
    builder = IndexBuilder(settings)
    final_path = faiss_index_dir / "faiss" / "risk.faiss"

    with (
        patch.object(builder._embedder, "encode_passages", side_effect=mock_encode_passages),
        patch("app.ingestion.indexer.os.replace") as mock_replace,
        patch("app.ingestion.indexer.faiss.write_index") as mock_write,
    ):
        builder.rebuild_department(RISK, [dict(c) for c in sample_chunks])

    mock_write.assert_called_once()
    tmp_path = mock_write.call_args[0][1]
    assert str(tmp_path).endswith(".faiss.tmp")
    mock_replace.assert_called_once_with(tmp_path, str(final_path))


def test_rebuild_never_leaves_tmp_on_success(
    faiss_index_dir,
    sample_chunks,
    mock_encode_passages,
    index_builder_cls,
):
    IndexBuilder = index_builder_cls
    settings = Settings(index_dir=str(faiss_index_dir))
    builder = IndexBuilder(settings)

    with patch.object(builder._embedder, "encode_passages", side_effect=mock_encode_passages):
        builder.rebuild_department(RISK, [dict(c) for c in sample_chunks])

    faiss_dir = faiss_index_dir / "faiss"
    tmp_files = list(faiss_dir.glob("*.faiss.tmp"))
    assert tmp_files == []
    assert (faiss_dir / "risk.faiss").exists()


def test_empty_rebuild_removes_partition_file(
    faiss_index_dir,
    sample_chunks,
    mock_encode_passages,
    index_builder_cls,
):
    IndexBuilder = index_builder_cls
    settings = Settings(index_dir=str(faiss_index_dir))
    builder = IndexBuilder(settings)

    with patch.object(builder._embedder, "encode_passages", side_effect=mock_encode_passages):
        builder.rebuild_department(RISK, [dict(c) for c in sample_chunks])

    assert (faiss_index_dir / "faiss" / "risk.faiss").exists()

    builder.rebuild_department(RISK, [])
    assert not (faiss_index_dir / "faiss" / "risk.faiss").exists()
    assert MetaStore(faiss_index_dir / "meta.db").count(RISK) == 0
