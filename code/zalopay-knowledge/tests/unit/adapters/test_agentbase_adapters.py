from __future__ import annotations

from unittest.mock import MagicMock, patch

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
        Settings(app_env="agentbase", memory_id="mem-1", log_level="error")
    )
    assert recall("", "session-1") is None


def test_recall_joins_memory_records() -> None:
    settings = Settings(app_env="agentbase", memory_id="mem-abc", log_level="error")
    recall = make_agentbase_recall(settings)

    mock_client = MagicMock()
    mock_client.search.return_value = [
        {"content": "Prefer concise answers"},
        {"content": ""},
        {"content": "Use Vietnamese when asked"},
    ]

    mock_memory_client = MagicMock(return_value=mock_client)
    with patch.dict(
        "sys.modules",
        {"greennode_agent_bridge": MagicMock(), "greennode_agent_bridge.memory": MagicMock()},
    ):
        with patch(
            "greennode_agent_bridge.memory.MemoryClient",
            mock_memory_client,
        ):
            result = recall("user-42", "sess-9")

    assert result == "Prefer concise answers\nUse Vietnamese when asked"
    mock_memory_client.assert_called_once_with(memory_id="mem-abc")
    mock_client.search.assert_called_once_with(
        actor_id="user-42",
        record_types=["USER_PREFERENCE", "CUSTOM"],
        limit=5,
    )
