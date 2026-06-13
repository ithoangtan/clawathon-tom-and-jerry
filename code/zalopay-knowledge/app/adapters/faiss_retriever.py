from __future__ import annotations

"""FaissRetriever — the local (MVP) :class:`RetrieverPort` implementation.

Per 03-ARCHITECTURE.md §5 the corpus index is **pre-built by the sync job and
loaded at boot — never built per request**.  This adapter therefore loads every
available ``faiss/{department}.faiss`` partition once at construction and keeps
the FAISS indexes in memory for the process lifetime.

Search flow for one department branch:

1. encode the query locally with the E5 ``"query: "`` prefix (zero MaaS tokens),
2. inner-product search the department's partition for ``k + buffer`` rows,
3. resolve row positions → chunk metadata via :class:`MetaStore`,
4. drop ``sunset`` chunks, keep ``deprecated`` (tagged for staleness warnings),
5. return the top ``k`` :class:`RetrievedChunk` sorted by descending score.

A future managed-vector-DB adapter can replace this class wholesale without any
node change, because nodes only ever call the :class:`RetrieverPort` Protocol.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from app.adapters.embeddings import Embedder
from app.common.departments import iter_keys
from app.config import Settings, get_settings
from app.ports.errors import RetrieverUnavailable
from app.ports.types import RetrievedChunk
from app.store.meta import MetaStore

if TYPE_CHECKING:  # keep faiss out of the import path until construction
    import faiss

logger = logging.getLogger(__name__)

# Extra rows to over-fetch from FAISS so that excluding ``sunset`` chunks still
# leaves at least ``k`` results in the common case.
_SUNSET_OVERFETCH = 10


class FaissRetriever:
    """Department-partitioned FAISS retriever backed by a local SQLite meta DB."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Load all available FAISS partitions and bind the metadata store.

        Missing partitions are tolerated: a department with no ``.faiss`` file
        is simply absent from :attr:`_indexes`, and :meth:`search` raises
        :class:`RetrieverUnavailable` for it (the ``retrieve`` node degrades to
        an empty chunk list for that branch only).
        """
        self._cfg = settings or get_settings()
        index_dir = Path(self._cfg.index_dir)

        self._embedder = Embedder(
            self._cfg.embedding_model, cache_dir=index_dir / "hf-cache"
        )
        self._meta = MetaStore(index_dir / "meta.db")
        self._faiss_dir = index_dir / "faiss"
        self._indexes: dict[str, "faiss.Index"] = self._load_partitions()

    # ── Boot-time partition loading ───────────────────────────────────────────

    def _load_partitions(self) -> dict[str, "faiss.Index"]:
        """Read every ``faiss/{dept}.faiss`` partition that exists on disk."""
        indexes: dict[str, "faiss.Index"] = {}
        if not self._faiss_dir.is_dir():
            logger.warning(
                "FAISS dir %s does not exist — retriever will report not-ready",
                self._faiss_dir,
            )
            return indexes

        import faiss

        for dept in iter_keys():
            path = self._faiss_dir / f"{dept}.faiss"
            if not path.exists():
                continue
            try:
                indexes[dept] = faiss.read_index(str(path))
                logger.info(
                    "Loaded FAISS partition %s (%d vectors)",
                    dept,
                    indexes[dept].ntotal,
                )
            except Exception as exc:  # noqa: BLE001 — one bad partition shouldn't kill boot
                logger.error("Failed to load FAISS partition %s: %s", path, exc)
        return indexes

    # ── RetrieverPort ─────────────────────────────────────────────────────────

    def search(
        self,
        *,
        department: str,
        query: str,
        k: int = 8,
        language: str = "en",
    ) -> list[RetrievedChunk]:
        """Retrieve the top-*k* non-sunset chunks for *query* from *department*."""
        index = self._indexes.get(department)
        if index is None or index.ntotal == 0:
            raise RetrieverUnavailable(department)

        if not query.strip():
            return []

        # 1–2. encode + search (over-fetch to survive sunset filtering).
        qvec = self._embedder.encode_query(query).reshape(1, -1)
        fetch = min(k + _SUNSET_OVERFETCH, index.ntotal)
        scores, positions = index.search(qvec, fetch)
        scores, positions = scores[0], positions[0]

        # 3. resolve positions → metadata in one batch.
        valid_positions = [int(p) for p in positions if p >= 0]
        meta = self._meta.fetch_by_positions(department, valid_positions)

        # 4. assemble, skip sunset, keep order by score (FAISS already sorted).
        results: list[RetrievedChunk] = []
        for pos, score in zip(positions, scores):
            pos = int(pos)
            if pos < 0:
                continue
            row = meta.get(pos)
            if row is None:
                continue  # stale index entry referencing a deleted chunk
            if row.get("lifecycle_state") == "sunset":
                continue
            results.append(self._to_chunk(row, department, float(score)))
            if len(results) >= k:
                break

        logger.info(
            "FAISS search[%s]: %d/%d returned (lang=%s)",
            department,
            len(results),
            fetch,
            language,
        )
        return results

    def is_ready(self) -> bool:
        """True when ≥1 partition is loaded and the metadata DB has chunks."""
        try:
            return bool(self._indexes) and self._meta.exists()
        except Exception:  # noqa: BLE001 — health check must never raise
            return False

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _to_chunk(row: dict, department: str, raw_score: float) -> RetrievedChunk:
        """Build a :class:`RetrievedChunk` from a meta row + FAISS score.

        Cosine similarity from L2-normalized vectors lands in ``[-1, 1]``; we
        clamp to ``[0, 1]`` to match the port's documented score range.
        """
        page = row.get("page")
        return RetrievedChunk(
            chunk_id=row["chunk_id"],
            department=row.get("department") or department,
            doc_type=row.get("doc_type") or "",
            title=row.get("title") or "",
            url=row.get("url") or "",
            section=row.get("section"),
            last_modified=row.get("last_modified"),
            lifecycle_state=row.get("lifecycle_state") or "active",
            source_type=row.get("source_type") or "confluence",
            page=int(page) if page is not None else None,
            text=row.get("text") or "",
            score=max(0.0, min(1.0, raw_score)),
        )
