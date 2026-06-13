from __future__ import annotations

import sqlite3

from app.store.meta import MetaStore

from tests.unit.store.helpers import make_chunk_row


class TestMetaStoreSchema:
    def test_ensure_schema_creates_chunks_table(self, meta_store: MetaStore) -> None:
        meta_store.ensure_schema()
        assert meta_store._path.exists()

        conn = sqlite3.connect(str(meta_store._path))
        try:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            assert "chunks" in tables

            indexes = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index'"
                ).fetchall()
            }
            assert "idx_chunks_dept_pos" in indexes
            assert "idx_chunks_dept_lifecycle" in indexes
        finally:
            conn.close()

    def test_ensure_schema_is_idempotent(self, meta_store: MetaStore) -> None:
        meta_store.ensure_schema()
        meta_store.ensure_schema()
        assert meta_store._path.exists()


class TestMetaStoreCRUD:
    def test_upsert_and_fetch_by_positions(self, meta_store: MetaStore) -> None:
        rows = [
            make_chunk_row(chunk_id="c0", vec_pos=0, text="first"),
            make_chunk_row(chunk_id="c1", vec_pos=1, text="second"),
        ]
        meta_store.upsert_chunks(rows)

        result = meta_store.fetch_by_positions("risk", [0, 1])
        assert set(result.keys()) == {0, 1}
        assert result[0]["chunk_id"] == "c0"
        assert result[1]["text"] == "second"

    def test_upsert_replaces_existing_chunk(self, meta_store: MetaStore) -> None:
        meta_store.upsert_chunks([make_chunk_row(text="original")])
        meta_store.upsert_chunks([make_chunk_row(text="updated")])

        result = meta_store.fetch_by_positions("risk", [0])
        assert result[0]["text"] == "updated"
        assert meta_store.total_chunks() == 1

    def test_replace_department_chunks(self, meta_store: MetaStore) -> None:
        meta_store.upsert_chunks(
            [
                make_chunk_row(chunk_id="old-1", vec_pos=0, department="risk"),
                make_chunk_row(chunk_id="old-2", vec_pos=1, department="risk"),
            ]
        )
        new_rows = [
            make_chunk_row(chunk_id="new-1", vec_pos=0, department="risk"),
        ]
        written = meta_store.replace_department_chunks("risk", new_rows)

        assert written == 1
        assert meta_store.count("risk") == 1
        result = meta_store.fetch_by_positions("risk", [0, 1])
        assert 0 in result
        assert 1 not in result
        assert result[0]["chunk_id"] == "new-1"

    def test_clear_department(self, meta_store: MetaStore) -> None:
        meta_store.upsert_chunks(
            [
                make_chunk_row(chunk_id="r1", department="risk"),
                make_chunk_row(chunk_id="l1", department="legal", vec_pos=0),
            ]
        )
        meta_store.clear_department("risk")

        assert meta_store.count("risk") == 0
        assert meta_store.count("legal") == 1

    def test_departments_with_data(self, meta_store: MetaStore) -> None:
        meta_store.upsert_chunks(
            [
                make_chunk_row(chunk_id="r1", department="risk"),
                make_chunk_row(chunk_id="l1", department="legal", vec_pos=0),
            ]
        )
        assert meta_store.departments_with_data() == ["legal", "risk"]

    def test_doc_count_distinct_urls(self, meta_store: MetaStore) -> None:
        meta_store.upsert_chunks(
            [
                make_chunk_row(chunk_id="c0", vec_pos=0, url="https://a.com/doc"),
                make_chunk_row(chunk_id="c1", vec_pos=1, url="https://a.com/doc"),
                make_chunk_row(chunk_id="c2", vec_pos=2, url="https://b.com/doc"),
            ]
        )
        assert meta_store.doc_count() == 2
        assert meta_store.doc_count("risk") == 2

    def test_exists_and_empty_db(self, meta_store: MetaStore) -> None:
        assert meta_store.exists() is False
        meta_store.upsert_chunks([make_chunk_row()])
        assert meta_store.exists() is True


class TestMetaStoreTombstone:
    """Chunks marked sunset/deprecated are stored with lifecycle_state for filtering upstream."""

    def test_upsert_sunset_lifecycle_state(self, meta_store: MetaStore) -> None:
        meta_store.upsert_chunks(
            [make_chunk_row(chunk_id="sunset-1", lifecycle_state="sunset")]
        )
        row = meta_store.fetch_by_positions("risk", [0])[0]
        assert row["lifecycle_state"] == "sunset"

    def test_record_source_hashes_round_trip(self, meta_store: MetaStore) -> None:
        meta_store.record_source_hashes(
            "risk",
            [
                {
                    "url": "https://example.com/a",
                    "source_id": "1",
                    "content_hash": "abc123",
                    "last_modified": "2025-01-01",
                }
            ],
        )
        assert meta_store.get_source_hash("risk", "https://example.com/a") == "abc123"

    def test_fetch_chunks_by_url_returns_active_rows(self, meta_store: MetaStore) -> None:
        rows = [
            make_chunk_row(chunk_id="c0", vec_pos=0, url="https://example.com/a"),
            make_chunk_row(
                chunk_id="c1",
                vec_pos=1,
                url="https://example.com/a",
                lifecycle_state="sunset",
            ),
        ]
        meta_store.upsert_chunks(rows)
        active = meta_store.fetch_chunks_by_url("risk", "https://example.com/a", active_only=True)
        assert len(active) == 1
        assert active[0]["chunk_id"] == "c0"

    def test_tombstone_does_not_remove_row(self, meta_store: MetaStore) -> None:
        meta_store.upsert_chunks([make_chunk_row(chunk_id="active-1")])
        meta_store.upsert_chunks(
            [make_chunk_row(chunk_id="active-1", lifecycle_state="sunset")]
        )
        assert meta_store.count("risk") == 1
        assert meta_store.fetch_by_positions("risk", [0])[0]["lifecycle_state"] == "sunset"

    def test_mixed_lifecycle_states_in_department(self, meta_store: MetaStore) -> None:
        meta_store.upsert_chunks(
            [
                make_chunk_row(chunk_id="a", vec_pos=0, lifecycle_state="active"),
                make_chunk_row(chunk_id="d", vec_pos=1, lifecycle_state="deprecated"),
                make_chunk_row(chunk_id="s", vec_pos=2, lifecycle_state="sunset"),
            ]
        )
        result = meta_store.fetch_by_positions("risk", [0, 1, 2])
        assert result[0]["lifecycle_state"] == "active"
        assert result[1]["lifecycle_state"] == "deprecated"
        assert result[2]["lifecycle_state"] == "sunset"

    def test_tombstone_urls_marks_matching_rows(self, meta_store: MetaStore) -> None:
        meta_store.upsert_chunks(
            [
                make_chunk_row(
                    chunk_id="keep",
                    vec_pos=0,
                    url="https://example.com/keep",
                ),
                make_chunk_row(
                    chunk_id="gone",
                    vec_pos=1,
                    url="https://example.com/gone",
                ),
            ]
        )
        count = meta_store.tombstone_urls(
            "risk", {"https://example.com/gone"}
        )
        assert count == 1
        rows = meta_store.fetch_by_positions("risk", [0, 1])
        assert rows[0]["lifecycle_state"] == "active"
        assert rows[1]["lifecycle_state"] == "sunset"

    def test_distinct_urls(self, meta_store: MetaStore) -> None:
        meta_store.upsert_chunks(
            [
                make_chunk_row(chunk_id="a", vec_pos=0, url="https://example.com/a"),
                make_chunk_row(chunk_id="b", vec_pos=1, url="https://example.com/a"),
                make_chunk_row(chunk_id="c", vec_pos=2, url="https://example.com/b"),
            ]
        )
        assert meta_store.distinct_urls("risk") == {
            "https://example.com/a",
            "https://example.com/b",
        }


class TestMetaStoreEdgeCases:
    def test_fetch_by_positions_empty_and_negative(self, meta_store: MetaStore) -> None:
        meta_store.upsert_chunks([make_chunk_row()])
        assert meta_store.fetch_by_positions("risk", []) == {}
        assert meta_store.fetch_by_positions("risk", [-1, -5]) == {}

    def test_fetch_missing_position_returns_partial(self, meta_store: MetaStore) -> None:
        meta_store.upsert_chunks([make_chunk_row(vec_pos=0)])
        result = meta_store.fetch_by_positions("risk", [0, 99])
        assert set(result.keys()) == {0}

    def test_upsert_empty_rows_is_noop(self, meta_store: MetaStore) -> None:
        meta_store.upsert_chunks([])
        assert meta_store.total_chunks() == 0

    def test_count_on_missing_db_returns_zero(self, tmp_path) -> None:
        store = MetaStore(tmp_path / "nonexistent" / "meta.db")
        assert store.count("risk") == 0
        assert store.total_chunks() == 0
