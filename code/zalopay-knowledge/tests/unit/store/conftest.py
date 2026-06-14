from __future__ import annotations

from pathlib import Path

import pytest

from app.store.audit import AuditStore
from app.store.feedback import FeedbackStore
from app.store.meta import MetaStore
from app.store.sync_state import SyncOrchestrator


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
    """AuditStore backed by MySQL — requires DB_HOST/DB_USER/DB_PASSWORD env vars."""
    return AuditStore()


@pytest.fixture
def feedback_store() -> FeedbackStore:
    """FeedbackStore backed by MySQL — requires DB_HOST/DB_USER/DB_PASSWORD env vars."""
    return FeedbackStore()


@pytest.fixture
def sync_orchestrator(meta_store: MetaStore) -> SyncOrchestrator:
    return SyncOrchestrator(meta_store)
