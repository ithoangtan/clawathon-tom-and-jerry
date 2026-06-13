from __future__ import annotations

"""LLMPort — the frozen interface for all LLM interactions.

Graph nodes import this Protocol and call ``complete()``.  Adapters implement it.
Swap local MaaS → AgentBase MaaS by registering a different adapter in deps.py.
"""

from typing import Literal, Protocol, runtime_checkable

from app.ports.types import LLMResult, ModelTier


@runtime_checkable
class LLMPort(Protocol):
    """Synchronous LLM completion interface.

    Implementations must be stateless and thread-safe (the same instance is
    shared across concurrent subgraph branches).

    Raises:
        app.ports.errors.LLMUnavailable: when the underlying model is
            unreachable after retries and no fallback is available.
    """

    def complete(
        self,
        *,
        tier: ModelTier,
        messages: list[dict],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        response_format: Literal["text", "json"] = "text",
        timeout_s: float | None = None,
    ) -> LLMResult:
        """Send *messages* to the model selected by *tier* and return the result.

        Args:
            tier: ``ModelTier.SMALL`` for routing/grading/verify;
                  ``ModelTier.MAIN`` for synthesis/reconcile.
            messages: OpenAI-style message list — each dict has ``role`` and
                      ``content`` keys at minimum.
            temperature: Sampling temperature (0.0 = deterministic / greedy).
            max_tokens: Hard token cap on the completion; None = model default.
            response_format: ``"json"`` instructs the model to return valid JSON
                             only (best-effort; adapter does one repair retry).
            timeout_s: Per-call wall-clock timeout in seconds.  None inherits
                       the adapter default.

        Returns:
            :class:`~app.ports.types.LLMResult` with text, raw response, usage
            counters, and a ``degraded`` flag when a retry/fallback was used.
        """
        ...
