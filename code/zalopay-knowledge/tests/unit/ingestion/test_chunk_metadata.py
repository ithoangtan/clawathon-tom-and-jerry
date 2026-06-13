from __future__ import annotations

import json
import sqlite3

import pytest

from app.ingestion.chunker import chunk_text, classify_doc_type
from app.ingestion.metadata import (
    DOC_TYPES,
    MVP_ACL_DEFAULT,
    REQUIRED_CHUNK_METADATA_FIELDS,
    parse_acl,
    parse_labels,
    serialize_acl,
)
from app.store.meta import CHUNK_COLUMNS, MetaStore
from tests.unit.store.helpers import make_chunk_row


class TestRequiredMetadataFields:
    """Checklist §4: every indexed chunk carries the full metadata contract."""

    @pytest.mark.parametrize("field", REQUIRED_CHUNK_METADATA_FIELDS)
    def test_chunk_text_includes_required_field(self, field: str, sample_text: str) -> None:
        chunks = chunk_text(
            sample_text,
            department="risk",
            doc_type="Risk",
            title="Escalation Policy",
            url="https://example.com/policy",
            source="12345",
            space="RISK",
            labels=["policy"],
            author="owner@example.com",
            last_modified="2025-01-15T10:00:00Z",
        )
        assert chunks
        for chunk in chunks:
            assert field in chunk

    def test_chunk_text_keys_match_meta_store_columns(self, sample_text: str) -> None:
        chunks = chunk_text(
            sample_text,
            department="risk",
            doc_type="Risk",
            title="T",
            url="https://example.com/t",
        )
        assert chunks
        assert set(chunks[0].keys()) == set(CHUNK_COLUMNS)

    def test_acl_defaults_to_all_employees_when_omitted(self, sample_text: str) -> None:
        chunks = chunk_text(
            sample_text,
            department="risk",
            doc_type="Risk",
            title="T",
            url="https://example.com/t",
        )
        for chunk in chunks:
            assert parse_acl(chunk["acl"]) == MVP_ACL_DEFAULT

    def test_labels_default_to_empty_json_array(self, sample_text: str) -> None:
        chunks = chunk_text(
            sample_text,
            department="risk",
            doc_type="Risk",
            title="T",
            url="https://example.com/t",
        )
        for chunk in chunks:
            assert parse_labels(chunk["labels"]) == []

    def test_heading_derives_section_and_anchor(self) -> None:
        text = "# Severity levels\n\nDefine P1 through P4."
        chunks = chunk_text(
            text,
            department="risk",
            doc_type="Risk",
            title="Policy",
            url="https://example.com/p",
        )
        assert chunks[0]["section"] == "Severity levels"
        assert chunks[0]["anchor"] == "severity-levels"

    def test_meta_store_round_trips_all_columns(self, meta_store: MetaStore) -> None:
        row = make_chunk_row()
        meta_store.upsert_chunks([row])
        stored = meta_store.fetch_by_positions("risk", [0])[0]
        for column in CHUNK_COLUMNS:
            assert column in stored
            assert stored[column] == row[column]


class TestMetaStoreSchemaColumns:
    def test_chunks_table_has_required_metadata_columns(self, meta_store: MetaStore) -> None:
        meta_store.ensure_schema()
        conn = sqlite3.connect(str(meta_store._path))
        try:
            columns = {
                row[1]: row[2]
                for row in conn.execute("PRAGMA table_info(chunks)").fetchall()
            }
        finally:
            conn.close()

        for field in REQUIRED_CHUNK_METADATA_FIELDS:
            assert field in columns

    def test_migration_adds_columns_to_legacy_db(self, tmp_path) -> None:
        db_path = tmp_path / "legacy-meta.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            """
            CREATE TABLE chunks (
                chunk_id TEXT PRIMARY KEY,
                department TEXT NOT NULL,
                vec_pos INTEGER NOT NULL,
                doc_type TEXT,
                title TEXT,
                url TEXT,
                section TEXT,
                last_modified TEXT,
                lifecycle_state TEXT NOT NULL DEFAULT 'active',
                source_type TEXT,
                page INTEGER,
                text TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()

        store = MetaStore(db_path)
        store.ensure_schema()

        conn = sqlite3.connect(str(db_path))
        try:
            columns = {row[1] for row in conn.execute("PRAGMA table_info(chunks)").fetchall()}
        finally:
            conn.close()

        assert {"source", "anchor", "space", "labels", "author", "acl"}.issubset(columns)


class TestDocTypeClassification:
    @pytest.mark.parametrize(
        ("title", "labels", "expected"),
        [
            ("Q1 Product PRD", None, "PRD"),
            ("Payment outage RCA", None, "RCA"),
            ("Security audit checklist", None, "Security"),
            ("AML compliance guide", None, "Risk"),
            ("Settlement runbook", None, "Operation"),
            ("API design doc", None, "Technical"),
            ("Org structure 2025", None, "Org-structure"),
            ("Ops guidance for on-call", None, "Ops-guidance"),
        ],
    )
    def test_title_keyword_rules(
        self, title: str, labels: list[str] | None, expected: str
    ) -> None:
        result = classify_doc_type(title=title, department="grow_enablement", labels=labels)
        assert result == expected
        assert result in DOC_TYPES

    def test_label_can_classify_ops_guidance(self) -> None:
        assert (
            classify_doc_type(
                title="Weekly checklist",
                department="grow_enablement",
                labels=["ops-guidance"],
            )
            == "Ops-guidance"
        )

    def test_url_keyword_security(self) -> None:
        assert (
            classify_doc_type(
                title="Review",
                url="https://wiki/spaces/RISK/pages/security-audit",
                department="risk",
            )
            == "Security"
        )

    def test_department_defaults(self) -> None:
        assert classify_doc_type(title="General notes", department="risk") == "Risk"
        assert classify_doc_type(title="Notes", department="grow_enablement") == "Operation"
        assert (
            classify_doc_type(title="Notes", department="bank_partnerships") == "Technical"
        )

    def test_all_doc_types_are_classifiable_via_rules_or_defaults(self) -> None:
        samples = {
            "PRD": classify_doc_type(title="Feature PRD"),
            "RCA": classify_doc_type(title="Incident RCA"),
            "Security": classify_doc_type(title="Security review"),
            "Risk": classify_doc_type(title="Risk memo", department="risk"),
            "Operation": classify_doc_type(title="Settlement runbook"),
            "Technical": classify_doc_type(title="System architecture"),
            "Org-structure": classify_doc_type(title="Team org structure"),
            "Ops-guidance": classify_doc_type(title="Ops guidance note"),
        }
        assert set(samples.values()) == set(DOC_TYPES)


class TestMetadataSerialization:
    def test_serialize_acl_is_valid_json(self) -> None:
        raw = serialize_acl(None)
        assert json.loads(raw) == MVP_ACL_DEFAULT
