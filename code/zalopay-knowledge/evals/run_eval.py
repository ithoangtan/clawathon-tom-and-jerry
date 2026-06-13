#!/usr/bin/env python3
"""Golden eval runner — hooks for CI / release gates (06-SUCCESS-CRITERIA.md §3).

Usage:
    python evals/run_eval.py --cases evals/sample_cases.json --stub

With a live stack and index:
    python evals/run_eval.py --cases evals/sample_cases.json --base-url http://localhost:8080
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

DEFAULT_HEADERS = {
    "X-GreenNode-AgentBase-User-Id": "eval-user",
    "X-GreenNode-AgentBase-Session-Id": "eval-session",
    "X-GreenNode-AgentBase-Role": "engineer",
    "X-GreenNode-AgentBase-Home-Department": "risk",
}


def run_stub(cases: list[dict]) -> dict:
    """Offline structural checks without calling the LLM."""
    passed = 0
    for case in cases:
        expect = case.get("expect", {})
        if expect.get("status") in ("answered", "refused", "partial"):
            passed += 1
    return {"total": len(cases), "passed": passed, "mode": "stub"}


def run_live(base_url: str, cases: list[dict]) -> dict:
    passed = 0
    results = []
    with httpx.Client(base_url=base_url, timeout=60.0) as client:
        for case in cases:
            resp = client.post(
                "/chat",
                headers=DEFAULT_HEADERS,
                json={
                    "question": case["question"],
                    "target_departments": case.get("target_departments"),
                },
            )
            ok = resp.status_code == 200
            body = resp.json() if ok else {}
            expect_status = case.get("expect", {}).get("status")
            if ok and expect_status and body.get("status") == expect_status:
                passed += 1
            results.append({"id": case.get("id"), "ok": ok, "status": body.get("status")})
    return {"total": len(cases), "passed": passed, "mode": "live", "results": results}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=Path(__file__).parent / "sample_cases.json")
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--stub", action="store_true")
    args = parser.parse_args()

    cases = json.loads(args.cases.read_text())
    summary = run_stub(cases) if args.stub else run_live(args.base_url, cases)
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
