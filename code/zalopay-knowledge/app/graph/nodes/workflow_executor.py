from __future__ import annotations

"""``execute_workflow`` node — run a discovered workflow end-to-end in one pass.

Pipeline (after ``discover_workflow`` set ``workflow_page_id``):

1. Load the full workflow page via ``retriever.get_page_chunks``.
2. Parse it into a :class:`WorkflowDefinition` (``parse_workflow``).
3. Enforce the definition-lifecycle gate (``is_executable``) — only ACTIVE runs.
4. Iterate the steps in order, dispatching by ``step.type``:
   fetch / rag / synthesize / checklist / gate / action.
5. Emit a numbered markdown answer + a global citation list.

Every failure mode (no match, parse error, Jira/retriever down, budget exhausted)
degrades to a graceful, cited reply — the node never raises.
"""

import logging
from typing import Callable

from app.common.departments import routable_keys
from app.config import Settings, get_settings
from app.graph.nodes._helpers import budget_exceeded, excerpt_from_text, parse_json_response
from app.graph.state import Citation, GraphState
from app.ports.errors import JiraUnavailable, LLMUnavailable, RetrieverUnavailable, WorkflowParseError
from app.ports.jira import JiraPort
from app.ports.llm import LLMPort
from app.ports.retriever import RetrieverPort
from app.ports.types import ModelTier, RetrievedChunk
from app.workflow.labels import workflow_label
from app.workflow.models import WorkflowDefinition, WorkflowStep
from app.workflow.parser import is_executable, parse_workflow

logger = logging.getLogger(__name__)

_WORKFLOW_DEPT = "workflow"

# Loose mapping from a step's "Responsible: … — Department" to a routable Q&A
# corpus key used for `rag` lookups.
_DOMAIN_ALIASES = {
    "risk": "risk",
    "grow": "grow_enablement",
    "growth": "grow_enablement",
    "enablement": "grow_enablement",
    "product": "grow_enablement",
    "ops": "grow_enablement",
    "bank": "bank_partnerships",
    "partnership": "bank_partnerships",
    "partnerships": "bank_partnerships",
    "bd": "bank_partnerships",
}


def make_execute_workflow_node(
    llm: LLMPort,
    retriever: RetrieverPort,
    jira: JiraPort,
    *,
    settings: Settings | None = None,
) -> Callable[[GraphState], dict]:
    """Build the ``execute_workflow`` node bound to its ports."""
    cfg = settings or get_settings()

    def execute_workflow(state: GraphState) -> dict:
        lang = state.get("request_language", "en")
        deadline = state.get("deadline_ts")
        page_id = state.get("workflow_page_id")

        # ── No workflow discovered → graceful reply ───────────────────────────
        if not page_id:
            note = state.get("workflow_discovery_note") or _t("no_match", lang)
            return _reply(note, status="refused", lang=lang)

        # ── Load the full page ────────────────────────────────────────────────
        try:
            chunks = retriever.get_page_chunks(department=_WORKFLOW_DEPT, page_id=page_id)
        except RetrieverUnavailable:
            return _reply(_t("retriever_down", lang), status="refused", lang=lang)
        page_text = "\n\n".join((c.text or "") for c in chunks).strip()
        if not page_text:
            return _reply(_t("page_empty", lang), status="refused", lang=lang)

        # The Confluence page title (= workflow name) lives in page metadata, not
        # in the storage body, so it is absent from the chunk text. Discovery
        # already resolved it from the chunk title — prepend it as the H1 so the
        # parser extracts the correct ``name`` instead of guessing from the body.
        discovered_name = state.get("workflow_name")
        if discovered_name and discovered_name.lower() not in page_text[:200].lower():
            page_text = f"# {discovered_name}\n\n{page_text}"

        page_citation = _page_citation(chunks, fallback_name=discovered_name)

        # ── Parse ─────────────────────────────────────────────────────────────
        try:
            defn = parse_workflow(page_text, llm=llm, settings=cfg)
        except WorkflowParseError as exc:
            logger.warning("execute_workflow: parse failed: %s", exc)
            return _reply(_t("parse_failed", lang), status="refused", lang=lang,
                          citations=[page_citation])

        # ── Definition-lifecycle gate (only ACTIVE runs) ──────────────────────
        ok, gate_reason = is_executable(defn)
        if not ok:
            header = f"# {defn.name}"
            body = f"{header}\n\n⚠️ {gate_reason}"
            return _reply(body, status="refused", lang=lang, citations=[page_citation])

        # ── Execute the steps ─────────────────────────────────────────────────
        jira_key = state.get("jira_parent_key")
        ctx = _ExecContext(
            llm=llm,
            retriever=retriever,
            jira=jira,
            cfg=cfg,
            defn=defn,
            jira_key=jira_key,
            lang=lang,
            page_id=page_id,
        )
        ctx.citations.append(page_citation)

        degraded = False
        for step in defn.steps:
            if budget_exceeded(deadline):
                ctx.step_logs.append(_budget_note(step, lang))
                degraded = True
                break
            try:
                ctx.run_step(step)
            except Exception:  # noqa: BLE001 — a single step never kills the run
                logger.exception("execute_workflow: step %d crashed", step.index)
                ctx.step_logs.append(f"## Step {step.index}: {step.title}\n\n⚠️ {_t('step_error', lang)}")
                degraded = True

        answer = ctx.render_answer()
        status = "partial" if (degraded or ctx.degraded) else "answered"
        return {
            "workflow_mode": True,
            "answer": answer,
            "citations": ctx.dedup_citations(),
            "status": status,
            "confidence": 1.0 if status == "answered" else 0.6,
            "source_departments": [_WORKFLOW_DEPT],
            "jira_source": defn.jira_source,
        }

    return execute_workflow


# ── Execution context ─────────────────────────────────────────────────────────

class _ExecContext:
    """Mutable accumulator for one workflow run (logs, citations, Jira refs)."""

    def __init__(
        self,
        *,
        llm: LLMPort,
        retriever: RetrieverPort,
        jira: JiraPort,
        cfg: Settings,
        defn: WorkflowDefinition,
        jira_key: str | None,
        lang: str,
        page_id: str | None = None,
    ) -> None:
        self.llm = llm
        self.retriever = retriever
        self.jira = jira
        self.cfg = cfg
        self.defn = defn
        self.jira_key = jira_key
        self.lang = lang
        self.page_id = page_id
        self.step_logs: list[str] = []
        self.citations: list[Citation] = []
        self.jira_refs: list[str] = []
        self.findings: list[str] = []  # running context fed to synthesize/gate/checklist
        self.degraded = False

    # ── Dispatch ──────────────────────────────────────────────────────────────

    def run_step(self, step: WorkflowStep) -> None:
        handler = {
            "fetch": self._fetch,
            "rag": self._rag,
            "synthesize": self._synthesize,
            "checklist": self._checklist,
            "gate": self._gate,
            "action": self._action,
        }.get(step.type, self._synthesize)
        body = handler(step)
        self.step_logs.append(self._step_block(step, body))
        if step.policy_ref:
            self.findings.append(f"[{step.title}] policy ref: {step.policy_ref}")

    # ── Step handlers ─────────────────────────────────────────────────────────

    def _fetch(self, step: WorkflowStep) -> str:
        if self.jira_key:
            try:
                issue = self.jira.get_issue(self.jira_key)
            except JiraUnavailable:
                self.degraded = True
                return f"⚠️ Could not fetch Jira `{self.jira_key}` (Jira unavailable)."
            summary = issue.get("summary", "")
            status = issue.get("status", "")
            self.findings.append(f"Jira {self.jira_key}: {summary} (status: {status})")
            self.jira_refs.append(f"Read `{self.jira_key}` — {summary} ({status})")
            url = issue.get("url")
            link = f" — [{self.jira_key}]({url})" if url else ""
            return f"Fetched Jira `{self.jira_key}`: **{summary}** (status: {status}){link}."
        # No Jira key → fall back to a RAG-style lookup of the named source.
        return self._rag(step, label="Fetched context")

    def _rag(self, step: WorkflowStep, *, label: str = "Findings") -> str:
        domain = self._domain_for(step)
        query = step.action or step.input or step.title
        if not domain:
            return "_No routable knowledge domain for this step; skipped lookup._"
        try:
            hits = self.retriever.search(
                department=domain, query=query, k=3, language=self.lang
            )
        except RetrieverUnavailable:
            self.degraded = True
            return "⚠️ Knowledge base unavailable for this step."
        if not hits:
            return "_No supporting documents found._"
        lines = []
        for hit in hits:
            cite = _chunk_citation(hit)
            self.citations.append(cite)
            idx = len(self.citations)
            snippet = excerpt_from_text(hit.text) or ""
            lines.append(f"- [{idx}] **{hit.title}** — {snippet}")
            self.findings.append(f"{hit.title}: {snippet}")
        return f"{label} (`{domain}`):\n" + "\n".join(lines)

    def _synthesize(self, step: WorkflowStep) -> str:
        instruction = step.action or step.output or step.title
        context = "\n".join(self.findings[-12:]) or "(no prior findings)"
        prompt = (
            f"You are executing the step \"{step.title}\" of a workflow. "
            f"Task: {instruction}. Using ONLY the context below, write a concise "
            f"grounded result ({'Vietnamese' if self.lang == 'vi' else 'English'}). "
            f"Do not invent facts.\n\nContext:\n{context}"
        )
        try:
            result = self.llm.complete(
                tier=ModelTier.MAIN,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                timeout_s=self.cfg.branch_timeout_s,
            )
        except LLMUnavailable:
            self.degraded = True
            return "⚠️ Could not synthesise this step (LLM unavailable)."
        text = (result.text or "").strip()
        if text:
            self.findings.append(f"{step.title}: {text}")
        return text or "_(no output)_"

    def _checklist(self, step: WorkflowStep) -> str:
        if not step.checklist:
            return "_(no checklist items)_"
        context = "\n".join(self.findings[-12:]) or "(no prior findings)"
        items_json = "\n".join(f"- {i}" for i in step.checklist)
        prompt = (
            "Evaluate each checklist item against the context. Return ONLY a JSON "
            'array of {"item": <verbatim>, "verdict": "pass"|"unclear", "note": <short>}. '
            "Mark 'pass' only when the context clearly supports it; otherwise 'unclear'.\n\n"
            f"Context:\n{context}\n\nChecklist:\n{items_json}"
        )
        verdicts: dict[str, dict] = {}
        try:
            result = self.llm.complete(
                tier=ModelTier.SMALL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format="json",
                timeout_s=self.cfg.branch_timeout_s,
            )
            data = parse_json_response(result.text)
            if isinstance(data, list):
                for row in data:
                    if isinstance(row, dict) and row.get("item"):
                        verdicts[str(row["item"]).strip()] = row
        except (LLMUnavailable, ValueError):
            self.degraded = True  # render items as needs-confirm

        lines = []
        for item in step.checklist:
            row = verdicts.get(item.strip())
            if row and row.get("verdict") == "pass":
                mark, note = "✅", row.get("note", "")
            else:
                mark = "⚠️"
                note = (row or {}).get("note", "") or "needs human confirmation"
            suffix = f" — {note}" if note else ""
            lines.append(f"- {mark} {item}{suffix}")
        return "Checklist:\n" + "\n".join(lines)

    def _gate(self, step: WorkflowStep) -> str:
        condition = step.condition or step.action or ""
        if not condition:
            return "_(no gate condition)_"
        context = "\n".join(self.findings[-12:]) or "(no prior findings)"
        prompt = (
            f"Evaluate this branch condition against the context. Condition: {condition}. "
            'Return ONLY JSON {"decision": "proceed"|"escalate"|"skip", "rationale": <short>}.\n\n'
            f"Context:\n{context}"
        )
        try:
            result = self.llm.complete(
                tier=ModelTier.SMALL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format="json",
                timeout_s=self.cfg.branch_timeout_s,
            )
            data = parse_json_response(result.text)
            decision = str(data.get("decision", "proceed")) if isinstance(data, dict) else "proceed"
            rationale = str(data.get("rationale", "")) if isinstance(data, dict) else ""
        except (LLMUnavailable, ValueError):
            self.degraded = True
            decision, rationale = "escalate", "could not evaluate condition automatically"
        self.findings.append(f"Gate '{condition}': {decision} ({rationale})")
        emoji = {"proceed": "✅", "escalate": "🚨", "skip": "⏭️"}.get(decision, "•")
        return f"Condition: _{condition}_\n\n{emoji} **{decision.upper()}** — {rationale}"

    def _action(self, step: WorkflowStep) -> str:
        source = self.defn.jira_source
        body = self._action_body(step)
        try:
            if source == "auto-create":
                return self._action_auto_create(step, body)
            # default + existing-ticket: comment on the supplied ticket
            return self._action_existing_ticket(step, body)
        except JiraUnavailable as exc:
            self.degraded = True
            return f"⚠️ Jira action not performed ({exc})."

    def _action_existing_ticket(self, step: WorkflowStep, body: str) -> str:
        if not self.jira_key:
            self.degraded = True
            return (
                "⚠️ This workflow uses an existing Jira ticket, but no ticket key "
                "was provided. Re-run with e.g. `... cho ticket KAN-1`."
            )
        res = self.jira.add_comment(key=self.jira_key, body=body)
        dry = res.get("dry_run")
        url = res.get("url")
        link = f" [{self.jira_key}]({url})" if url else f" `{self.jira_key}`"
        verb = "Would post" if dry else "Posted"
        self.jira_refs.append(f"{verb} comment on{link}")
        self._tag_ticket(self.jira_key)
        return f"{verb} a Jira comment on{link}{' _(dry-run)_' if dry else ''}."

    def _action_auto_create(self, step: WorkflowStep, body: str) -> str:
        parent = self.jira.create_issue(
            summary=self.defn.name,
            description=body,
            issuetype="Task",
        )
        pkey, purl = parent.get("key", ""), parent.get("url", "")
        dry = parent.get("dry_run")
        self.jira_refs.append(("Would create" if dry else "Created") + f" parent `{pkey}`")
        if pkey:
            self._tag_ticket(pkey)
        # One sub-task per step that names a responsible role.
        sub_lines = []
        for s in self.defn.steps:
            if not s.responsible_role:
                continue
            sub = self.jira.create_issue(
                summary=f"{s.title}",
                description=f"Responsible: {s.responsible_role} — {s.responsible_department or ''}",
                issuetype="Sub-task",
                parent=pkey or None,
            )
            sub_lines.append(f"  - `{sub.get('key','?')}` {s.title} → {s.responsible_role}")
        plink = f"[{pkey}]({purl})" if purl else f"`{pkey}`"
        head = ("Would create" if dry else "Created") + f" parent {plink}{' _(dry-run)_' if dry else ''}"
        return head + ("\n" + "\n".join(sub_lines) if sub_lines else "")

    def _action_body(self, step: WorkflowStep) -> str:
        head = f"[Agent] {self.defn.name}"
        findings = "\n".join(f"- {f}" for f in self.findings[-10:]) or "- (no findings recorded)"
        return f"{head}\n\nStep: {step.title}\n\nFindings:\n{findings}"

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _tag_ticket(self, key: str) -> None:
        """Tag the ticket with ``wf-<slug>`` so webhooks resolve the workflow.

        Best-effort: a failure here must not break the run.
        """
        label = workflow_label(self.defn.name)
        try:
            self.jira.add_labels(key=key, labels=[label])
        except JiraUnavailable:
            logger.info("Could not tag ticket %s with %s (Jira unavailable)", key, label)

    def _domain_for(self, step: WorkflowStep) -> str | None:
        routable = set(routable_keys())
        dept = (step.responsible_department or "").strip().lower()
        if not dept:
            return next(iter(routable), None)
        if dept in routable:
            return dept
        for alias, key in _DOMAIN_ALIASES.items():
            if alias in dept and key in routable:
                return key
        return next(iter(routable), None)

    def _step_block(self, step: WorkflowStep, body: str) -> str:
        who = step.responsible_role or "—"
        if step.responsible_department:
            who += f" · {step.responsible_department}"
        header = f"## Step {step.index}: {step.title}\n_Type: {step.type} · Responsible: {who}_"
        return f"{header}\n\n{body}"

    def render_answer(self) -> str:
        version = f" (v{self.defn.version})" if self.defn.version else ""
        lines = [f"# {self.defn.name}{version}"]
        meta = []
        if self.jira_key:
            meta.append(f"Ticket: `{self.jira_key}`")
        if self.defn.jira_source:
            meta.append(f"Jira source: {self.defn.jira_source}")
        if meta:
            lines.append("> " + " · ".join(meta))
        lines.append("")
        lines.extend(self.step_logs)
        if self.jira_refs:
            lines.append("\n## Jira actions")
            lines.extend(f"- {r}" for r in self.jira_refs)
        return "\n\n".join(lines)

    def dedup_citations(self) -> list[Citation]:
        seen: set[tuple] = set()
        out: list[Citation] = []
        for c in self.citations:
            key = (c.get("url"), c.get("section"), c.get("title"))
            if key in seen:
                continue
            seen.add(key)
            out.append(c)
        return out


# ── Citation builders ───────────────────────────────────────────────────────────

def _chunk_citation(rc: RetrievedChunk) -> Citation:
    lifecycle = rc.lifecycle_state or "active"
    cite = Citation(
        title=rc.title or "(untitled)",
        url=rc.url or "",
        section=rc.section,
        doc_type=rc.doc_type,
        last_modified=rc.last_modified,
        lifecycle_state=lifecycle,
        deprecated=lifecycle == "deprecated",
        successor_url=None,
        source_type=rc.source_type,
        page=rc.page,
    )
    excerpt = excerpt_from_text(rc.text)
    if excerpt:
        cite["excerpt"] = excerpt
    if rc.chunk_id:
        cite["chunk_id"] = rc.chunk_id
    return cite


def _page_citation(chunks: list[RetrievedChunk], *, fallback_name: str | None) -> Citation:
    if chunks:
        cite = _chunk_citation(chunks[0])
        cite["section"] = None  # cite the page as a whole
        return cite
    return Citation(title=fallback_name or "Workflow", url="", lifecycle_state="active", deprecated=False)


# ── Replies / localisation ──────────────────────────────────────────────────────

def _reply(
    answer: str,
    *,
    status: str,
    lang: str,
    citations: list[Citation] | None = None,
) -> dict:
    return {
        "workflow_mode": True,
        "answer": answer,
        "citations": citations or [],
        "status": status,
        "confidence": 0.0 if status == "refused" else 1.0,
        "source_departments": [_WORKFLOW_DEPT] if status != "refused" else [],
    }


def _budget_note(step: WorkflowStep, lang: str) -> str:
    msg = (
        "Hết thời gian xử lý — dừng ở bước này, trả về kết quả một phần."
        if lang == "vi"
        else "Ran out of time — stopping here and returning a partial result."
    )
    return f"## Step {step.index}: {step.title}\n\n⏱️ {msg}"


def _t(key: str, lang: str) -> str:
    vi = lang == "vi"
    table = {
        "no_match": (
            "Không tìm thấy workflow đang hoạt động phù hợp với yêu cầu của bạn.",
            "No matching active workflow was found for your request.",
        ),
        "retriever_down": (
            "Không truy cập được kho workflow lúc này.",
            "The workflow registry is not available right now.",
        ),
        "page_empty": (
            "Trang workflow rỗng hoặc chưa được lập chỉ mục.",
            "The workflow page is empty or not yet indexed.",
        ),
        "parse_failed": (
            "Không đọc được định nghĩa workflow từ trang Confluence.",
            "Could not parse the workflow definition from the Confluence page.",
        ),
        "step_error": (
            "Bước này gặp lỗi và đã được bỏ qua.",
            "This step failed and was skipped.",
        ),
    }
    vi_text, en_text = table.get(key, ("", ""))
    return vi_text if vi else en_text
