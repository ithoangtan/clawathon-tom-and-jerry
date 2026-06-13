from __future__ import annotations

"""PII masking for audit logs and dashboard history (FR-7.1 / §8)."""

import re

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
# Match full VN numbers including leading "+" on +84… forms. Avoid trailing \b on
# the +84 branch — word boundaries sit between "+" and digits and can leave "+".
_PHONE_RE = re.compile(r"\+84\d{9}|0\d{9}(?!\d)")
_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def mask_pii(text: str) -> str:
    """Mask common PII patterns in *text* for safe logging."""
    if not text:
        return text
    masked = _EMAIL_RE.sub("[email]", text)
    masked = _PHONE_RE.sub("[phone]", masked)
    masked = _CARD_RE.sub("[card]", masked)
    return masked
