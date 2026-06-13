from __future__ import annotations

"""In-process sync job state — polled by ``GET /sync/status``."""

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Literal

from app.store.meta import MetaStore

logger = logging.getLogger(__name__)

SyncState = Literal["running", "idle", "error"]


@dataclass
class SourceSyncState:
    source: str
    state: SyncState = "idle"
    doc_count: int = 0
    chunk_count: int = 0
    last_success_at: str | None = None
    freshness_hours: float | None = None
    errors: list[str] = field(default_factory=list)
    progress: dict[str, Any] | None = None


class SyncOrchestrator:
    """Tracks background sync jobs and exposes status for the API."""

    def __init__(self, meta: MetaStore) -> None:
        self._meta = meta
        self._lock = threading.Lock()
        self._running: set[str] = set()
        self._states: dict[str, SourceSyncState] = {
            "confluence": SourceSyncState(source="confluence"),
            "gdrive": SourceSyncState(source="gdrive"),
        }

    def is_running(self, source: str) -> bool:
        with self._lock:
            return source in self._running

    def start(self, source: str) -> bool:
        """Mark *source* as running. Returns False if already running."""
        with self._lock:
            if source in self._running:
                return False
            self._running.add(source)
            st = self._states.setdefault(source, SourceSyncState(source=source))
            st.state = "running"
            st.errors = []
            st.progress = {}
            return True

    def finish(
        self,
        source: str,
        *,
        success: bool,
        doc_count: int = 0,
        chunk_count: int = 0,
        error: str | None = None,
    ) -> None:
        with self._lock:
            self._running.discard(source)
            st = self._states.setdefault(source, SourceSyncState(source=source))
            if success:
                st.state = "idle"
                st.doc_count = doc_count
                st.chunk_count = chunk_count
                st.last_success_at = _iso_now()
                st.freshness_hours = 0.0
                st.progress = None
            else:
                st.state = "error"
                if error:
                    st.errors = (st.errors + [error])[-5:]
                st.progress = None

    def update_progress(self, source: str, progress: dict[str, Any]) -> None:
        with self._lock:
            st = self._states.setdefault(source, SourceSyncState(source=source))
            st.progress = progress

    def status_snapshot(self) -> list[dict[str, Any]]:
        """Build the ``sources`` list for ``GET /sync/status``."""
        with self._lock:
            out: list[dict[str, Any]] = []
            for source, st in self._states.items():
                chunk_count = st.chunk_count
                if source == "confluence" and st.state != "running":
                    chunk_count = sum(
                        self._meta.count(d) for d in self._meta.departments_with_data()
                    )
                freshness = st.freshness_hours
                if st.last_success_at and st.state != "running":
                    try:
                        from datetime import datetime

                        last = datetime.fromisoformat(st.last_success_at.replace("Z", "+00:00"))
                        freshness = (time.time() - last.timestamp()) / 3600.0
                    except ValueError:
                        pass
                out.append(
                    {
                        "source": source,
                        "state": st.state,
                        "doc_count": st.doc_count,
                        "chunk_count": chunk_count if source == "confluence" else st.chunk_count,
                        "last_success_at": st.last_success_at,
                        "freshness_hours": freshness,
                        "errors": list(st.errors),
                        "progress": st.progress,
                    }
                )
            return out


def _iso_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
