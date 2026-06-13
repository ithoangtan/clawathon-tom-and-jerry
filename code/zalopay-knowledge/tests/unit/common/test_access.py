"""Department access control message tests — FR-7.2."""

from __future__ import annotations

from app.common.access import ACCESS_DENIED_ERROR, access_denied_message


def test_access_denied_error_constant():
    assert ACCESS_DENIED_ERROR == "access_denied"


def test_access_denied_message_english():
    msg = access_denied_message("en", ["grow_enablement"])
    assert "permission" in msg.lower()
    assert "administrator" in msg.lower()
    assert "teams-grow-enablement-knowledge" in msg


def test_access_denied_message_vietnamese():
    msg = access_denied_message("vi", ["risk"])
    assert "quyền" in msg.lower()
    assert "quản trị" in msg.lower()
    assert "teams-risk-knowledge" in msg
