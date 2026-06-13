from __future__ import annotations

"""AgentBaseCheckpointer — the platform :class:`CheckpointerPort` implementation.

On GreenNode AgentBase, conversation state is persisted by the platform's
Memory service rather than a local SQLite file.  The bridge package
``greennode-agent-bridge[langgraph]`` ships ``AgentBaseMemoryEvents``, a
``BaseCheckpointSaver`` that records STM events against the configured Memory
store (03-ARCHITECTURE.md §3).  Swapping local→platform is a one-line change in
deps.py — graph code only ever sees :class:`CheckpointerPort`.

This package is **only installed at deploy time** (added by the AgentBase
deployment pipeline, never locally — see requirements.txt), so every reference
to it is lazily imported.  Importing this module is therefore always safe; the
bridge is only touched when ``get_saver()`` is actually called on the platform.

NOTE: confirm the exact ``AgentBaseMemoryEvents`` import path and constructor
signature against the installed bridge version during ``preflight`` — the
platform owns that contract.
"""

import logging

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class AgentBaseCheckpointer:
    """Provides the platform-backed ``AgentBaseMemoryEvents`` saver."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._cfg = settings or get_settings()
        self._saver = None

    def get_saver(self):
        """Return a cached ``AgentBaseMemoryEvents`` saver (lazy-imported)."""
        if self._saver is not None:
            return self._saver

        try:
            from greennode_agent_bridge.langgraph import AgentBaseMemoryEvents
        except ImportError as exc:  # pragma: no cover — only on misconfigured deploys
            raise RuntimeError(
                "greennode-agent-bridge[langgraph] is not installed. It is added "
                "by the AgentBase deployment pipeline; AgentBaseCheckpointer must "
                "not be used in a local environment (set APP_ENV=local)."
            ) from exc

        # The Memory store id is injected by the platform into MEMORY_ID.
        self._saver = AgentBaseMemoryEvents(memory_id=self._cfg.memory_id)
        logger.info("AgentBaseMemoryEvents saver ready (memory_id set=%s)", bool(self._cfg.memory_id))
        return self._saver

    def healthy(self) -> bool:
        """Best-effort liveness: the saver can be constructed. Never raises."""
        try:
            self.get_saver()
            return True
        except Exception as exc:  # noqa: BLE001 — health check must not raise
            logger.warning("AgentBaseCheckpointer unhealthy: %s", exc)
            return False
