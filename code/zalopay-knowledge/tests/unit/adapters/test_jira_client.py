from __future__ import annotations

"""JiraClient tests — credential reuse, request shaping, dry-run, graceful errors.
httpx is mocked; no network or real Jira instance needed."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.adapters.jira_client import JiraClient, NullJiraClient, _to_adf
from app.config import Settings
from app.ports.errors import JiraUnavailable


def _settings(**overrides) -> Settings:
    base = dict(
        app_env="local",
        confluence_base_url="https://ithoangtan-clawathon.atlassian.net/wiki",
        confluence_email="ithoangtan@gmail.com",
        confluence_api_token="test-token",
    )
    base.update(overrides)
    return Settings(_env_file=None, **base)


def _patched_request(resp_json: dict | None = None, *, status: int = 200, content: bytes = b"{}"):
    """Patch httpx.Client to return a fake response; returns (patch_ctx, fake_client)."""
    fake_resp = MagicMock()
    fake_resp.json.return_value = resp_json or {}
    fake_resp.content = content
    fake_resp.raise_for_status.return_value = None
    fake_client = MagicMock()
    fake_client.request.return_value = fake_resp
    ctx = patch("app.adapters.jira_client.httpx.Client")
    return ctx, fake_client, fake_resp


def _bind(ctx, fake_client) -> None:
    mock_cls = ctx.start()
    mock_cls.return_value.__enter__.return_value = fake_client


# ── _to_adf ──────────────────────────────────────────────────────────────────

class TestToAdf:
    def test_single_line(self) -> None:
        adf = _to_adf("hello")
        assert adf["type"] == "doc"
        assert adf["content"][0]["content"][0]["text"] == "hello"

    def test_multiline_becomes_paragraphs(self) -> None:
        adf = _to_adf("a\nb")
        assert len(adf["content"]) == 2

    def test_empty_text_has_one_empty_paragraph(self) -> None:
        adf = _to_adf("")
        assert adf["content"] == [{"type": "paragraph", "content": []}]

    def test_code_block_appended(self) -> None:
        adf = _to_adf("intro", code_block='{"a": 1}', code_language="json")
        cb = adf["content"][-1]
        assert cb["type"] == "codeBlock"
        assert cb["attrs"]["language"] == "json"
        assert cb["content"][0]["text"] == '{"a": 1}'


# ── config / base URL ──────────────────────────────────────────────────────────

def test_base_url_strips_wiki_suffix() -> None:
    client = JiraClient(_settings())
    assert client._base == "https://ithoangtan-clawathon.atlassian.net"


def test_configured_true_with_token() -> None:
    assert JiraClient(_settings()).configured() is True


def test_configured_false_without_token() -> None:
    assert JiraClient(_settings(confluence_api_token="")).configured() is False


def test_browse_url() -> None:
    client = JiraClient(_settings())
    assert client._browse_url("KAN-1") == "https://ithoangtan-clawathon.atlassian.net/browse/KAN-1"


# ── get_issue ───────────────────────────────────────────────────────────────────

def test_get_issue_returns_key_url_summary_status() -> None:
    ctx, fake_client, _ = _patched_request(
        {"key": "KAN-1", "fields": {"summary": "Demo", "status": {"name": "To Do"}}}
    )
    _bind(ctx, fake_client)
    try:
        result = JiraClient(_settings()).get_issue("KAN-1")
    finally:
        ctx.stop()

    method, url = fake_client.request.call_args.args
    assert method == "GET"
    assert url.endswith("/rest/api/3/issue/KAN-1")
    assert result["key"] == "KAN-1"
    assert result["url"].endswith("/browse/KAN-1")
    assert result["summary"] == "Demo"
    assert result["status"] == "To Do"


# ── create_issue ─────────────────────────────────────────────────────────────────

def test_create_issue_posts_expected_fields_with_default_project() -> None:
    ctx, fake_client, _ = _patched_request({"key": "KAN-42"})
    _bind(ctx, fake_client)
    try:
        result = JiraClient(_settings()).create_issue(summary="Review campaign", description="body")
    finally:
        ctx.stop()

    kwargs = fake_client.request.call_args.kwargs
    fields = kwargs["json"]["fields"]
    assert fields["project"] == {"key": "KAN"}  # hardcoded default
    assert fields["summary"] == "Review campaign"
    assert fields["issuetype"] == {"name": "Task"}
    assert fields["description"]["type"] == "doc"  # ADF-wrapped
    assert result["key"] == "KAN-42"
    assert result["url"].endswith("/browse/KAN-42")
    assert result["dry_run"] is False


def test_create_subtask_includes_parent() -> None:
    ctx, fake_client, _ = _patched_request({"key": "KAN-43"})
    _bind(ctx, fake_client)
    try:
        JiraClient(_settings()).create_issue(
            summary="KYC check", issuetype="Sub-task", parent="KAN-1"
        )
    finally:
        ctx.stop()

    fields = fake_client.request.call_args.kwargs["json"]["fields"]
    assert fields["parent"] == {"key": "KAN-1"}
    assert fields["issuetype"] == {"name": "Sub-task"}


# ── add_comment ──────────────────────────────────────────────────────────────────

def test_add_comment_posts_adf_body() -> None:
    ctx, fake_client, _ = _patched_request({"id": "10001"})
    _bind(ctx, fake_client)
    try:
        result = JiraClient(_settings()).add_comment(key="KAN-1", body="risk assessment done")
    finally:
        ctx.stop()

    method, url = fake_client.request.call_args.args
    body = fake_client.request.call_args.kwargs["json"]["body"]
    assert method == "POST"
    assert url.endswith("/rest/api/3/issue/KAN-1/comment")
    assert body["type"] == "doc"
    assert result["comment_id"] == "10001"


# ── dry_run ──────────────────────────────────────────────────────────────────────

def test_dry_run_create_does_no_network() -> None:
    with patch("app.adapters.jira_client.httpx.Client") as mock_cls:
        result = JiraClient(_settings(), dry_run=True).create_issue(summary="x")
    mock_cls.assert_not_called()
    assert result["dry_run"] is True
    assert result["key"] == "DRY-RUN"


def test_dry_run_comment_does_no_network() -> None:
    with patch("app.adapters.jira_client.httpx.Client") as mock_cls:
        result = JiraClient(_settings(), dry_run=True).add_comment(key="KAN-1", body="x")
    mock_cls.assert_not_called()
    assert result["dry_run"] is True


# ── error handling ────────────────────────────────────────────────────────────────

def test_http_error_raises_jira_unavailable() -> None:
    request = httpx.Request("POST", "https://x/rest/api/3/issue")
    response = httpx.Response(400, text="bad request", request=request)
    fake_resp = MagicMock()
    fake_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "400", request=request, response=response
    )
    fake_client = MagicMock()
    fake_client.request.return_value = fake_resp
    with patch("app.adapters.jira_client.httpx.Client") as mock_cls:
        mock_cls.return_value.__enter__.return_value = fake_client
        with pytest.raises(JiraUnavailable):
            JiraClient(_settings()).create_issue(summary="x")


def test_request_when_unconfigured_raises() -> None:
    with pytest.raises(JiraUnavailable):
        JiraClient(_settings(confluence_api_token="")).get_issue("KAN-1")


def test_is_ready_false_when_unconfigured() -> None:
    assert JiraClient(_settings(confluence_api_token="")).is_ready() is False


def test_is_ready_true_when_myself_ok() -> None:
    ctx, fake_client, _ = _patched_request({"accountId": "abc"})
    _bind(ctx, fake_client)
    try:
        assert JiraClient(_settings()).is_ready() is True
    finally:
        ctx.stop()


# ── NullJiraClient ────────────────────────────────────────────────────────────────

class TestNullJiraClient:
    def test_actions_raise(self) -> None:
        null = NullJiraClient()
        with pytest.raises(JiraUnavailable):
            null.get_issue("KAN-1")
        with pytest.raises(JiraUnavailable):
            null.create_issue(summary="x")
        with pytest.raises(JiraUnavailable):
            null.add_comment(key="KAN-1", body="x")

    def test_is_ready_false(self) -> None:
        assert NullJiraClient().is_ready() is False
