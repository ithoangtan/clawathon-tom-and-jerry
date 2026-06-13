from __future__ import annotations

import pytest

from app.common.security import (
    build_gateway_trust_token,
    has_any_agentbase_headers,
    is_gateway_verified,
    validate_gateway_trust,
)
from app.config import Settings


class TestSecurityHelpers:
    def test_validate_rejects_unverified_client_headers(self) -> None:
        error = validate_gateway_trust(
            {
                "X-GreenNode-AgentBase-User-Id": "spoofed",
                "X-GreenNode-AgentBase-Session-Id": "sess",
            },
            trust_required=True,
            trust_secret="",
        )
        assert error is not None
        assert "rejected" in error

    def test_validate_allows_verified_headers(self) -> None:
        error = validate_gateway_trust(
            {
                "X-GreenNode-AgentBase-User-Id": "user",
                "X-GreenNode-AgentBase-Session-Id": "sess",
                "X-GreenNode-AgentBase-Gateway-Verified": "true",
            },
            trust_required=True,
            trust_secret="",
        )
        assert error is None

    def test_hmac_trust_token_roundtrip(self) -> None:
        secret = "rotate-me"
        token = build_gateway_trust_token("user-1", "sess-1", secret)
        assert is_gateway_verified(
            {
                "X-GreenNode-AgentBase-User-Id": "user-1",
                "X-GreenNode-AgentBase-Session-Id": "sess-1",
                "X-GreenNode-AgentBase-Gateway-Trust": token,
            },
            trust_secret=secret,
        )

    def test_rejects_spoofed_gateway_verified_marker_alone(self) -> None:
        error = validate_gateway_trust(
            {"X-GreenNode-AgentBase-Gateway-Verified": "true"},
            trust_required=True,
            trust_secret="",
        )
        assert error is not None

    def test_has_any_agentbase_headers(self) -> None:
        assert has_any_agentbase_headers(
            {"X-GreenNode-AgentBase-Gateway-Verified": "true"}
        )
        assert not has_any_agentbase_headers({"Authorization": "Bearer x"})

    def test_tls_enforced_on_llm_url(self) -> None:
        with pytest.raises(ValueError, match="LLM_BASE_URL must use https"):
            Settings(llm_base_url="http://insecure.example/v1", log_level="error")
