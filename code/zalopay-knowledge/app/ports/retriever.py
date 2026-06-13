from __future__ import annotations

"""RetrieverPort — the frozen interface for vector-search retrieval.

Graph nodes call ``search()`` to fetch evidence chunks for a department.
The FAISS adapter implements this; a future adapter could swap to a managed
vector DB without touching any node code.
"""

from typing import Protocol, runtime_checkable

from app.ports.types import RetrievedChunk


@runtime_checkable
class RetrieverPort(Protocol):
    """Department-scoped vector retrieval interface.

    The retriever is responsible for:
    - Encoding the query with the correct ``query: `` prefix.
    - Filtering out ``sunset`` lifecycle chunks before returning.
    - Tagging ``deprecated`` chunks (so nodes can add staleness warnings).
    - Returning chunks sorted by descending relevance score.

    Raises:
        app.ports.errors.RetrieverUnavailable: when the index is not yet built
            or is corrupt.  Callers should treat this as a refusal signal.
    """

    def search(
        self,
        *,
        department: str,
        query: str,
        k: int = 8,
        language: str = "en",
    ) -> list[RetrievedChunk]:
        """Retrieve the top-*k* chunks for *query* from *department*'s partition.

        Args:
            department: Canonical department key (``risk`` / ``grow_enablement``
                        / ``bank_partnerships``).
            query: Natural-language question string (NOT yet prefixed with
                   ``query: `` — the adapter handles that).
            k: Maximum number of chunks to return.  May return fewer when the
               partition has less than *k* indexed chunks.
            language: ISO-639-1 language hint (``"en"`` or ``"vi"``).  Passed
                      to the adapter for future language-specific re-ranking;
                      currently informational.

        Returns:
            List of :class:`~app.ports.types.RetrievedChunk` sorted by
            ``score`` descending; ``sunset`` chunks excluded; ``deprecated``
            chunks included with ``lifecycle_state="deprecated"``.
        """
        ...

    def is_ready(self) -> bool:
        """Return True when the index for at least one department is available.

        Used by the ``/health`` endpoint and the ``ingest_context`` node to
        decide whether to serve a "knowledge base unavailable" refusal.
        """
        ...
