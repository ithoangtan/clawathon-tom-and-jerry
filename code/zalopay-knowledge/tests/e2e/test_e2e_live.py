"""30-case E2E test suite against the live server at localhost:8080.

All cases hit the real running FastAPI backend — no mocks, no TestClient.
Calls go to real MySQL, real OpenSearch/FAISS, and real VNG MaaS LLM endpoints.

Run with:
    pytest tests/e2e/test_e2e_live.py -v --tb=short

Prerequisites:
    - BE running at localhost:8080 (make up or uvicorn directly)
    - MySQL reachable (DB_HOST=127.0.0.1)
    - MaaS LLM accessible (checked via /health)
"""

from __future__ import annotations

import uuid

import pytest
import requests

BASE = "http://localhost:8080"

AUTH = {
    "X-GreenNode-AgentBase-User-Id": "e2e-user",
    "X-GreenNode-AgentBase-Session-Id": "e2e-session",
    "X-GreenNode-AgentBase-Role": "engineer",
    "X-GreenNode-AgentBase-Home-Department": "risk",
}

JSON_CT = {"Content-Type": "application/json"}


def _chat(question: str, headers: dict | None = None, **body_kwargs) -> requests.Response:
    h = {**AUTH, **JSON_CT, **(headers or {})}
    return requests.post(f"{BASE}/chat", json={"question": question, **body_kwargs}, headers=h)


def _get(path: str, **params) -> requests.Response:
    return requests.get(f"{BASE}{path}", headers=AUTH, params=params)


@pytest.fixture(scope="session")
def index_ready() -> bool:
    r = requests.get(f"{BASE}/health")
    return r.json().get("index_ready", False)


# ── 1. Health Endpoints ─────────────────────────────────────────────────────


class TestHealthEndpoints:
    def test_e01_health_returns_200_and_healthy(self) -> None:
        """GET /health → 200 with status=healthy."""
        r = requests.get(f"{BASE}/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "healthy"
        assert body["version"] == "1.0.0"
        assert "index_ready" in body

    def test_e02_health_config_has_expected_fields(self) -> None:
        """GET /health → config block contains all required fields."""
        body = requests.get(f"{BASE}/health").json()
        cfg = body["config"]
        assert cfg["grade_threshold"] == pytest.approx(0.3)
        assert cfg["topk"] == 8
        assert cfg["route_confidence_min"] == pytest.approx(0.55)
        assert cfg["embedding_model"] == "baai/bge-m3"
        assert "small_model" in cfg
        assert "main_model" in cfg

    def test_e03_health_ready_probe(self) -> None:
        """GET /health/ready → 200 when ready, 503 when not (K8s readiness probe semantics)."""
        r = requests.get(f"{BASE}/health/ready")
        assert r.status_code in (200, 503)
        body = r.json()
        assert "index_ready" in body
        assert "ready" in body

    def test_e04_health_live_probe(self) -> None:
        """GET /health/live → 200 with version field."""
        r = requests.get(f"{BASE}/health/live")
        assert r.status_code == 200
        body = r.json()
        assert body["version"] == "1.0.0"
        assert body["status"] == "healthy"


# ── 2. Chat: Auth / Validation Errors ───────────────────────────────────────


class TestChatAuthValidation:
    def test_e05_chat_missing_user_id_returns_400(self) -> None:
        """POST /chat without User-Id → 400 with helpful detail."""
        h = {**JSON_CT, "X-GreenNode-AgentBase-Session-Id": "s1"}
        r = requests.post(f"{BASE}/chat", json={"question": "hello"}, headers=h)
        assert r.status_code == 400
        assert "User-Id" in r.json()["detail"]

    def test_e06_chat_missing_session_id_returns_400(self) -> None:
        """POST /chat without Session-Id → 400 with helpful detail."""
        h = {**JSON_CT, "X-GreenNode-AgentBase-User-Id": "u1"}
        r = requests.post(f"{BASE}/chat", json={"question": "hello"}, headers=h)
        assert r.status_code == 400
        assert "Session-Id" in r.json()["detail"]

    def test_e07_chat_empty_question_returns_422(self) -> None:
        """POST /chat with empty question string → 422 validation error."""
        r = _chat("")
        assert r.status_code == 422

    def test_e08_chat_question_too_long_returns_422(self) -> None:
        """POST /chat with 4001-char question → 422 max_length violation."""
        r = _chat("x" * 4001)
        assert r.status_code == 422
        errs = r.json()["detail"]
        assert any("4000" in str(e) for e in errs)

    def test_e09_chat_extra_field_forbidden_returns_422(self) -> None:
        """POST /chat with unknown field → 422 (extra=forbid on ChatRequest)."""
        h = {**AUTH, **JSON_CT}
        r = requests.post(
            f"{BASE}/chat", json={"question": "hello", "unknown_field": "bad"}, headers=h
        )
        assert r.status_code == 422

    def test_e10_chat_invalid_json_returns_422(self) -> None:
        """POST /chat with malformed JSON body → 422."""
        h = {**AUTH, **JSON_CT}
        r = requests.post(f"{BASE}/chat", data="not-json-at-all", headers=h)
        assert r.status_code == 422


# ── 3. Chat: KB-Not-Ready Behaviour ──────────────────────────────────────────


class TestChatKBNotReady:
    def test_e11_chat_returns_503_when_index_not_ready(self, index_ready: bool) -> None:
        """POST /chat → 503 when index is not ready (no sync done)."""
        if index_ready:
            pytest.skip("Index is ready — this case is only meaningful before sync")
        r = _chat("What is the escalation process?")
        assert r.status_code == 503
        assert "not ready" in r.json()["detail"].lower()

    def test_e12_invocations_503_when_index_not_ready(self, index_ready: bool) -> None:
        """POST /invocations (AgentBase alias) → 503 when index not ready."""
        if index_ready:
            pytest.skip("Index is ready — this case is only meaningful before sync")
        h = {**AUTH, **JSON_CT}
        r = requests.post(f"{BASE}/invocations", json={"question": "What is risk?"}, headers=h)
        assert r.status_code == 503

    def test_e13_stream_503_when_index_not_ready(self, index_ready: bool) -> None:
        """POST /chat/stream → 503 when index not ready."""
        if index_ready:
            pytest.skip("Index is ready — this case is only meaningful before sync")
        h = {**AUTH, **JSON_CT}
        r = requests.post(f"{BASE}/chat/stream", json={"question": "test"}, headers=h)
        assert r.status_code == 503


# ── 4. Chat: Live Q&A (skipped when index not ready) ─────────────────────────


class TestChatLiveQA:
    def test_e14_chat_out_of_scope_returns_refused(self, index_ready: bool) -> None:
        """Chat with a clearly out-of-scope question → refused with out_of_scope reason."""
        if not index_ready:
            pytest.skip("Requires indexed KB")
        r = _chat("What is today's weather in Ho Chi Minh City?")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "refused"
        assert body.get("refusal_reason") == "out_of_scope"

    def test_e15_chat_answered_has_required_fields(self, index_ready: bool) -> None:
        """Chat with a domain question → response has all required ChatResponse fields."""
        if not index_ready:
            pytest.skip("Requires indexed KB")
        r = _chat("What is the escalation process for risk alerts?")
        assert r.status_code == 200
        body = r.json()
        assert "status" in body
        assert "answer" in body
        assert "citations" in body
        assert "source_departments" in body
        assert "confidence" in body
        assert "feedback_id" in body
        assert "lang" in body

    def test_e16_chat_answered_citations_are_valid(self, index_ready: bool) -> None:
        """Chat → citations array has valid structure (url, title, source_type)."""
        if not index_ready:
            pytest.skip("Requires indexed KB")
        r = _chat("Describe the KYC procedure for merchant onboarding.")
        assert r.status_code == 200
        body = r.json()
        if body["status"] == "answered":
            for cit in body["citations"]:
                assert "title" in cit
                assert "url" in cit
                assert "source_type" in cit

    def test_e17_chat_vi_question_answered_in_vi(self, index_ready: bool) -> None:
        """Vietnamese question → response language is 'vi'."""
        if not index_ready:
            pytest.skip("Requires indexed KB")
        r = _chat("Quy trình leo thang rủi ro là gì?")
        assert r.status_code == 200
        body = r.json()
        assert body.get("lang") == "vi"

    def test_e18_chat_with_target_department_routes_correctly(self, index_ready: bool) -> None:
        """Chat with target_departments=['risk'] routes to risk department only."""
        if not index_ready:
            pytest.skip("Requires indexed KB")
        h = {**AUTH, **JSON_CT}
        r = requests.post(
            f"{BASE}/chat",
            json={"question": "What are the risk policies?", "target_departments": ["risk"]},
            headers=h,
        )
        assert r.status_code == 200
        body = r.json()
        if body["status"] == "answered":
            assert "risk" in body["source_departments"]

    def test_e19_chat_confidence_between_0_and_1(self, index_ready: bool) -> None:
        """Confidence score is always in [0, 1]."""
        if not index_ready:
            pytest.skip("Requires indexed KB")
        r = _chat("What is the bank partnerships SLA?")
        assert r.status_code == 200
        body = r.json()
        assert 0.0 <= body["confidence"] <= 1.0

    def test_e20_chat_feedback_id_is_uuid(self, index_ready: bool) -> None:
        """feedback_id returned by /chat is a valid UUID."""
        if not index_ready:
            pytest.skip("Requires indexed KB")
        r = _chat("What is the escalation process?")
        assert r.status_code == 200
        fid = r.json()["feedback_id"]
        uuid.UUID(fid)  # raises ValueError if not valid UUID

    def test_e21_chat_stream_returns_sse_events(self, index_ready: bool) -> None:
        """POST /chat/stream → SSE stream with data: events."""
        if not index_ready:
            pytest.skip("Requires indexed KB")
        h = {**AUTH, **JSON_CT}
        r = requests.post(
            f"{BASE}/chat/stream",
            json={"question": "What is the escalation process?"},
            headers=h,
            stream=True,
        )
        assert r.status_code == 200
        lines = []
        for chunk in r.iter_lines(decode_unicode=True):
            if chunk:
                lines.append(chunk)
            if len(lines) >= 5:
                break
        assert any(line.startswith("data:") for line in lines), f"No SSE events in: {lines}"


# ── 5. Feedback Endpoint ─────────────────────────────────────────────────────


class TestFeedbackEndpoint:
    def test_e22_feedback_unknown_id_returns_404(self) -> None:
        """POST /feedback with non-existent feedback_id → 404."""
        h = {**AUTH, **JSON_CT}
        r = requests.post(
            f"{BASE}/feedback",
            json={"feedback_id": "fb-00000000-0000-0000-0000-000000000001", "rating": "up"},
            headers=h,
        )
        assert r.status_code == 404

    def test_e23_feedback_invalid_rating_returns_422(self) -> None:
        """POST /feedback with rating='thumbs_up' (wrong value) → 422."""
        h = {**AUTH, **JSON_CT}
        r = requests.post(
            f"{BASE}/feedback",
            json={"feedback_id": "fb-abc", "rating": "thumbs_up"},
            headers=h,
        )
        assert r.status_code == 422

    def test_e24_feedback_missing_rating_returns_422(self) -> None:
        """POST /feedback without rating field → 422."""
        h = {**AUTH, **JSON_CT}
        r = requests.post(
            f"{BASE}/feedback",
            json={"feedback_id": "fb-abc"},
            headers=h,
        )
        assert r.status_code == 422

    def test_e25_feedback_round_trip(self, index_ready: bool) -> None:
        """Full round-trip: chat → get feedback_id → submit thumbs_up → 204."""
        if not index_ready:
            pytest.skip("Requires indexed KB to get a real feedback_id")
        chat_r = _chat("What is the escalation process?")
        assert chat_r.status_code == 200
        fid = chat_r.json()["feedback_id"]

        h = {**AUTH, **JSON_CT}
        fb_r = requests.post(
            f"{BASE}/feedback",
            json={"feedback_id": fid, "rating": "up", "comment": "Helpful answer"},
            headers=h,
        )
        assert fb_r.status_code == 204

    def test_e26_feedback_thumbs_down_with_comment(self, index_ready: bool) -> None:
        """POST /feedback with rating='down' and comment → 204."""
        if not index_ready:
            pytest.skip("Requires indexed KB to get a real feedback_id")
        chat_r = _chat("What is the KYC process?")
        assert chat_r.status_code == 200
        fid = chat_r.json()["feedback_id"]

        h = {**AUTH, **JSON_CT}
        fb_r = requests.post(
            f"{BASE}/feedback",
            json={"feedback_id": fid, "rating": "down", "comment": "Answer was incomplete"},
            headers=h,
        )
        assert fb_r.status_code == 204


# ── 6. Sync Status ───────────────────────────────────────────────────────────


class TestSyncStatus:
    def test_e27_sync_status_returns_sources_array(self) -> None:
        """GET /sync/status → sources array with confluence and gdrive entries."""
        r = _get("/sync/status")
        assert r.status_code == 200
        body = r.json()
        sources = {s["source"] for s in body["sources"]}
        assert "confluence" in sources
        assert "gdrive" in sources

    def test_e28_sync_status_has_expected_fields(self) -> None:
        """GET /sync/status sources have state, doc_count, chunk_count fields."""
        body = _get("/sync/status").json()
        for src in body["sources"]:
            assert "state" in src
            assert "doc_count" in src
            assert "chunk_count" in src
            assert src["state"] in ("idle", "running", "done", "error")


# ── 7. Dashboard ─────────────────────────────────────────────────────────────


class TestDashboard:
    def test_e29_dashboard_returns_metrics(self) -> None:
        """GET /api/dashboard → metrics object with expected numeric fields."""
        r = _get("/api/dashboard")
        assert r.status_code == 200
        body = r.json()
        assert "query_count" in body
        assert "deflection_rate" in body
        assert "answered_wrong_rate" in body
        assert "feedback_up" in body
        assert "feedback_down" in body

    def test_e30_dashboard_rates_between_0_and_1(self) -> None:
        """GET /api/dashboard → all rate fields are in [0.0, 1.0]."""
        body = _get("/api/dashboard").json()
        for key in ("deflection_rate", "answered_wrong_rate", "refusal_rate", "partial_rate"):
            val = body.get(key, 0.0)
            assert 0.0 <= val <= 1.0, f"{key}={val} out of [0,1]"
