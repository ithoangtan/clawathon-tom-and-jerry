from __future__ import annotations

import hashlib
import re

import pytest

from app.ingestion.chunker import _MAX_CHARS, _MIN_CHARS, _OVERLAP_CHARS, chunk_text, classify_doc_type
from app.ingestion.metadata import parse_acl, parse_labels
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK

# Approximate token count using the chunker's 4 chars/token heuristic.
_CHARS_PER_TOKEN = 4
_MIN_TOKENS = 300
_MAX_TOKENS = 800


def _approx_tokens(text: str) -> int:
    return len(text) // _CHARS_PER_TOKEN


def _hash_prefix(department: str, url: str, text: str) -> str:
    digest = hashlib.sha256(f"{department}|{url}|{text[:200]}".encode()).hexdigest()[:16]
    return f"{department}-{digest}"


class TestChunkText:
    def test_empty_text_returns_no_chunks(self):
        assert chunk_text("", department=RISK, doc_type="policy", title="T", url="u") == []

    def test_whitespace_only_returns_no_chunks(self):
        assert chunk_text("   \n\n  ", department=RISK, doc_type="policy", title="T", url="u") == []

    def test_produces_at_least_one_chunk(self, sample_text: str):
        chunks = chunk_text(
            sample_text,
            department=RISK,
            doc_type="policy",
            title="Escalation Policy",
            url="https://example.com/policy",
        )
        assert len(chunks) >= 1

    def test_chunk_sizes_within_token_target_range(self, long_text: str):
        """Long segments are windowed to ~300–800 tokens (chars heuristic)."""
        chunks = chunk_text(
            long_text,
            department=RISK,
            doc_type="policy",
            title="Long Doc",
            url="https://example.com/long",
        )
        assert len(chunks) > 1
        for chunk in chunks:
            text = chunk["text"]
            assert len(text) <= _MAX_CHARS
            assert _approx_tokens(text) <= _MAX_TOKENS
            # Interior windows advance by at least _MIN_CHARS (≈75 tokens).
            if len(text) >= _MIN_CHARS:
                assert len(text) >= _MIN_CHARS or len(text) == len(long_text.strip())

    def test_metadata_preserved_on_every_chunk(self, sample_text: str):
        chunks = chunk_text(
            sample_text,
            department=GROW,
            doc_type="Operation",
            title="Growth Playbook",
            url="https://example.com/grow",
            source="67890",
            section="Onboarding",
            anchor="onboarding",
            space="GROW",
            labels=["playbook", "growth"],
            last_modified="2025-02-01T12:00:00Z",
            author="grow.owner@example.com",
            lifecycle_state="active",
            source_type="confluence",
            page=None,
        )
        assert chunks
        for chunk in chunks:
            assert chunk["department"] == GROW
            assert chunk["doc_type"] == "Operation"
            assert chunk["title"] == "Growth Playbook"
            assert chunk["url"] == "https://example.com/grow"
            assert chunk["source"] == "67890"
            assert chunk["section"] == "Onboarding"
            assert chunk["anchor"] == "onboarding"
            assert chunk["space"] == "GROW"
            assert parse_labels(chunk["labels"]) == ["growth", "playbook"]
            assert chunk["last_modified"] == "2025-02-01T12:00:00Z"
            assert chunk["author"] == "grow.owner@example.com"
            assert parse_acl(chunk["acl"]) == ["all-employees"]
            assert chunk["lifecycle_state"] == "active"
            assert chunk["source_type"] == "confluence"
            assert chunk["page"] is None
            assert chunk["vec_pos"] == 0
            assert chunk["chunk_id"].startswith("grow_enablement-")
            assert chunk["text"]

    def test_pdf_page_metadata(self):
        chunks = chunk_text(
            "Page content about bank partnerships.",
            department=BANK,
            doc_type="guide",
            title="partner.pdf",
            url="https://drive.google.com/file/d/abc",
            source_type="pdf",
            page=2,
        )
        assert len(chunks) == 1
        assert chunks[0]["source_type"] == "pdf"
        assert chunks[0]["page"] == 2

    def test_heading_boundaries_create_segments(self):
        section_a = "# Section A\n\n" + ("A content. " * 400)
        section_b = "# Section B\n\n" + ("B content. " * 400)
        text = section_a + "\n\n" + section_b
        chunks = chunk_text(
            text,
            department=RISK,
            doc_type="policy",
            title="Segmented",
            url="https://example.com/seg",
        )
        assert len(chunks) >= 2
        joined = "\n".join(c["text"] for c in chunks)
        assert "Section A" in joined
        assert "Section B" in joined

    def test_overlap_between_consecutive_windows(self):
        """Windows on a long segment share _OVERLAP_CHARS of text."""
        segment = "word " * 2000  # well over _MAX_CHARS
        chunks = chunk_text(
            segment,
            department=RISK,
            doc_type="policy",
            title="Overlap",
            url="https://example.com/overlap",
        )
        assert len(chunks) >= 2
        for prev, nxt in zip(chunks, chunks[1:], strict=False):
            prev_tail = prev["text"][-_OVERLAP_CHARS:]
            nxt_head = nxt["text"][: _OVERLAP_CHARS + 20]
            assert prev_tail.strip() and prev_tail in nxt["text"]

    def test_content_hash_prefix_stable_for_same_input(self, sample_text: str):
        url = "https://example.com/stable"
        chunks_a = chunk_text(
            sample_text,
            department=RISK,
            doc_type="policy",
            title="T",
            url=url,
        )
        chunks_b = chunk_text(
            sample_text,
            department=RISK,
            doc_type="policy",
            title="T",
            url=url,
        )
        for a, b in zip(chunks_a, chunks_b, strict=True):
            expected = _hash_prefix(RISK, url, a["text"])
            assert a["chunk_id"].startswith(expected)
            assert b["chunk_id"].startswith(expected)
            # UUID suffix differs across calls.
            assert a["chunk_id"] != b["chunk_id"]

    def test_normalizes_excessive_blank_lines(self):
        text = "Line one\n\n\n\n\nLine two"
        chunks = chunk_text(
            text,
            department=RISK,
            doc_type="policy",
            title="T",
            url="u",
        )
        assert len(chunks) == 1
        assert not re.search(r"\n{3,}", chunks[0]["text"])


class TestClassifyDocType:
    def test_title_keyword_prd(self):
        assert classify_doc_type(title="Q1 Product PRD", department=RISK) == "PRD"

    def test_title_keyword_rca(self):
        assert classify_doc_type(title="Payment outage RCA", department=RISK) == "RCA"

    def test_url_keyword_security(self):
        assert (
            classify_doc_type(
                title="Review",
                url="https://wiki/spaces/RISK/pages/security-audit",
                department=RISK,
            )
            == "Security"
        )

    def test_department_default_risk(self):
        assert classify_doc_type(title="General notes", department=RISK) == "Risk"

    def test_department_default_grow(self):
        assert classify_doc_type(title="Notes", department=GROW) == "Operation"

    def test_runbook_maps_to_operation(self):
        assert classify_doc_type(title="Settlement runbook", department=BANK) == "Operation"
