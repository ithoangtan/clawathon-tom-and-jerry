from __future__ import annotations

from pathlib import Path

import pytest

from app.store.audit import AuditStore
from app.store.feedback import FeedbackStore
from app.store.meta import MetaStore
from app.store.sync_state import SyncOrchestrator


@pytest.fixture
def tmp_db_dir(tmp_path: Path) -> Path:
    """Directory for isolated SQLite database files."""
    db_dir = tmp_path / "dbs"
    db_dir.mkdir()
    return db_dir


@pytest.fixture
def meta_store(tmp_db_dir: Path) -> MetaStore:
    return MetaStore(tmp_db_dir / "meta.db")


@pytest.fixture
def audit_store(tmp_db_dir: Path) -> AuditStore:
    return AuditStore(tmp_db_dir / "audit.db")


@pytest.fixture
def feedback_store(tmp_db_dir: Path) -> FeedbackStore:
    return FeedbackStore(tmp_db_dir / "feedback.db")


@pytest.fixture
def sync_orchestrator(meta_store: MetaStore) -> SyncOrchestrator:
    return SyncOrchestrator(meta_store)
