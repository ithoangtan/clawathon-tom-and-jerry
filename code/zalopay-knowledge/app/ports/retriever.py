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
        filters: dict[str, list[str]] | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve the top-*k* chunks for *query* from *department*'s partition.

        Args:
            department: Canonical department key (see ``app.common.departments`` registry).
            query: Natural-language question string (NOT yet prefixed with
                   ``query: `` — the adapter handles that).
            k: Maximum number of chunks to return.  May return fewer when the
               partition has less than *k* indexed chunks.
            language: ISO-639-1 language hint (``"en"`` or ``"vi"``).  Passed
                      to the adapter for future language-specific re-ranking;
                      currently informational.
            filters: Optional metadata constraints applied *before* ranking.
                     Maps a field name to a list of accepted values. Constraints
                     across fields are AND-ed.  Semantics per field:

                     - ``"labels"``: the chunk must carry **all** listed labels
                       (AND) — e.g. ``{"labels": ["zalopay-workflow", "status:active"]}``
                       only matches chunks tagged with both. Labels are stored as
                       a JSON string, so adapters match against that encoding.
                     - any other field (``"space"``, ``"lifecycle_state"``,
                       ``"source"``, ...): the chunk's value must be **one of**
                       the listed values (OR within the field).

                     ``None`` (the default) means no filtering — identical to the
                     pre-existing behaviour.

        Returns:
            List of :class:`~app.ports.types.RetrievedChunk` sorted by
            ``score`` descending; ``sunset`` chunks excluded; ``deprecated``
            chunks included with ``lifecycle_state="deprecated"``.
        """
        ...

    def get_page_chunks(
        self,
        *,
        department: str,
        page_id: str,
    ) -> list[RetrievedChunk]:
        """Return **all** chunks of a single source document, in page order.

        Exact-match lookup by upstream document id (``source`` field) — not a
        semantic search.  Used to reconstruct a full Confluence page (e.g. a
        workflow definition) for downstream parsing.

        Args:
            department: Canonical department key the page lives in.
            page_id: Upstream document id (Confluence page id) — matched against
                     each chunk's ``source`` field.

        Returns:
            All non-``sunset`` chunks whose ``source == page_id``, ordered by
            their position in the original document (so concatenating ``text``
            reconstructs the page).  Empty list when the page is not indexed.
            ``score`` is not meaningful here and is set to ``1.0``.
        """
        ...

    def is_ready(self) -> bool:
        """Return True when the index for at least one department is available.

        Used by the ``/health`` endpoint and the ``ingest_context`` node to
        decide whether to serve a "knowledge base unavailable" refusal.
        """
        ...
