from __future__ import annotations

"""Product-facing copy for refusals, escalation, scope, and disclaimers (PM MUST 🟢)."""

from typing import Any

from app.common.departments import all_departments, get_department, iter_keys

HIGH_STAKES_DOC_TYPES = frozenset({"Risk", "Security", "RCA"})
_HIGH_STAKES_TITLE_KEYWORDS = (
    "policy",
    "compliance",
    "sla",
    "threshold",
    "regulatory",
    "fraud",
    "kyc",
    "aml",
)


def mvp_department_names(lang: str = "en") -> str:
    """Comma-separated display names for the three MVP departments."""
    return ", ".join(d.display_name(lang) for d in all_departments())


def out_of_scope_notice(lang: str = "en") -> str:
    """Explicit out-of-scope definition — locked to MVP corpus boundaries."""
    names = mvp_department_names(lang)
    if lang == "vi":
        return (
            f"Phạm vi MVP: chỉ tài liệu nội bộ của {names}. "
            "Không tra cứu internet, dữ liệu thời gian thực, HR/pháp lý ngoài phạm vi, "
            "và không thực hiện hành động trên hệ thống."
        )
    return (
        f"MVP scope: internal docs for {names} only. "
        "No web search, no live/real-time data, no HR or legal topics outside those teams, "
        "and no system actions."
    )


def escalation_hint(lang: str = "en", departments: list[str] | None = None) -> str:
    """Useful escalation path on refusal — static Teams channel + owner pointer."""
    keys = [d for d in (departments or []) if d in set(iter_keys())]
    if not keys:
        keys = list(iter_keys())

    lines: list[str] = []
    for key in keys:
        dept = get_department(key)
        if lang == "vi":
            lines.append(
                f"- **{dept.display_name('vi')}**: Teams **{dept.display_name('vi')}** "
                f"hoặc {dept.head_manager_vi} (trưởng bộ phận)"
            )
        else:
            lines.append(
                f"- **{dept.display_name('en')}**: Teams **{dept.display_name('en')}** "
                f"or {dept.head_manager_en} (department head)"
            )

    header = (
        "**Liên hệ tiếp:**"
        if lang == "vi"
        else "**Next step — ask a human:**"
    )
    return f"{header}\n" + "\n".join(lines)


def refusal_body(lang: str = "en", departments: list[str] | None = None) -> str:
    """Full refusal message with escalation pointer and scope notice."""
    if lang == "vi":
        lead = (
            "Không có thông tin trong tài liệu.\n\n"
            "Tôi không tìm thấy nội dung liên quan trong tài liệu nội bộ được phép. "
            "Hãy thử hỏi cụ thể hơn hoặc liên hệ bộ phận sở hữu tài liệu."
        )
    else:
        lead = (
            "Not covered in the docs.\n\n"
            "I couldn't find relevant content in the permitted internal documentation. "
            "Try rephrasing your question or contact the document owner."
        )
    return f"{lead}\n\n{escalation_hint(lang, departments)}\n\n{out_of_scope_notice(lang)}"


def high_stakes_disclaimer(lang: str, owner: str, as_of: str) -> str:
    """High-stakes disclaimer pattern: verify with owner, as of date."""
    if lang == "vi":
        return f"_Vui lòng xác minh với {owner}, tính đến {as_of}._"
    return f"_Verify with {owner}, as of {as_of}._"


_HIGH_STAKES_KEYWORDS = _HIGH_STAKES_TITLE_KEYWORDS + (
    "settlement",
    "reconciliation",
)


def is_high_stakes_content(
    *,
    citations: list[dict] | None,
    departments: list[str] | None = None,
    answer: str = "",
) -> bool:
    """True when answer cites policy/compliance/risk/SLA-class sources."""
    norm_answer = answer.lower()
    if any(kw in norm_answer for kw in _HIGH_STAKES_KEYWORDS):
        return True
    for cite in citations or []:
        doc_type = (cite.get("doc_type") or "").strip()
        if doc_type in HIGH_STAKES_DOC_TYPES:
            return True
        title = (cite.get("title") or "").lower()
        if any(kw in title for kw in _HIGH_STAKES_KEYWORDS):
            return True
    return False


def maybe_append_high_stakes_disclaimer(
    answer: str,
    *,
    lang: str,
    citations: list[dict] | None,
    departments: list[str] | None = None,
) -> str:
    """Append disclaimer when content is high-stakes and not already present."""
    if not answer.strip():
        return answer
    if "verify with" in answer.lower() or "xác minh với" in answer.lower():
        return answer
    if not is_high_stakes_content(citations=citations, departments=departments, answer=answer):
        return answer

    owner_keys = [d for d in (departments or []) if d in set(iter_keys())]
    if not owner_keys:
        owner_keys = [next(iter_keys())]
    owner = get_department(owner_keys[0]).display_name(lang)

    dates = [c.get("last_modified") for c in (citations or []) if c.get("last_modified")]
    as_of = max(dates) if dates else "the cited source date"
    line = high_stakes_disclaimer(lang, owner, as_of)
    return f"{answer.rstrip()}\n\n{line}"


def is_high_stakes_chunk(chunk: dict[str, Any]) -> bool:
    """True when chunk metadata indicates policy/compliance/risk content."""
    doc_type = (chunk.get("doc_type") or "").strip()
    if doc_type in HIGH_STAKES_DOC_TYPES:
        return True
    haystack = f"{chunk.get('title', '')} {chunk.get('text', '')}".lower()
    return any(kw in haystack for kw in _HIGH_STAKES_TITLE_KEYWORDS)


def _disclaimer_owner(chunks: list[dict[str, Any]], lang: str) -> str:
    for chunk in chunks:
        author = (chunk.get("author") or "").strip()
        if author:
            return author
    for chunk in chunks:
        dept_key = chunk.get("department")
        if dept_key:
            dept = get_department(dept_key)
            return dept.head_manager_vi if lang == "vi" else dept.head_manager_en
    return "document owner" if lang != "vi" else "chủ sở hữu tài liệu"


def _disclaimer_as_of(chunks: list[dict[str, Any]]) -> str:
    dates = [str(c.get("last_modified")) for c in chunks if c.get("last_modified")]
    if not dates:
        return "latest indexed version"
    newest = max(dates)
    return newest[:10] if len(newest) >= 10 else newest


def append_high_stakes_disclaimer_if_needed(
    answer: str,
    lang: str,
    cited_chunks: list[dict[str, Any]],
) -> str:
    """Append disclaimer when high-stakes sources were cited (PM MUST 🟢)."""
    if not answer.strip() or not cited_chunks:
        return answer
    if not any(is_high_stakes_chunk(c) for c in cited_chunks):
        return answer
    norm = answer.lower()
    if "verify with" in norm or "xác minh với" in norm:
        return answer
    owner = _disclaimer_owner(cited_chunks, lang)
    as_of = _disclaimer_as_of(cited_chunks)
    disclaimer = high_stakes_disclaimer(lang, owner, as_of)
    return f"{answer.rstrip()}\n\n{disclaimer}"
