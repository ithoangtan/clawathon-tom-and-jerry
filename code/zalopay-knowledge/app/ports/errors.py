from __future__ import annotations

"""Typed exceptions raised by port implementations.

Graph nodes catch these specific exceptions to apply graceful degradation
(refusal or partial answers) rather than letting raw HTTP/IO errors propagate
to the API layer.
"""


class KnowledgeAgentError(Exception):
    """Base class for all application-level errors."""


class LLMUnavailable(KnowledgeAgentError):
    """Raised by :class:`~app.ports.llm.LLMPort` when the model endpoint is
    unreachable after all retries, or when the API key is invalid.

    Handlers should degrade gracefully: emit a refusal response with a
    ``memory_degraded=True`` flag so the frontend can show a transient-error
    notice rather than a hard failure page.
    """

    def __init__(self, message: str = "LLM service is temporarily unavailable") -> None:
        super().__init__(message)


class RetrieverUnavailable(KnowledgeAgentError):
    """Raised by :class:`~app.ports.retriever.RetrieverPort` when the FAISS
    index has not been built yet or is corrupt.

    The ``ingest_context`` node should catch this and set
    ``status="refused"`` with a localised "knowledge base not ready" message
    instead of propagating a 500.
    """

    def __init__(
        self,
        department: str | None = None,
        message: str | None = None,
    ) -> None:
        dept_clause = f" for department '{department}'" if department else ""
        default_msg = f"Retrieval index is not available{dept_clause}"
        super().__init__(message or default_msg)
        self.department = department
