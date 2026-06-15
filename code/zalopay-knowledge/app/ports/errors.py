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


class JiraUnavailable(KnowledgeAgentError):
    """Raised by :class:`~app.ports.jira.JiraPort` when Jira is unreachable, the
    credentials are missing/invalid, or the API returns an error.

    Workflow-execution nodes catch this and degrade gracefully: the action step
    is reported as not-performed in the answer rather than failing the whole run.
    """

    def __init__(self, message: str = "Jira service is unavailable") -> None:
        super().__init__(message)


class ConfluenceUnavailable(KnowledgeAgentError):
    """Raised by the Confluence writer when a create/update/label call fails
    (transport, auth, or API error).

    Workflow trigger actions catch this and report the Confluence update as
    not-performed rather than failing the whole event handler.
    """

    def __init__(self, message: str = "Confluence write failed") -> None:
        super().__init__(message)


class WorkflowParseError(KnowledgeAgentError):
    """Raised by the workflow parser when an LLM response cannot be turned into a
    valid :class:`~app.workflow.models.WorkflowDefinition`.

    Causes: the model returned non-JSON, the JSON failed schema validation, or a
    required field (e.g. ``name``/``steps``) was missing.  The executor catches
    this and turns it into a graceful, cited refusal instead of crashing the run.
    """

    def __init__(self, message: str = "Could not parse the workflow definition") -> None:
        super().__init__(message)
