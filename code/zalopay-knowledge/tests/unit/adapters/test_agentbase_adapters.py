from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.adapters import agentbase_checkpointer, agentbase_memory
from app.adapters.agentbase_checkpointer import AgentBaseCheckpointer
from app.adapters.agentbase_memory import make_agentbase_recall
from app.config import Settings


def test_modules_import_without_bridge_package() -> None:
    """Lazy imports: importing adapter modules must not require the bridge."""
    assert agentbase_checkpointer.AgentBaseCheckpointer is AgentBaseCheckpointer
    assert callable(agentbase_memory.make_agentbase_recall)


def test_checkpointer_get_saver_raises_when_bridge_missing() -> None:
    cp = AgentBaseCheckpointer(
        Settings(app_env="agentbase", memory_id="mem-1", log_level="error")
    )

    with pytest.raises(RuntimeError, match="greennode-agent-bridge"):
        cp.get_saver()


def test_checkpointer_healthy_false_when_bridge_missing() -> None:
    cp = AgentBaseCheckpointer(Settings(app_env="agentbase", log_level="error"))
    assert cp.healthy() is False


def test_recall_returns_none_for_empty_user_id() -> None:
    recall = make_agentbase_recall(
        Settings(app_env="agentbase", memory_id="mem-1", memory_strategy_id="strat-1", log_level="error")
    )
    assert recall("", "session-1") is None


def test_recall_returns_none_when_memory_id_missing() -> None:
    recall = make_agentbase_recall(
        Settings(app_env="agentbase", memory_id="", memory_strategy_id="strat-1", log_level="error")
    )
    assert recall("user-1", "session-1") is None


def test_recall_returns_none_when_strategy_id_missing() -> None:
    recall = make_agentbase_recall(
        Settings(app_env="agentbase", memory_id="mem-1", memory_strategy_id="", log_level="error")
    )
    assert recall("user-1", "session-1") is None


def test_recall_joins_memory_records() -> None:
    settings = Settings(
        app_env="agentbase",
        memory_id="mem-abc",
        memory_strategy_id="strat-xyz",
        log_level="error",
    )
    recall = make_agentbase_recall(settings)

    record1 = MagicMock()
    record1.memory = "Prefer concise answers"
    record2 = MagicMock()
    record2.memory = ""
    record3 = MagicMock()
    record3.memory = "Use Vietnamese when asked"

    mock_client = MagicMock()
    mock_client.searchMemoryRecords_async = AsyncMock(return_value=[record1, record2, record3])
    mock_client_cls = MagicMock(return_value=mock_client)

    mock_memory_module = MagicMock()
    mock_memory_module.MemoryClient = mock_client_cls

    mock_models_module = MagicMock()
    mock_models_module.MemoryRecordSearchRequest = MagicMock()

    with patch.dict(
        "sys.modules",
        {
            "greennode_agentbase": MagicMock(),
            "greennode_agentbase.memory": mock_memory_module,
            "greennode_agentbase.memory.models": mock_models_module,
        },
    ):
        result = recall("user-42", "sess-9")

    assert result == "Prefer concise answers\nUse Vietnamese when asked"
    mock_client_cls.assert_called_once_with()
    mock_client.searchMemoryRecords_async.assert_called_once()
    call_kwargs = mock_client.searchMemoryRecords_async.call_args
    assert call_kwargs.kwargs["id"] == "mem-abc"
    assert call_kwargs.kwargs["namespace"] == "/strategies/strat-xyz/actors/user-42"
