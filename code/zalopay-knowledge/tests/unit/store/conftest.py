from __future__ import annotations

from pathlib import Path

import pytest

from app.store.audit import AuditStore
from app.store.db import get_connection
from app.store.feedback import FeedbackStore
from app.store.meta import MetaStore
from app.store.sync_state import SyncOrchestrator


def _mysql_available() -> bool:
    """Return True only when a real MySQL server (not our test stub) is available."""
    import pymysql as _pymysql
    # Real pymysql package has __version__; our stub ModuleType does not.
    return hasattr(_pymysql, "__version__")


_HAS_MYSQL = _mysql_available()


@pytest.fixture
def tmp_db_dir(tmp_path: Path) -> Path:
    """Directory for isolated SQLite database files (MetaStore only)."""
    db_dir = tmp_path / "dbs"
    db_dir.mkdir()
    return db_dir


@pytest.fixture
def meta_store(tmp_db_dir: Path) -> MetaStore:
    return MetaStore(tmp_db_dir / "meta.db")


@pytest.fixture
def audit_store() -> AuditStore:
    """AuditStore backed by MySQL — truncates tables before each test for isolation."""
    if not _HAS_MYSQL:
        pytest.skip("requires MySQL")
    store = AuditStore()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM queries")
        conn.commit()
    finally:
        conn.close()
    return store


@pytest.fixture
def feedback_store() -> FeedbackStore:
    """FeedbackStore backed by MySQL — truncates tables before each test for isolation."""
    if not _HAS_MYSQL:
        pytest.skip("requires MySQL")
    store = FeedbackStore()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM feedback")
            cur.execute("DELETE FROM pending_feedback")
        conn.commit()
    finally:
        conn.close()
    return store


@pytest.fixture
def sync_orchestrator(meta_store: MetaStore) -> SyncOrchestrator:
    return SyncOrchestrator(meta_store)
