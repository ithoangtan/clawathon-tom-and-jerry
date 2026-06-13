from __future__ import annotations

"""CheckpointerPort — the frozen interface for LangGraph checkpoint persistence.

Local: SqliteSaver (langgraph-checkpoint-sqlite).
AgentBase: AgentBaseMemoryEvents saver (injected by greennode-agent-bridge).

Swapping between them is a one-line change in deps.py — all graph code calls
only this port.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class CheckpointerPort(Protocol):
    """Provider of a LangGraph-compatible checkpoint saver.

    The saver returned by ``get_saver()`` must implement the
    ``langgraph.checkpoint.base.BaseCheckpointSaver`` interface so it can be
    passed directly to ``graph.compile(checkpointer=...)``.
    """

    def get_saver(self):
        """Return a LangGraph ``BaseCheckpointSaver`` instance.

        The returned object must be safe to pass as the ``checkpointer``
        argument to ``StateGraph.compile()``.

        Returns:
            A ``BaseCheckpointSaver`` implementation (SqliteSaver locally,
            AgentBaseMemoryEvents on the platform).
        """
        ...

    def healthy(self) -> bool:
        """Return True when the underlying storage is reachable and writable.

        Used by the ``/health`` endpoint.  Should not raise — return False
        on any error instead.
        """
        ...
