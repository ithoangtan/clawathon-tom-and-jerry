"""Seed a live demo for the Lucky Wheel risk-review workflow.

For each of the 3 CTKM in ``promotional_campaigns_risk_assessment.md``:
  1. Publish a **campaign-spec** Confluence page in ``ClawathonRisk`` containing
     only the campaign info + Terms & Conditions (the risk verdict X.3/X.4 and the
     inline "[Vi phạm …]" annotations are stripped, so the agent must assess it).
  2. Create a Jira ticket (project KAN) labelled ``wf-risk-campaign-review-lucky-wheel``
     (no ``testing`` label) whose Description links that spec page.

Prints a JSON line ``DEMO_MAP=<json>`` mapping CTKM → {page_id, page_url, ticket_key}.
Idempotent on pages (by title); always creates fresh tickets.

    python -m scripts.seed_demo_campaigns
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import httpx

from app.adapters.confluence_credentials import resolve_confluence_api_token
from app.adapters.jira_client import JiraClient
from app.common.markdown_storage import md_to_storage
from app.config import get_settings

SPACE_KEY = "ClawathonRisk"
WF_LABEL = "wf-risk-campaign-review-lucky-wheel"
MD = Path(__file__).resolve().parents[3] / "promotional_campaigns_risk_assessment.md"

# Strip the editorial verdict markers so the spec doesn't give away the answer.
_ANNOT = re.compile(r"\s*\*\*\[[^\]]*\]\*\*|\s*\[(?:⚠️|🚨)[^\]]*\]")


def _campaign_sections(md: str) -> list[tuple[int, str]]:
    """Return [(n, spec_markdown)] — info + T&C only, verdict stripped."""
    parts = re.split(r"(?m)^#\s+CTKM\s+(\d)\s*[–-].*$", md)
    out: list[tuple[int, str]] = []
    # parts = [pre, '1', body1, '2', body2, '3', body3]
    for i in range(1, len(parts), 2):
        n = int(parts[i])
        body = parts[i + 1]
        # keep everything before the Risk Assessment Summary subsection
        cut = re.search(r"(?m)^###\s+\d+\.3", body)
        if cut:
            body = body[: cut.start()]
        body = _ANNOT.sub("", body)
        out.append((n, body.strip()))
    return out


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    sections = _campaign_sections(md)

    cfg = get_settings()
    base = (cfg.confluence_base_url or "").rstrip("/")
    auth = (cfg.confluence_email, resolve_confluence_api_token(cfg))
    jira = JiraClient(cfg)

    demo_map: dict[str, dict] = {}
    with httpx.Client(timeout=30.0, auth=auth) as client:
        space_id = str(client.get(
            f"{base}/api/v2/spaces", params={"keys": SPACE_KEY, "limit": 1}
        ).json()["results"][0]["id"])

        for n, spec_md in sections:
            title = f"[Demo] Campaign Spec — Lucky Wheel CTKM {n}"
            body = md_to_storage(spec_md)

            existing = client.get(
                f"{base}/rest/api/content/search",
                params={"cql": f'space="{SPACE_KEY}" and title="{title}" and type=page'},
            ).json().get("results", [])
            if existing:
                pid = existing[0]["id"]
                cur = client.get(f"{base}/api/v2/pages/{pid}", params={"body-format": "storage"}).json()
                ver = int((cur.get("version") or {}).get("number", 1)) + 1
                client.put(f"{base}/api/v2/pages/{pid}", json={
                    "id": pid, "status": "current", "title": title, "spaceId": space_id,
                    "body": {"representation": "storage", "value": body}, "version": {"number": ver},
                }).raise_for_status()
            else:
                pid = client.post(f"{base}/api/v2/pages", json={
                    "spaceId": space_id, "status": "current", "title": title,
                    "body": {"representation": "storage", "value": body},
                }).json()["id"]
            page_url = f"{base}/spaces/{SPACE_KEY}/pages/{pid}"

            # Jira ticket linking the spec page (URL in plain text → resolver extracts it).
            desc = (
                f"Campaign cần review rủi ro: Lucky Wheel CTKM {n}.\n"
                f"Campaign spec: {page_url}\n"
                f"Vui lòng chuyển sang RISK REVIEW để Agent đánh giá."
            )
            issue = jira.create_issue(summary=f"[Demo] Lucky Wheel CTKM {n} — Campaign Risk Review", description=desc)
            key = issue["key"]
            jira.add_labels(key=key, labels=[WF_LABEL])

            demo_map[f"CTKM{n}"] = {"page_id": pid, "page_url": page_url, "ticket_key": key, "ticket_url": issue["url"]}
            print(f"CTKM{n}: spec page {pid} | ticket {key}")

    print("DEMO_MAP=" + json.dumps(demo_map, ensure_ascii=False))


if __name__ == "__main__":
    main()
