from __future__ import annotations

"""Generic reaction dispatcher: apply a workflow page's declared side-effects.

A workflow page declares, in its ``## Reactions`` table, what to do for each
decision the agent can reach (``PASS`` / ``PARTIAL_FAIL`` / ``FAIL`` / …). After
a trigger's action runs and the LLM emits a ``DECISION:`` token, this module maps
the matching row's **verbs** onto capability primitives:

- ``comment``            — handled by the caller (always posts the report); skipped here
- ``reassign:<target>``  — ``target`` = ``reporter`` (the ticket creator) or an accountId
- ``label:<name>``       — add a Jira label
- ``append_confluence``  — append the report to the workflow page

Verbs are **data on the Confluence page**; this is the only code that knows how to
*perform* each one, so a new workflow reuses it with zero code change. Each verb
degrades independently — the dispatcher never raises.
"""

import logging
import re
from datetime import datetime, timezone

from app.adapters.confluence_writer import text_to_storage
from app.ports.confluence_writer import ConfluenceWriterPort
from app.ports.errors import ConfluenceUnavailable, JiraUnavailable
from app.ports.jira import JiraPort

logger = logging.getLogger(__name__)

_DECISION_RE = re.compile(r"DECISION\s*[:=]\s*([A-Za-z][A-Za-z0-9 _-]*)", re.IGNORECASE)


def _norm(token: str) -> str:
    return (token or "").strip().upper().replace(" ", "_").replace("-", "_")


def parse_decision(text: str) -> str | None:
    """Extract the ``DECISION:`` token from an action result (None if absent)."""
    m = _DECISION_RE.search(text or "")
    return _norm(m.group(1)) if m else None


def apply_reactions(
    decision: str | None,
    defn,
    *,
    issue_key: str,
    report_text: str,
    issue: dict,
    jira: JiraPort,
    confluence_writer: ConfluenceWriterPort,
    page_id: str,
) -> dict:
    """Apply the page-declared verbs for *decision*. Returns an applied-summary dict.

    No-op (returns ``{"decision", "verbs": []}``) when there is no decision or no
    matching ``## Reactions`` row — so workflows without a Reactions table behave
    exactly as before (comment-only).
    """
    applied: dict = {"decision": decision, "verbs": []}
    if not decision:
        return applied

    reaction = next(
        (r for r in (defn.reactions or []) if _norm(r.decision) == decision), None
    )
    if reaction is None:
        return applied

    reporter = ((issue.get("fields") or {}).get("reporter") or {}).get("accountId")

    for verb in reaction.verbs:
        name, _, arg = str(verb).partition(":")
        name, arg = name.strip().lower(), arg.strip()
        try:
            if name in ("comment", ""):
                continue  # caller always posts the report as a comment
            elif name == "reassign":
                target = reporter if arg in ("", "reporter", "creator") else arg
                if not target:
                    applied["verbs"].append("reassign:skipped-no-target")
                    continue
                res = jira.assign_issue(key=issue_key, account_id=target)
                applied["verbs"].append(
                    f"reassign:{target}" + (" (dry-run)" if res.get("dry_run") else "")
                )
            elif name == "label":
                if not arg:
                    continue
                res = jira.add_labels(key=issue_key, labels=[arg])
                applied["verbs"].append(
                    f"label:{arg}" + (" (dry-run)" if res.get("dry_run") else "")
                )
            elif name == "update_status":
                if not arg:
                    applied["verbs"].append("update_status:skipped-no-target")
                    continue
                res = jira.update_issue_status(key=issue_key, transition_name=arg)
                applied["verbs"].append(
                    f"update_status:{arg}" + (" (dry-run)" if res.get("dry_run") else "")
                )
            elif name == "append_confluence":
                ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
                frag = (
                    f"<h3>Agent run — {ts} ({issue_key}) — {decision}</h3>"
                    + text_to_storage(report_text)
                )
                confluence_writer.append_to_page(page_id=page_id, html_fragment=frag)
                applied["verbs"].append("append_confluence")
            else:
                logger.info("reaction verb %r not supported — skipped", verb)
                applied["verbs"].append(f"{name}:unsupported")
        except (JiraUnavailable, ConfluenceUnavailable) as exc:
            logger.warning("reaction verb %r failed: %s", verb, exc)
            applied.setdefault("errors", []).append(f"{name}: {exc}")

    return applied
