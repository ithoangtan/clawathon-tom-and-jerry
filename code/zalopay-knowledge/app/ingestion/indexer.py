from __future__ import annotations

"""FAISS partition builder — embeds chunks and writes index + meta rows."""

import logging
import os
import tempfile
from pathlib import Path

import faiss
import numpy as np

from app.adapters.embeddings import Embedder
from app.config import Settings, get_settings
from app.store.meta import MetaStore

logger = logging.getLogger(__name__)


class IndexBuilder:
    """Build or replace a department's FAISS partition from chunk dicts."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._cfg = settings or get_settings()
        index_dir = Path(self._cfg.index_dir)
        self._faiss_dir = index_dir / "faiss"
        self._faiss_dir.mkdir(parents=True, exist_ok=True)
        self._meta = MetaStore(index_dir / "meta.db")
        self._embedder = Embedder(
            self._cfg.embedding_model, cache_dir=index_dir / "hf-cache"
        )

    def rebuild_department(self, department: str, chunks: list[dict]) -> int:
        """Embed *chunks*, write FAISS + meta. Returns chunk count.

        Full-rebuild sync removes chunks for documents no longer present in
        *chunks* (hard delete).  Use :meth:`tombstone_removed_urls` before an
        incremental upsert when soft-delete tombstones are required.
        """
        if not chunks:
            self._meta.replace_department_chunks(department, [])
            self._remove_partition_file(department)
            return 0

        texts = [c["text"] for c in chunks]
        vectors = self._embedder.encode_passages(texts)
        dim = vectors.shape[1]

        index = faiss.IndexFlatIP(dim)
        index.add(vectors.astype(np.float32))

        for pos, chunk in enumerate(chunks):
            chunk["vec_pos"] = pos

        # Build offline, then swap atomically so reload never reads a half-written
        # FAISS file.  Meta commit follows the on-disk vector swap.
        self._atomic_write_faiss(department, index)
        self._meta.replace_department_chunks(department, chunks)
        logger.info("Indexed %d chunks for %s (dim=%d)", len(chunks), department, dim)
        return len(chunks)

    def _partition_path(self, department: str) -> Path:
        return self._faiss_dir / f"{department}.faiss"

    def _remove_partition_file(self, department: str) -> None:
        path = self._partition_path(department)
        if path.exists():
            path.unlink()

    def _atomic_write_faiss(self, department: str, index: faiss.Index) -> None:
        """Write *index* via a temp file and ``os.replace`` (POSIX atomic swap)."""
        self._faiss_dir.mkdir(parents=True, exist_ok=True)
        final_path = self._partition_path(department)
        fd, tmp_path = tempfile.mkstemp(
            suffix=".faiss.tmp",
            dir=self._faiss_dir,
            prefix=f"{department}.",
        )
        os.close(fd)
        try:
            faiss.write_index(index, tmp_path)
            os.replace(tmp_path, str(final_path))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def tombstone_removed_urls(
        self, department: str, active_urls: set[str]
    ) -> set[str]:
        """Mark indexed URLs absent from *active_urls* as sunset tombstones.

        Returns the set of URLs that were tombstoned.  A subsequent full
        ``rebuild_department`` will hard-delete them instead.
        """
        indexed = self._meta.distinct_urls(department)
        removed = indexed - active_urls
        if removed:
            count = self._meta.tombstone_urls(department, removed)
            logger.info(
                "Tombstoned %d chunk row(s) across %d removed URL(s) in %s",
                count,
                len(removed),
                department,
            )
        return removed

    def reload_retriever(self) -> None:
        """Ask the process-wide retriever to reload partitions (best-effort)."""
        try:
            from app.adapters.deps import get_deps

            retriever = get_deps().retriever
            if hasattr(retriever, "reload"):
                retriever.reload()
            elif hasattr(retriever, "_load_partitions"):
                retriever._indexes = retriever._load_partitions()  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not hot-reload retriever: %s", exc)
