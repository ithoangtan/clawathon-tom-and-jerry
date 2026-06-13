from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest

# Stub optional runtime deps so API/ingestion tests collect without a full image.
if "pypdf" not in sys.modules:
    _pypdf = ModuleType("pypdf")
    _pypdf.PdfReader = MagicMock()
    sys.modules["pypdf"] = _pypdf


@pytest.fixture(autouse=True)
def test_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Isolate index/audit DBs per test."""
    index_dir = tmp_path / "index"
    index_dir.mkdir()
    monkeypatch.setenv("INDEX_DIR", str(index_dir))
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("LOG_LEVEL", "error")

    from app.config import get_settings

    get_settings.cache_clear()

    from app.adapters.deps import get_deps

    get_deps.cache_clear()

    from app.graph import get_compiled_graph

    get_compiled_graph.cache_clear()

    from app.api import service as api_service

    api_service.get_audit_store.cache_clear()
    api_service.get_feedback_store.cache_clear()

    yield

    get_settings.cache_clear()
    get_deps.cache_clear()
    get_compiled_graph.cache_clear()
    api_service.get_audit_store.cache_clear()
    api_service.get_feedback_store.cache_clear()
