from __future__ import annotations

from pathlib import Path

import pytest

from app.adapters.sqlite_checkpointer import SqliteCheckpointer


def _sample_checkpoint(*, foo: str = "bar") -> dict:
    return {
        "v": 1,
        "ts": "2024-01-01T00:00:00.000000+00:00",
        "id": "00000000-0000-0000-0000-000000000001",
        "channel_values": {"foo": foo},
        "channel_versions": {"foo": 1},
        "versions_seen": {"__start__": {"__start__": 1}},
    }


def test_get_saver_creates_sqlite_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "checkpoints.db"
    cp = SqliteCheckpointer(db_path)

    saver = cp.get_saver()
    saver2 = cp.get_saver()

    assert saver is saver2
    assert db_path.exists()


def test_save_and_load_thread_state(tmp_path: Path) -> None:
    db_path = tmp_path / "checkpoints.db"
    cp = SqliteCheckpointer(db_path)
    saver = cp.get_saver()

    config = {"configurable": {"thread_id": "thread-abc", "checkpoint_ns": ""}}
    checkpoint = _sample_checkpoint(foo="persisted-value")
    metadata = {"source": "test", "step": 1, "writes": None}
    new_versions = {"foo": 1}

    saver.put(config, checkpoint, metadata, new_versions)

    loaded = saver.get_tuple(config)
    assert loaded is not None
    assert loaded.checkpoint["channel_values"]["foo"] == "persisted-value"
    assert loaded.metadata["source"] == "test"


def test_healthy_returns_true_for_writable_db(tmp_path: Path) -> None:
    cp = SqliteCheckpointer(tmp_path / "checkpoints.db")
    assert cp.healthy() is True


def test_healthy_returns_false_for_invalid_path(monkeypatch: pytest.MonkeyPatch) -> None:
    cp = SqliteCheckpointer("/proc/not-a-real-checkpoint-dir/checkpoints.db")

    def _boom(*_args, **_kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr("sqlite3.connect", _boom)
    assert cp.healthy() is False
