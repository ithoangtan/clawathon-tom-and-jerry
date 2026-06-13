from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    CitationModel,
    ClarifyingQuestion,
    ConflictModel,
    ConflictSide,
    DashboardData,
    FeedbackRequest,
    HealthInfo,
    HistoryItem,
    SourceStatus,
    SyncStartResponse,
    SyncStatusResponse,
)
from tests.department_fixtures import GROW, RISK


class TestChatRequest:
    def test_valid_minimal(self) -> None:
        req = ChatRequest(question="What is the escalation process?")
        assert req.question == "What is the escalation process?"
        assert req.target_departments is None

    def test_valid_with_target_departments(self) -> None:
        req = ChatRequest(question="hello", target_departments=[RISK, GROW])
        assert req.target_departments == [RISK, GROW]

    def test_rejects_empty_question(self) -> None:
        with pytest.raises(ValidationError) as exc:
            ChatRequest(question="")
        errors = exc.value.errors()
        assert any(e["loc"] == ("question",) for e in errors)

    def test_rejects_question_over_4000_chars(self) -> None:
        with pytest.raises(ValidationError) as exc:
            ChatRequest(question="x" * 4001)
        errors = exc.value.errors()
        assert any(e["loc"] == ("question",) for e in errors)

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError) as exc:
            ChatRequest(question="hello", unknown_field="nope")  # type: ignore[call-arg]
        errors = exc.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)

    def test_rejects_invalid_department(self) -> None:
        with pytest.raises(ValidationError):
            ChatRequest(question="hello", target_departments=["finance"])  # type: ignore[list-item]


class TestFeedbackRequest:
    def test_valid_minimal(self) -> None:
        req = FeedbackRequest(feedback_id="fb-123", rating="up")
        assert req.rating == "up"
        assert req.comment is None

    def test_valid_with_comment(self) -> None:
        req = FeedbackRequest(
            feedback_id="fb-123",
            rating="down",
            comment="Not helpful",
        )
        assert req.comment == "Not helpful"

    def test_rejects_empty_feedback_id(self) -> None:
        with pytest.raises(ValidationError):
            FeedbackRequest(feedback_id="", rating="up")

    def test_rejects_comment_over_2000_chars(self) -> None:
        with pytest.raises(ValidationError):
            FeedbackRequest(feedback_id="fb-1", rating="up", comment="x" * 2001)

    def test_rejects_invalid_rating(self) -> None:
        with pytest.raises(ValidationError):
            FeedbackRequest(feedback_id="fb-1", rating="maybe")  # type: ignore[arg-type]


class TestCitationModel:
    def test_required_fields(self) -> None:
        with pytest.raises(ValidationError) as exc:
            CitationModel(title="Doc")  # type: ignore[call-arg]
        locs = {tuple(e["loc"]) for e in exc.value.errors()}
        assert ("url",) in locs

    def test_full_shape(self) -> None:
        cite = CitationModel(
            title="Policy",
            url="https://example.com/doc",
            section="Section 1",
            last_modified="2024-01-01T00:00:00Z",
            lifecycle_state="active",
            deprecated=True,
            successor_url="https://example.com/new",
            source_type="pdf",
            page=3,
            excerpt="Policy excerpt text.",
            chunk_id="risk-abc123",
            doc_type="Risk",
        )
        assert cite.page == 3
        assert cite.deprecated is True
        assert cite.excerpt == "Policy excerpt text."
        assert cite.chunk_id == "risk-abc123"
        assert cite.doc_type == "Risk"

    def test_excerpt_and_chunk_id_optional(self) -> None:
        cite = CitationModel(title="Doc", url="https://example.com")
        assert cite.excerpt is None
        assert cite.chunk_id is None
        assert cite.doc_type is None


class TestConflictAndClarifying:
    def test_conflict_model(self) -> None:
        side = ConflictSide(
            department=RISK,
            statement="SLA is 4 hours",
            citation=CitationModel(title="Runbook", url="https://example.com"),
        )
        conflict = ConflictModel(topic="SLA", sides=[side])
        assert conflict.topic == "SLA"
        assert len(conflict.sides) == 1

    def test_clarifying_question(self) -> None:
        cq = ClarifyingQuestion(
            prompt="Which department?",
            options=[RISK, GROW],
        )
        assert cq.options == [RISK, GROW]


class TestChatResponse:
    def test_valid_response(self) -> None:
        resp = ChatResponse(
            answer="Answer [1]",
            confidence=0.5,
            feedback_id="fb-1",
            status="answered",
        )
        assert resp.citations == []
        assert resp.lang is None

    def test_rejects_confidence_below_zero(self) -> None:
        with pytest.raises(ValidationError):
            ChatResponse(
                answer="x",
                confidence=-0.1,
                feedback_id="fb-1",
                status="answered",
            )

    def test_rejects_confidence_above_one(self) -> None:
        with pytest.raises(ValidationError):
            ChatResponse(
                answer="x",
                confidence=1.1,
                feedback_id="fb-1",
                status="answered",
            )

    def test_allows_extra_keys_for_forward_compat(self) -> None:
        resp = ChatResponse(
            answer="x",
            confidence=0.5,
            feedback_id="fb-1",
            status="answered",
            future_field="ok",  # type: ignore[call-arg]
        )
        assert resp.model_dump().get("future_field") == "ok"


class TestSyncAndDashboardSchemas:
    def test_sync_start_response(self) -> None:
        resp = SyncStartResponse(
            source="confluence",
            started=True,
            message="Confluence sync started in background",
        )
        assert resp.source == "confluence"

    def test_sync_status_response(self) -> None:
        status = SyncStatusResponse(
            sources=[
                SourceStatus(source="confluence", state="idle"),
                SourceStatus(source="gdrive", state="running", progress={"files_processed": 1}),
            ]
        )
        assert len(status.sources) == 2

    def test_dashboard_data_rates_bounded(self) -> None:
        dash = DashboardData(
            query_count=10,
            deflection_rate=0.82,
            answered_wrong_rate=0.05,
            refusal_rate=0.08,
            partial_rate=0.12,
            conflict_rate=0.04,
        )
        assert dash.deflection_rate == 0.82
        assert dash.query_count == 10

        with pytest.raises(ValidationError):
            DashboardData(refusal_rate=1.5)

    def test_history_item(self) -> None:
        item = HistoryItem(
            ts="2024-12-01T15:42:00Z",
            question="What is KYC?",
            departments=[RISK],
            status="answered",
            confidence=0.91,
            latency_ms=1523,
        )
        assert item.latency_ms == 1523


class TestHealthInfo:
    def test_defaults(self) -> None:
        health = HealthInfo()
        assert health.status == "healthy"
        assert health.index_ready is False
        assert health.maas_ready is False
        assert health.ready is False
        assert health.version is None
        assert health.config is None

    def test_with_config_snapshot(self) -> None:
        health = HealthInfo(
            version="0.1.0",
            index_ready=True,
            maas_ready=True,
            ready=True,
            config={"topk": 8, "grade_threshold": 0.5},
        )
        assert health.ready is True
        assert health.config["topk"] == 8
