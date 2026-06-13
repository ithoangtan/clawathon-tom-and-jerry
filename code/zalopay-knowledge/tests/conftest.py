from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from app.common.departments import DepartmentKey, all_departments, iter_keys
from tests.department_fixtures import ALL_KEYS, BANK, GROW, RISK

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


@pytest.fixture
def dept_risk() -> str:
    return RISK


@pytest.fixture
def dept_grow() -> str:
    return GROW


@pytest.fixture
def dept_bank() -> str:
    return BANK


@pytest.fixture
def all_dept_keys() -> list[str]:
    return list(ALL_KEYS)


@pytest.fixture
def sample_confluence_spaces() -> dict[str, str]:
    return {
        DepartmentKey.RISK.value: "RISK",
        DepartmentKey.GROW_ENABLEMENT.value: "GROW",
        DepartmentKey.BANK_PARTNERSHIPS.value: "BANK",
    }


@pytest.fixture
def all_departments_list():
    return all_departments()
