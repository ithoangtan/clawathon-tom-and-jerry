from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import faiss

from app.config import Settings
from app.ingestion.metadata import REQUIRED_CHUNK_METADATA_FIELDS
from app.store.meta import MetaStore


class TestIndexBuilder:
    def test_rebuild_empty_department_clears_meta(
        self, faiss_index_dir: Path, index_builder_cls, mock_encode_passages
    ):
        IndexBuilder = index_builder_cls
        settings = Settings(index_dir=str(faiss_index_dir))
        builder = IndexBuilder(settings)
        meta = MetaStore(faiss_index_dir / "meta.db")

        with patch.object(builder._embedder, "encode_passages", side_effect=mock_encode_passages):
            builder.rebuild_department(
                "risk",
                [
                    {
                        "chunk_id": "risk-old-1",
                        "department": "risk",
                        "vec_pos": 0,
                        "doc_type": "Risk",
                        "title": "Old",
                        "source": "1",
                        "url": "u",
                        "anchor": None,
                        "section": None,
                        "space": "RISK",
                        "labels": "[]",
                        "last_modified": None,
                        "author": None,
                        "acl": '["all-employees"]',
                        "lifecycle_state": "active",
                        "source_type": "confluence",
                        "page": None,
                        "text": "old text",
                    }
                ],
            )
        assert meta.count("risk") == 1

        count = builder.rebuild_department("risk", [])
        assert count == 0
        assert meta.count("risk") == 0

    def test_faiss_write_read_round_trip(
        self,
        faiss_index_dir: Path,
        sample_chunks: list[dict],
        mock_encode_passages,
        mock_embedding_dim: int,
        index_builder_cls,
    ):
        IndexBuilder = index_builder_cls
        settings = Settings(index_dir=str(faiss_index_dir))
        builder = IndexBuilder(settings)

        with patch.object(builder._embedder, "encode_passages", side_effect=mock_encode_passages):
            count = builder.rebuild_department("risk", [dict(c) for c in sample_chunks])

        assert count == 2
        faiss_path = faiss_index_dir / "faiss" / "risk.faiss"
        assert faiss_path.exists()

        index = faiss.read_index(str(faiss_path))
        assert index.ntotal == 2
        assert index.d == mock_embedding_dim

        vectors = index.reconstruct_n(0, index.ntotal)
        assert vectors.shape == (2, mock_embedding_dim)

        meta = MetaStore(faiss_index_dir / "meta.db")
        assert meta.count("risk") == 2
        by_pos = meta.fetch_by_positions("risk", [0, 1])
        assert by_pos[0]["chunk_id"] == sample_chunks[0]["chunk_id"]
        assert by_pos[1]["text"] == sample_chunks[1]["text"]
        assert by_pos[0]["vec_pos"] == 0
        assert by_pos[1]["vec_pos"] == 1

    def test_rebuild_preserves_required_metadata_fields(
        self,
        faiss_index_dir: Path,
        sample_chunks: list[dict],
        mock_encode_passages,
        index_builder_cls,
    ):
        """Indexed rows must expose every checklist §4 metadata field."""
        IndexBuilder = index_builder_cls
        settings = Settings(index_dir=str(faiss_index_dir))
        builder = IndexBuilder(settings)

        with patch.object(builder._embedder, "encode_passages", side_effect=mock_encode_passages):
            builder.rebuild_department("risk", [dict(c) for c in sample_chunks])

        meta = MetaStore(faiss_index_dir / "meta.db")
        rows = meta.fetch_by_positions("risk", [0, 1])
        for row in rows.values():
            for field in REQUIRED_CHUNK_METADATA_FIELDS:
                assert field in row

    def test_vec_pos_assigned_sequentially(
        self,
        faiss_index_dir: Path,
        sample_chunks: list[dict],
        mock_encode_passages,
        index_builder_cls,
    ):
        IndexBuilder = index_builder_cls
        settings = Settings(index_dir=str(faiss_index_dir))
        builder = IndexBuilder(settings)
        chunks = [dict(c) for c in sample_chunks]

        with patch.object(builder._embedder, "encode_passages", side_effect=mock_encode_passages):
            builder.rebuild_department("risk", chunks)

        meta = MetaStore(faiss_index_dir / "meta.db")
        rows = meta.fetch_by_positions("risk", [0, 1])
        assert rows[0]["vec_pos"] == 0
        assert rows[1]["vec_pos"] == 1

    def test_reload_retriever_best_effort(self, faiss_index_dir: Path, index_builder_cls):
        IndexBuilder = index_builder_cls
        settings = Settings(index_dir=str(faiss_index_dir))
        builder = IndexBuilder(settings)
        mock_retriever = MagicMock()
        mock_retriever.reload = MagicMock()

        mock_deps = MagicMock()
        mock_deps.retriever = mock_retriever

        with patch("app.adapters.deps.get_deps", return_value=mock_deps):
            builder.reload_retriever()

        mock_retriever.reload.assert_called_once()

    def test_reload_retriever_swallows_errors(self, faiss_index_dir: Path, index_builder_cls):
        IndexBuilder = index_builder_cls
        settings = Settings(index_dir=str(faiss_index_dir))
        builder = IndexBuilder(settings)

        with patch("app.adapters.deps.get_deps", side_effect=RuntimeError("no deps")):
            builder.reload_retriever()  # should not raise

    def test_rebuild_replaces_prior_index(
        self,
        faiss_index_dir: Path,
        mock_encode_passages,
        index_builder_cls,
    ):
        IndexBuilder = index_builder_cls
        settings = Settings(index_dir=str(faiss_index_dir))
        builder = IndexBuilder(settings)

        def one_chunk(text: str) -> dict:
            return {
                "chunk_id": f"risk-{hash(text)}",
                "department": "risk",
                "vec_pos": 0,
                "doc_type": "Risk",
                "title": "T",
                "source": "1",
                "url": "u",
                "anchor": None,
                "section": None,
                "space": "RISK",
                "labels": "[]",
                "last_modified": None,
                "author": None,
                "acl": '["all-employees"]',
                "lifecycle_state": "active",
                "source_type": "confluence",
                "page": None,
                "text": text,
            }

        with patch.object(builder._embedder, "encode_passages", side_effect=mock_encode_passages):
            builder.rebuild_department("risk", [one_chunk("first")])
            builder.rebuild_department("risk", [one_chunk("second"), one_chunk("third")])

        index = faiss.read_index(str(faiss_index_dir / "faiss" / "risk.faiss"))
        assert index.ntotal == 2
        meta = MetaStore(faiss_index_dir / "meta.db")
        assert meta.count("risk") == 2

    def test_tombstone_removed_urls_marks_absent_urls(
        self,
        faiss_index_dir: Path,
        sample_chunks: list[dict],
        mock_encode_passages,
        index_builder_cls,
    ):
        IndexBuilder = index_builder_cls
        settings = Settings(index_dir=str(faiss_index_dir))
        builder = IndexBuilder(settings)

        with patch.object(builder._embedder, "encode_passages", side_effect=mock_encode_passages):
            builder.rebuild_department("risk", [dict(c) for c in sample_chunks])

        removed = builder.tombstone_removed_urls(
            "risk", {"https://acme.atlassian.net/wiki/spaces/RISK/pages/1"}
        )
        assert removed == set()

        removed = builder.tombstone_removed_urls("risk", set())
        assert removed == {"https://acme.atlassian.net/wiki/spaces/RISK/pages/1"}

        meta = MetaStore(faiss_index_dir / "meta.db")
        rows = meta.fetch_by_positions("risk", [0, 1])
        assert all(r["lifecycle_state"] == "sunset" for r in rows.values())
