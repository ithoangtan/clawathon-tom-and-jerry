from __future__ import annotations

"""Department access control helpers (FR-7.2 / S-C1)."""

ACCESS_DENIED_ERROR = "access_denied"


def access_denied_message(lang: str) -> str:
    """Polite refusal when the user lacks permission for the requested department(s)."""
    if lang == "vi":
        return (
            "Bạn không có quyền truy cập tài liệu của bộ phận này. "
            "Vui lòng liên hệ quản trị viên nếu bạn cần quyền truy cập."
        )
    return (
        "You do not have permission to access this department's knowledge. "
        "Please contact your administrator if you need access."
    )
