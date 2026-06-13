from __future__ import annotations

"""AgentBase STM/LTM recall — builds the ``RecallFn`` the ingest node consumes.

``ingest_context`` ([app/graph/nodes/ingest_context.py]) accepts an optional
``recall: Callable[[user_id, session_id], str | None]``.  When ``None`` (local,
stateless) the node simply runs without recalled preferences.  On AgentBase we
inject a real recall function built here, which reads the user's learned
response-style preferences from the platform Memory service's LTM records
(``USER_PREFERENCE`` auto-extracted + ``CUSTOM`` response-style — see
03-ARCHITECTURE.md §5).

Contract with the node: the returned callable **may raise**.  ``ingest_context``
catches any exception and continues statelessly with ``memory_degraded=True``,
so a Memory-service blip never fails the request.

Like the checkpointer, the bridge package is deploy-time-only, so its import is
lazy and this module is always safe to import locally.

NOTE: confirm the exact memory-client import path / query API against the
installed ``greennode-agent-bridge`` version during ``preflight``.
"""

import logging
import time
from typing import Callable, Optional

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

RecallFn = Callable[[str, str], Optional[str]]


def make_agentbase_recall(settings: Settings | None = None) -> RecallFn:
    """Return a ``RecallFn`` backed by the AgentBase Memory service.

    The client is created lazily inside the returned closure so that building
    deps never imports the bridge package and never reaches the network until a
    request actually needs recall.
    """
    cfg = settings or get_settings()

    def recall(user_id: str, session_id: str) -> Optional[str]:
        """Return the user's recalled response-style preferences, or None.

        Raises on Memory-service failure so the node marks ``memory_degraded``.
        """
        if not user_id:
            return None

        logger.info("AgentBase Memory recall user_id=%s", user_id)
        t0 = time.monotonic()
        from greennode_agent_bridge.memory import MemoryClient  # lazy, deploy-only

        try:
            client = MemoryClient(memory_id=cfg.memory_id)
            records = client.search(
                actor_id=user_id,
                record_types=["USER_PREFERENCE", "CUSTOM"],
                limit=5,
            )
            prefs = [r.get("content") for r in (records or []) if r.get("content")]
            logger.info(
                "AgentBase Memory recall user_id=%s → %d prefs (%.0fms)",
                user_id, len(prefs), (time.monotonic() - t0) * 1000,
            )
            if not prefs:
                return None
            return "\n".join(prefs)
        except Exception as exc:
            logger.error(
                "AgentBase Memory recall user_id=%s failed (%.0fms): %s",
                user_id, (time.monotonic() - t0) * 1000, exc,
            )
            raise

    return recall
