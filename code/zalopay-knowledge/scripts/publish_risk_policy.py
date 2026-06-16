"""Publish the promotional-campaign risk assessment as a Risk-space Confluence page.

Reads ``promotional_campaigns_risk_assessment.md`` (repo root by default, or a path
passed as argv[1]), converts Markdown → Confluence *storage* via
``app.common.markdown_storage.md_to_storage``, and creates/updates (idempotent by
title) a page in the ``risk`` space (``ClawathonRisk``). This becomes the RAG source
the Lucky Wheel workflow's RISK REVIEW step cites.

    python -m scripts.publish_risk_policy
    python -m scripts.publish_risk_policy /path/to/promotional_campaigns_risk_assessment.md
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

from app.adapters.confluence_credentials import resolve_confluence_api_token
from app.common.markdown_storage import md_to_storage
from app.config import get_settings

SPACE_KEY = "ClawathonRisk"
TITLE = "Promotional Campaigns — Risk Assessment Policy (Lucky Wheel)"
LABELS = ["risk-policy", "promotion", "lucky-wheel"]
DEFAULT_MD = Path(__file__).resolve().parents[3] / "promotional_campaigns_risk_assessment.md"


def main() -> None:
    md_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MD
    if not md_path.exists():
        raise SystemExit(f"Markdown not found: {md_path}")
    body = md_to_storage(md_path.read_text(encoding="utf-8"))

    s = get_settings()
    base = (s.confluence_base_url or "").rstrip("/")
    auth = (s.confluence_email, resolve_confluence_api_token(s))

    with httpx.Client(timeout=30.0, auth=auth) as client:
        existing = client.get(
            f"{base}/rest/api/content/search",
            params={"cql": f'space="{SPACE_KEY}" and title="{TITLE}" and type=page'},
        ).json().get("results", [])

        if existing:
            page_id = existing[0]["id"]
            cur = client.get(
                f"{base}/api/v2/pages/{page_id}", params={"body-format": "storage"}
            ).json()
            space_id = str(cur.get("spaceId", ""))
            version = int((cur.get("version") or {}).get("number", 1)) + 1
            resp = client.put(
                f"{base}/api/v2/pages/{page_id}",
                json={
                    "id": page_id, "status": "current", "title": TITLE, "spaceId": space_id,
                    "body": {"representation": "storage", "value": body},
                    "version": {"number": version, "message": "Update risk assessment policy"},
                },
            )
            resp.raise_for_status()
            print(f"Updated page {page_id} (v{version})")
        else:
            spaces = client.get(
                f"{base}/api/v2/spaces", params={"keys": SPACE_KEY, "limit": 1}
            ).json().get("results", [])
            if not spaces:
                raise SystemExit(f"Space {SPACE_KEY!r} not found")
            space_id = str(spaces[0]["id"])
            resp = client.post(
                f"{base}/api/v2/pages",
                json={
                    "spaceId": space_id, "status": "current", "title": TITLE,
                    "body": {"representation": "storage", "value": body},
                },
            )
            resp.raise_for_status()
            page_id = resp.json()["id"]
            print(f"Created page {page_id}")

        label_resp = client.post(
            f"{base}/rest/api/content/{page_id}/label",
            json=[{"prefix": "global", "name": n} for n in LABELS],
        )
        label_resp.raise_for_status()
        print("Labels attached:", [r["name"] for r in label_resp.json().get("results", [])])
        print("Page URL:", f"{base}/spaces/{SPACE_KEY}/pages/{page_id}")


if __name__ == "__main__":
    main()
