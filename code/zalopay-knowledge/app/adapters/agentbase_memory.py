from __future__ import annotations

"""AgentBase LTM recall — builds the ``RecallFn`` the ingest node consumes.

``ingest_context`` ([app/graph/nodes/ingest_context.py]) accepts an optional
``recall: Callable[[user_id, session_id], str | None]``.  When ``None`` (local,
stateless) the node simply runs without recalled preferences.  On AgentBase we
inject a real recall function built here, which reads the user's learned
response-style preferences from the platform Memory service's LTM records
(``USER_PREFERENCE`` auto-extracted + ``CUSTOM`` response-style).

Contract with the node: the returned callable **may raise**.  ``ingest_context``
catches any exception and continues statelessly with ``memory_degraded=True``,
so a Memory-service blip never fails the request.

Like the checkpointer, the SDK packages are deploy-time-only, so imports are
lazy and this module is always safe to import locally.
"""

import asyncio
import logging
import time
from typing import Callable, Optional

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

RecallFn = Callable[[str, str], Optional[str]]

_RECALL_QUERY = "user communication preferences and response style"


def make_agentbase_recall(settings: Settings | None = None) -> RecallFn:
    """Return a ``RecallFn`` backed by the AgentBase Memory service.

    The client is created lazily inside the returned closure so that building
    deps never imports the SDK packages and never reaches the network until a
    request actually needs recall.
    """
    cfg = settings or get_settings()

    def recall(user_id: str, session_id: str) -> Optional[str]:
        """Return the user's recalled response-style preferences, or None.

        Raises on Memory-service failure so the node marks ``memory_degraded``.
        """
        if not user_id or not cfg.memory_id or not cfg.memory_strategy_id:
            return None

        logger.info("AgentBase Memory recall user_id=%s", user_id)
        t0 = time.monotonic()
        from greennode_agentbase.memory import MemoryClient  # lazy, deploy-only
        from greennode_agentbase.memory.models import MemoryRecordSearchRequest

        try:
            namespace = f"/strategies/{cfg.memory_strategy_id}/actors/{user_id}"
            client = MemoryClient()
            results = asyncio.run(
                client.searchMemoryRecords_async(
                    id=cfg.memory_id,
                    namespace=namespace,
                    request=MemoryRecordSearchRequest(
                        query=_RECALL_QUERY,
                        limit=5,
                        scoreThreshold=0.5,
                    ),
                )
            )
            prefs = [r.memory for r in (results or []) if r.memory]
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
