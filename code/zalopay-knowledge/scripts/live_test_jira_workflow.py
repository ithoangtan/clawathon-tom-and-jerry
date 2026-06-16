"""Live end-to-end test for the Lucky Wheel risk-review Jira workflow.

For each ticket key (default: the 3 demo tickets from ``seed_demo_campaigns``),
synthesise a ``status_changed: TO DO → RISK REVIEW`` event and run the REAL
handler with REAL deps (Jira / Confluence / OpenSearch / MaaS LLM). This is the
same code path the webhook triggers — it reads the ticket, fetches the campaign
spec linked in the Description, grounds against the 11 policy rules, posts a
Quick Risk Report comment, and applies the page-defined reactions.

    python -m scripts.live_test_jira_workflow KAN-8 KAN-9 KAN-10
    python -m scripts.live_test_jira_workflow            # prompts for keys
"""

from __future__ import annotations

import sys

from app.adapters.deps import get_deps
from app.integrations.jira_events import normalize_jira_event
from app.integrations.jira_handler import handle_jira_event


def run(keys: list[str]) -> None:
    deps = get_deps()
    print(f"deps: jira_ready={deps.jira.is_ready()} retriever_ready={deps.retriever.is_ready()}\n")

    for key in keys:
        event = normalize_jira_event({
            "event_type": "status_changed",
            "issue_key": key,
            "status_from": "TO DO",
            "status_to": "RISK REVIEW",
            "actor": "human-reviewer",
        })
        out = handle_jira_event(
            event,
            llm=deps.llm,
            retriever=deps.retriever,
            jira=deps.jira,
            confluence_writer=deps.confluence_writer,
            settings=deps.settings,
        )
        comment = out.get("jira_comment") or {}
        reactions = out.get("reactions") or {}
        print(f"━━━ {key} ━━━")
        print(f"  status            : {out.get('status')}")
        print(f"  workflow          : {out.get('workflow')}")
        print(f"  DECISION          : {out.get('decision')}")
        print(f"  jira_comment      : dry_run={comment.get('dry_run')} url={comment.get('url')}")
        print(f"  confluence_updated: {out.get('confluence_updated')}")
        print(f"  reactions applied : {reactions.get('verbs')}"
              + (f" errors={reactions['errors']}" if reactions.get('errors') else ""))
        if out.get("status") not in ("acted",):
            print(f"  reason            : {out.get('reason')}")
        print()


if __name__ == "__main__":
    arg_keys = sys.argv[1:]
    if not arg_keys:
        arg_keys = ["KAN-8", "KAN-9", "KAN-10"]
    run(arg_keys)
