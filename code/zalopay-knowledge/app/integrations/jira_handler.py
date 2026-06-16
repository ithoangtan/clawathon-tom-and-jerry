from __future__ import annotations

"""Handle a normalised Jira event: resolve workflow → match trigger → act.

Stateless ECA (event → condition → action) reaction layer for the workflow
platform (S2). Flow:

1. Read the ticket's labels; find ``agent-wf-<page_id>`` (set by the executor
   when it first ran the workflow for that ticket).
2. Load + parse that workflow page → :class:`WorkflowDefinition`.
3. Match the event against the page's ``## Triggers`` rules.
4. Run the matched ``action`` (LLM-driven over ticket + RAG context) and apply
   side-effects: always post the result as a Jira comment; if the action refers
   to Confluence, append the result to the workflow page.

Every failure degrades to a structured result dict — never raises to the route.
"""

import json
import logging
from datetime import datetime, timezone

from app.adapters.confluence_writer import text_to_storage
from app.config import Settings, get_settings
from app.integrations.jira_events import JiraEvent
from app.integrations.source_links import resolve_description_sources
from app.ports.confluence_writer import ConfluenceWriterPort
from app.ports.errors import ConfluenceUnavailable, JiraUnavailable, RetrieverUnavailable, WorkflowParseError
from app.ports.jira import JiraPort
from app.ports.llm import LLMPort
from app.ports.retriever import RetrieverPort
from app.ports.types import ModelTier
from app.workflow.labels import WORKFLOW_LABEL_PREFIX
from app.workflow.parser import parse_workflow
from app.workflow.reactions import apply_reactions, parse_decision
from app.workflow.triggers import match_trigger

logger = logging.getLogger(__name__)

_CONFLUENCE_HINTS = ("confluence", "wiki", "page", "trang", "cập nhật page", "update page")
_TESTING_LABEL = "testing"


def handle_jira_event(
    event: JiraEvent,
    *,
    llm: LLMPort,
    retriever: RetrieverPort,
    jira: JiraPort,
    confluence_writer: ConfluenceWriterPort,
    settings: Settings | None = None,
) -> dict:
    """React to *event*. Returns a structured result (never raises)."""
    cfg = settings or get_settings()

    # 1. Resolve which workflow this ticket belongs to (label set by the executor).
    try:
        issue = jira.get_issue(event.issue_key)
    except JiraUnavailable as exc:
        return _result("error", reason=f"jira_unavailable: {exc}", issue=event.issue_key)
    labels = (issue.get("fields") or {}).get("labels") or []

    # ── Testing mode: ticket labelled `testing` → echo the webhook payload as a
    # JSON code-block comment (debug/visibility). No workflow resolution. ──────
    if any(str(lbl).lower() == _TESTING_LABEL for lbl in labels):
        return _testing_echo(event, jira)

    wf_label = next((lbl for lbl in labels if lbl.startswith(WORKFLOW_LABEL_PREFIX)), None)
    if not wf_label:
        return _result("ignored", reason="no_workflow_label", issue=event.issue_key)

    # 2. Resolve the workflow page from its identity label, then load it.
    try:
        page_id = _resolve_page_id(retriever, wf_label)
        if not page_id:
            return _result("ignored", reason="workflow_not_found", issue=event.issue_key, wf_label=wf_label)
        chunks = retriever.get_page_chunks(department="workflow", page_id=page_id)
    except RetrieverUnavailable as exc:
        return _result("error", reason=f"retriever_unavailable: {exc}", issue=event.issue_key)
    page_text = "\n\n".join((c.text or "") for c in chunks).strip()
    if not page_text:
        return _result("ignored", reason="workflow_page_empty", issue=event.issue_key, page_id=page_id)
    # The page title (= workflow name) lives in chunk metadata, not the body —
    # prepend it as the H1 so the parser names the workflow correctly.
    title = chunks[0].title if chunks else None
    if title and title.lower() not in page_text[:200].lower():
        page_text = f"# {title}\n\n{page_text}"
    try:
        defn = parse_workflow(page_text, llm=llm, settings=cfg)
    except WorkflowParseError as exc:
        return _result("error", reason=f"parse_failed: {exc}", issue=event.issue_key, page_id=page_id)

    # 3. Match a trigger.
    trig = match_trigger(event, defn)
    if trig is None:
        return _result("no_trigger_matched", issue=event.issue_key, page_id=page_id,
                       workflow=defn.name, n_triggers=len(defn.triggers))

    # 4. Run the action (LLM) + side-effects.
    result_text = _run_action(
        event, issue, defn, trig.action, llm=llm, retriever=retriever, jira=jira, cfg=cfg
    )

    out: dict = {
        "status": "acted",
        "issue": event.issue_key,
        "page_id": page_id,
        "workflow": defn.name,
        "trigger_action": trig.action,
        "jira_comment": None,
        "confluence_updated": False,
    }

    # 4a. Always post the result as a Jira comment (visible, safe side-effect).
    try:
        res = jira.add_comment(key=event.issue_key, body=f"[Agent · {defn.name}]\n\n{result_text}")
        out["jira_comment"] = {"dry_run": bool(res.get("dry_run")), "url": res.get("url")}
    except JiraUnavailable as exc:
        out["jira_comment"] = {"error": str(exc)}

    # 4b. If the action references Confluence, append the result to the workflow page.
    if any(h in trig.action.lower() for h in _CONFLUENCE_HINTS):
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        fragment = f"<h3>Agent run — {ts} ({event.issue_key})</h3>" + text_to_storage(result_text)
        try:
            confluence_writer.append_to_page(page_id=page_id, html_fragment=fragment)
            out["confluence_updated"] = True
        except ConfluenceUnavailable as exc:
            out["confluence_error"] = str(exc)

    # 4c. Decision-driven reactions — verbs declared on the page (## Reactions),
    # not hardcoded here: reassign / label / append_confluence. Comment-only when
    # the workflow declares no Reactions table (backward compatible).
    decision = parse_decision(result_text)
    out["decision"] = decision
    out["reactions"] = apply_reactions(
        decision, defn,
        issue_key=event.issue_key, report_text=result_text, issue=issue,
        jira=jira, confluence_writer=confluence_writer, page_id=page_id,
    )

    logger.info(
        "Jira event handled: issue=%s workflow=%r action=%r decision=%s jira=%s confluence=%s reactions=%s",
        event.issue_key, defn.name, trig.action, decision,
        out["jira_comment"], out["confluence_updated"], out["reactions"].get("verbs"),
    )
    return out


def _testing_echo(event: JiraEvent, jira: JiraPort) -> dict:
    """Echo the raw webhook payload back to the ticket as a JSON code block."""
    payload = event.raw or {
        k: v for k, v in {
            "event_type": event.event_type,
            "issue_key": event.issue_key,
            "status_from": event.status_from,
            "status_to": event.status_to,
            "field": event.field,
            "field_from": event.field_from,
            "field_to": event.field_to,
            "comment_body": event.comment_body,
            "actor_account_id": event.actor_account_id,
            "event_id": event.event_id,
        }.items() if v is not None
    }
    body_json = json.dumps(payload, ensure_ascii=False, indent=2)
    intro = "🧪 [Agent · testing] Webhook payload nhận được:"
    try:
        res = jira.add_comment(key=event.issue_key, body=intro, code_block=body_json, code_language="json")
        return _result(
            "acted", mode="testing", issue=event.issue_key,
            jira_comment={"dry_run": bool(res.get("dry_run")), "url": res.get("url")},
        )
    except JiraUnavailable as exc:
        return _result("error", mode="testing", reason=str(exc), issue=event.issue_key)


def _resolve_page_id(retriever: RetrieverPort, wf_label: str) -> str | None:
    """Find the workflow page id for *wf_label* via a label-filtered search.

    The workflow page carries the same ``wf-<slug>`` label, so an exact
    label filter pins it down; we return the best-scoring page's ``source``.
    """
    hits = retriever.search(
        department="workflow",
        query=wf_label.replace(WORKFLOW_LABEL_PREFIX, "").replace("-", " "),
        k=5,
        filters={"labels": ["zalopay-workflow", wf_label]},
    )
    best_id, best_score = None, float("-inf")
    for h in hits:
        if h.source and h.score > best_score:
            best_id, best_score = h.source, h.score
    return best_id


def _run_action(
    event: JiraEvent,
    issue: dict,
    defn,
    action: str,
    *,
    llm: LLMPort,
    retriever: RetrieverPort,
    jira: JiraPort,
    cfg: Settings,
) -> str:
    """Produce the action result text via the LLM.

    Grounding sources, in order: (1) the in-system documents linked from the
    ticket Description (Confluence/Jira/GDrive — see :mod:`source_links`),
    (2) the zalopay wiki via RAG. The review questions are read from the
    workflow page's step checklists (data, not hardcoded).
    """
    context = [
        f"Workflow: {defn.name}",
        f"Ticket {event.issue_key}: {issue.get('summary', '')} (status: {issue.get('status', '')})",
        _event_description(event),
    ]

    # 1. In-system documents referenced in the ticket Description (campaign spec…).
    description = (issue.get("fields") or {}).get("description")
    resolution = resolve_description_sources(description, settings=cfg, jira=jira)
    for src in resolution.sources:
        context.append(f"[tài liệu · {src.kind} · {src.title}]\n{src.text}")
    if resolution.skipped_external or resolution.unreadable:
        notes = []
        if resolution.skipped_external:
            notes.append(f"{resolution.skipped_external} link ngoài hệ thống (không hỗ trợ)")
        if resolution.unreadable:
            notes.append(f"{resolution.unreadable} link in-system không đọc được")
        context.append("(Lưu ý: đã bỏ qua " + "; ".join(notes) + ".)")

    # 2. zalopay wiki grounding (RAG) using the action text as the query. Pull enough
    # policy text that the rule definitions are present (else the LLM over-marks "Chưa rõ").
    try:
        hits = retriever.search(department="risk", query=action, k=6, language="vi")
        for h in hits:
            context.append(f"[chính sách] {h.title}: {(h.text or '')[:1500]}")
    except RetrieverUnavailable:
        pass

    # Review questions + valid decisions live on the workflow page — data, not code.
    questions = [item for step in defn.steps for item in (step.checklist or [])]
    decisions = [r.decision for r in (defn.reactions or []) if r.decision]
    spec_parts: list[str] = []
    if questions:
        q_block = "\n".join(f"- {q}" for q in questions)
        spec_parts.append(
            "Mỗi mục dưới đây ĐÃ nêu sẵn tiêu chí của rule — hãy đánh giá campaign spec "
            "theo đúng tiêu chí đó, KHÔNG đợi tài liệu policy lặp lại rule. Format: "
            '"- <mục>: **Comply/Violate/Chưa rõ** — <dẫn chứng ngắn từ campaign spec>":\n'
            f"{q_block}\n"
            'Chỉ ghi "Chưa rõ" khi CHÍNH CAMPAIGN SPEC thiếu thông tin để kết luận '
            "(không phải vì thiếu tài liệu policy). Nếu campaign spec nêu rõ đã đáp ứng "
            "tiêu chí → **Comply**."
        )
    else:
        spec_parts.append("Trả về kết quả ngắn gọn, có căn cứ.")
    if decisions:
        spec_parts.append(
            "Kết thúc bằng đúng MỘT dòng cuối: `DECISION: X` — với X là MỘT trong "
            f"[{', '.join(decisions)}]."
        )
    answer_spec = "\n\n".join(spec_parts)

    prompt = (
        f"Bạn là agent review rủi ro, vận hành theo workflow \"{defn.name}\". "
        f"Một sự kiện vừa xảy ra trên Jira. Thực hiện chỉ thị dưới đây, CHỈ dựa trên "
        f"tài liệu campaign và chính sách được cung cấp trong phần Ngữ cảnh — không bịa, "
        f"không dùng kiến thức ngoài. Trả lời bằng tiếng Việt, ngắn gọn.\n\n"
        f"Chỉ thị: {action}\n\n{answer_spec}\n\nNgữ cảnh:\n" + "\n".join(context)
    )
    try:
        res = llm.complete(
            tier=ModelTier.MAIN,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            timeout_s=cfg.branch_timeout_s,
        )
        return (res.text or "").strip() or f"(Đã xử lý: {action})"
    except Exception as exc:  # noqa: BLE001 — degrade to a plain note
        logger.warning("Jira action LLM failed: %s", exc)
        return f"(Không tạo được nội dung tự động cho: {action})"


def _event_description(event: JiraEvent) -> str:
    if event.event_type == "status_changed":
        return f"Sự kiện: status đổi {event.status_from} → {event.status_to}."
    if event.event_type == "comment_added":
        return f"Sự kiện: có comment mới: {event.comment_body}"
    if event.event_type == "field_changed":
        return f"Sự kiện: field {event.field} đổi {event.field_from} → {event.field_to}."
    return "Sự kiện: ticket được cập nhật."


def _result(status: str, **kw) -> dict:
    return {"status": status, **kw}
