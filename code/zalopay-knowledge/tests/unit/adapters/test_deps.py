from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.adapters.agentbase_checkpointer import AgentBaseCheckpointer
from app.adapters.deps import build_deps, get_deps
from app.adapters.sqlite_checkpointer import SqliteCheckpointer
from app.config import Settings


@pytest.fixture
def patched_adapters():
    """Avoid loading FAISS / embedding models when testing wiring only."""
    with (
        patch("app.adapters.deps.VngMaasLLM") as mock_llm_cls,
        patch("app.adapters.deps.FaissRetriever") as mock_retriever_cls,
    ):
        mock_llm_cls.return_value = MagicMock(name="llm")
        mock_retriever_cls.return_value = MagicMock(name="retriever")
        yield mock_llm_cls, mock_retriever_cls


def test_build_deps_local_wires_sqlite_and_no_recall(
    tmp_path: Path,
    patched_adapters,
) -> None:
    mock_llm_cls, mock_retriever_cls = patched_adapters
    settings = Settings(
        app_env="local",
        index_dir=str(tmp_path / "index"),
        log_level="error",
    )

    deps = build_deps(settings)

    mock_llm_cls.assert_called_once_with(settings)
    mock_retriever_cls.assert_called_once_with(settings)
    assert isinstance(deps.checkpointer, SqliteCheckpointer)
    assert deps.checkpointer._path == tmp_path / "index" / "checkpoints.db"
    assert deps.recall is None
    assert deps.settings is settings


def test_build_deps_agentbase_wires_platform_adapters(
    tmp_path: Path,
    patched_adapters,
) -> None:
    settings = Settings(
        app_env="agentbase",
        index_dir=str(tmp_path / "index"),
        memory_id="mem-123",
        log_level="error",
    )

    deps = build_deps(settings)

    assert isinstance(deps.checkpointer, AgentBaseCheckpointer)
    assert deps.recall is not None
    assert callable(deps.recall)


def test_get_deps_is_cached(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    get_deps.cache_clear()
    monkeypatch.setenv("INDEX_DIR", str(tmp_path / "index"))
    monkeypatch.setenv("APP_ENV", "local")

    from app.config import get_settings

    get_settings.cache_clear()

    with (
        patch("app.adapters.deps.VngMaasLLM", return_value=MagicMock()),
        patch("app.adapters.deps.FaissRetriever", return_value=MagicMock()),
    ):
        first = get_deps()
        second = get_deps()

    assert first is second

    get_deps.cache_clear()
    get_settings.cache_clear()
