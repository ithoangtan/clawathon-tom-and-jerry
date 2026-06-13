from __future__ import annotations

"""Gateway trust and security helpers for AgentBase identity headers."""

import hmac
from typing import Mapping

# Identity headers that must originate from a trusted gateway, not the browser.
HEADER_USER = "X-GreenNode-AgentBase-User-Id"
HEADER_SESSION = "X-GreenNode-AgentBase-Session-Id"
HEADER_ROLE = "X-GreenNode-AgentBase-Role"
HEADER_HOME = "X-GreenNode-AgentBase-Home-Department"
HEADER_GATEWAY_VERIFIED = "X-GreenNode-AgentBase-Gateway-Verified"
HEADER_GATEWAY_TRUST = "X-GreenNode-AgentBase-Gateway-Trust"

PROTECTED_IDENTITY_HEADERS = frozenset(
    {
        HEADER_USER,
        HEADER_SESSION,
        HEADER_ROLE,
        HEADER_HOME,
    }
)

AGENTBASE_HEADER_PREFIX = "x-greennode-agentbase-"


def _normalize_headers(headers: Mapping[str, str]) -> dict[str, str]:
    return {k.lower(): v for k, v in headers.items()}


def has_protected_identity_headers(headers: Mapping[str, str]) -> bool:
    """True when any AgentBase identity header is present on the request."""
    normalized = _normalize_headers(headers)
    return any(
        normalized.get(name.lower()) is not None for name in PROTECTED_IDENTITY_HEADERS
    )


def has_any_agentbase_headers(headers: Mapping[str, str]) -> bool:
    """True when any ``X-GreenNode-AgentBase-*`` header is present."""
    normalized = _normalize_headers(headers)
    return any(k.startswith(AGENTBASE_HEADER_PREFIX) for k in normalized)


def is_gateway_verified(headers: Mapping[str, str], *, trust_secret: str) -> bool:
    """Return True when the request carries a gateway trust marker.

    Two modes:
    - ``GATEWAY_TRUST_SECRET`` unset: require ``Gateway-Verified: true`` (platform/gateway marker).
    - Secret set: require ``Gateway-Trust`` HMAC over ``user_id:session_id``.
    """
    normalized = _normalize_headers(headers)
    if trust_secret:
        token = (normalized.get(HEADER_GATEWAY_TRUST.lower()) or "").strip()
        user_id = (normalized.get(HEADER_USER.lower()) or "").strip()
        session_id = (normalized.get(HEADER_SESSION.lower()) or "").strip()
        if not token or not user_id or not session_id:
            return False
        expected = hmac.new(
            trust_secret.encode("utf-8"),
            f"{user_id}:{session_id}".encode("utf-8"),
            digestmod="sha256",
        ).hexdigest()
        return hmac.compare_digest(token, expected)

    user_id = (normalized.get(HEADER_USER.lower()) or "").strip()
    session_id = (normalized.get(HEADER_SESSION.lower()) or "").strip()
    if not user_id or not session_id:
        return False

    verified = (normalized.get(HEADER_GATEWAY_VERIFIED.lower()) or "").strip().lower()
    return verified in {"1", "true", "yes"}


def build_gateway_trust_token(user_id: str, session_id: str, secret: str) -> str:
    """HMAC token for gateway-injected trust header."""
    return hmac.new(
        secret.encode("utf-8"),
        f"{user_id}:{session_id}".encode("utf-8"),
        digestmod="sha256",
    ).hexdigest()


def apply_gateway_trust_headers(
    headers: dict[str, str],
    *,
    user_id: str,
    session_id: str,
    trust_secret: str,
) -> None:
    """Mark identity headers as gateway-verified (platform / trusted proxy)."""
    if trust_secret:
        headers[HEADER_GATEWAY_TRUST] = build_gateway_trust_token(
            user_id, session_id, trust_secret
        )
    else:
        headers[HEADER_GATEWAY_VERIFIED] = "true"


def validate_gateway_trust(
    headers: Mapping[str, str],
    *,
    trust_required: bool,
    trust_secret: str,
) -> str | None:
    """Reject client-supplied AgentBase headers when gateway trust is required.

    Any ``X-GreenNode-AgentBase-*`` header must be accompanied by a valid
    gateway trust marker (HMAC or ``Gateway-Verified``). Returns an error
    message suitable for HTTP 403, or ``None`` when allowed.
    """
    if not trust_required:
        return None
    if not has_any_agentbase_headers(headers):
        return None
    if is_gateway_verified(headers, trust_secret=trust_secret):
        return None
    return (
        "Client-supplied X-GreenNode-AgentBase-* headers rejected; "
        "requests must pass through the trusted gateway"
    )


class AgentDisabledError(RuntimeError):
    """Raised when the kill-switch disables chat/sync paths."""


def assert_agent_enabled(*, agent_enabled: bool) -> None:
    """Raise :class:`AgentDisabledError` when the kill-switch is active."""
    if not agent_enabled:
        raise AgentDisabledError("Knowledge agent is temporarily disabled")
