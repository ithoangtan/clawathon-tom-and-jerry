from __future__ import annotations

"""In-process sync job state — polled by ``GET /sync/status`` and admin APIs."""

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from app.common.departments import iter_keys
from app.store.meta import MetaStore

logger = logging.getLogger(__name__)

SyncState = Literal["running", "idle", "error"]
AdminJobStatus = Literal["pending", "running", "success", "failed"]
_MAX_HISTORY = 20


@dataclass
class SyncedContentSummary:
    source_id: str
    title: str
    url: str | None = None


@dataclass
class DepartmentSyncResult:
    department: str
    space_key: str | None = None
    status: AdminJobStatus = "pending"
    page_count: int = 0
    chunk_count: int = 0
    synced_items: list[SyncedContentSummary] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class SyncJobRecord:
    job_id: str
    source: str
    status: AdminJobStatus
    started_at: str
    finished_at: str | None = None
    department: str | None = None
    doc_count: int = 0
    chunk_count: int = 0
    errors: list[str] = field(default_factory=list)
    departments: list[DepartmentSyncResult] = field(default_factory=list)


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
    job_id: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    target_department: str | None = None
    department_results: list[DepartmentSyncResult] = field(default_factory=list)


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
        self._history: list[SyncJobRecord] = []

    def is_running(self, source: str) -> bool:
        with self._lock:
            return source in self._running

    def current_job_id(self, source: str) -> str | None:
        with self._lock:
            st = self._states.get(source)
            return st.job_id if st else None

    def start(self, source: str, *, department: str | None = None) -> bool:
        """Mark *source* as running. Returns False if already running."""
        with self._lock:
            if source in self._running:
                return False
            self._running.add(source)
            st = self._states.setdefault(source, SourceSyncState(source=source))
            st.state = "running"
            st.errors = []
            st.progress = {}
            st.job_id = str(uuid.uuid4())
            st.started_at = _iso_now()
            st.finished_at = None
            st.target_department = department
            st.department_results = []
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
            finished_at = _iso_now()
            st.finished_at = finished_at
            if success:
                st.state = "idle"
                st.doc_count = doc_count
                st.chunk_count = chunk_count
                st.last_success_at = finished_at
                st.freshness_hours = 0.0
                st.progress = None
                admin_status: AdminJobStatus = "success"
            else:
                st.state = "error"
                if error:
                    st.errors = (st.errors + [error])[-5:]
                st.progress = None
                admin_status = "failed"
            if st.job_id and st.started_at:
                self._history.append(
                    SyncJobRecord(
                        job_id=st.job_id,
                        source=source,
                        status=admin_status,
                        started_at=st.started_at,
                        finished_at=finished_at,
                        department=st.target_department,
                        doc_count=doc_count if success else st.doc_count,
                        chunk_count=chunk_count if success else st.chunk_count,
                        errors=list(st.errors),
                        departments=list(st.department_results),
                    )
                )
                self._history = self._history[-_MAX_HISTORY:]

    def update_progress(self, source: str, progress: dict[str, Any]) -> None:
        with self._lock:
            st = self._states.setdefault(source, SourceSyncState(source=source))
            st.progress = progress

    def record_department_result(self, source: str, result: DepartmentSyncResult) -> None:
        with self._lock:
            st = self._states.setdefault(source, SourceSyncState(source=source))
            for i, existing in enumerate(st.department_results):
                if existing.department == result.department:
                    st.department_results[i] = result
                    return
            st.department_results.append(result)

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

    def admin_status_snapshot(self) -> dict[str, Any]:
        """Rich sync status for ``GET /api/admin/sync/status``."""
        with self._lock:
            jobs: dict[str, Any] = {}
            for source, st in self._states.items():
                chunk_count = st.chunk_count
                if source == "confluence" and st.state != "running":
                    chunk_count = sum(
                        self._meta.count(d) for d in self._meta.departments_with_data()
                    )
                jobs[source] = {
                    "job_id": st.job_id,
                    "status": _admin_job_status(st),
                    "started_at": st.started_at,
                    "finished_at": st.finished_at,
                    "last_success_at": st.last_success_at,
                    "target_department": st.target_department,
                    "doc_count": st.doc_count,
                    "chunk_count": chunk_count if source == "confluence" else st.chunk_count,
                    "errors": list(st.errors),
                    "progress": st.progress,
                    "departments": [_department_result_dict(d) for d in st.department_results],
                }

            departments_indexed: dict[str, Any] = {}
            for dept in iter_keys():
                count = self._meta.count(dept)
                departments_indexed[dept] = {
                    "chunk_count": count,
                    "doc_count": self._meta.doc_count(dept),
                    "has_data": count > 0,
                }

            return {"jobs": jobs, "departments_indexed": departments_indexed}

    def history_snapshot(
        self,
        *,
        source: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        with self._lock:
            entries = list(reversed(self._history))
            if source:
                entries = [e for e in entries if e.source == source]
            return [_job_record_dict(e) for e in entries[: max(1, min(limit, _MAX_HISTORY))]]


def _admin_job_status(st: SourceSyncState) -> AdminJobStatus:
    if st.state == "running":
        return "running"
    if st.state == "error":
        return "failed"
    if st.last_success_at:
        return "success"
    return "pending"


def _synced_item_dict(item: SyncedContentSummary) -> dict[str, Any]:
    return {
        "source_id": item.source_id,
        "title": item.title,
        "url": item.url,
    }


def _department_result_dict(result: DepartmentSyncResult) -> dict[str, Any]:
    return {
        "department": result.department,
        "space_key": result.space_key,
        "status": result.status,
        "page_count": result.page_count,
        "chunk_count": result.chunk_count,
        "synced_items": [_synced_item_dict(i) for i in result.synced_items],
        "errors": list(result.errors),
    }


def _job_record_dict(record: SyncJobRecord) -> dict[str, Any]:
    return {
        "job_id": record.job_id,
        "source": record.source,
        "status": record.status,
        "started_at": record.started_at,
        "finished_at": record.finished_at,
        "department": record.department,
        "doc_count": record.doc_count,
        "chunk_count": record.chunk_count,
        "errors": list(record.errors),
        "departments": [_department_result_dict(d) for d in record.departments],
    }


def _iso_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
