#!/usr/bin/env python3
"""Golden eval runner — retrieval, generation, and refusal metrics (Eval MUST 🟢).

Usage:
    python evals/run_eval.py --stub
    python evals/run_eval.py --cases evals/golden_cases.json --stub
    python evals/run_eval.py --base-url http://localhost:8080
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from evals.metrics import aggregate_eval

DEFAULT_HEADERS = {
    "X-GreenNode-AgentBase-User-Id": "eval-user",
    "X-GreenNode-AgentBase-Session-Id": "eval-session",
    "X-GreenNode-AgentBase-Role": "engineer",
    "X-GreenNode-AgentBase-Home-Department": "risk",
}

DEFAULT_CASES = Path(__file__).parent / "golden_cases.json"
DEFAULT_REPORT = Path(__file__).parent / "last_eval_report.json"


def load_cases(path: Path) -> list[dict]:
    return json.loads(path.read_text())


def run_stub(cases: list[dict]) -> tuple[list[dict], dict]:
    """Offline structural checks — simulates expected outcomes for CI without LLM."""
    results: list[dict] = []
    for case in cases:
        expect = case.get("expect", {})
        status = expect.get("status", "answered")
        answer = ""
        if status == "refused":
            answer = "Not covered in the docs."
        elif status == "partial":
            answer = "Partial answer based on available sources."
        else:
            keywords = expect.get("answer_keywords") or ["policy"]
            answer = f"Grounded answer mentioning {keywords[0]} with citation [1]."

        retrieval = case.get("retrieval") or {}
        relevant = retrieval.get("relevant_chunk_ids") or []
        retrieved = list(relevant[:5]) + ["noise-chunk-1", "noise-chunk-2"]
        source_texts = [
            f"Source text about {kw} for eval case {case.get('id')}."
            for kw in (expect.get("answer_keywords") or ["policy"])
        ]

        results.append(
            {
                "id": case.get("id"),
                "status": status,
                "answer": answer,
                "retrieved_chunk_ids": retrieved,
                "source_texts": source_texts,
                "citations": [{"title": expect.get("citation_keywords", ["doc"])[0]}],
            }
        )

    summary = aggregate_eval(cases, results).to_dict()
    summary["mode"] = "stub"
    return results, summary


def run_live(base_url: str, cases: list[dict]) -> tuple[list[dict], dict]:
    results: list[dict] = []
    with httpx.Client(base_url=base_url, timeout=120.0) as client:
        for case in cases:
            resp = client.post(
                "/chat",
                headers=DEFAULT_HEADERS,
                json={
                    "question": case["question"],
                    "target_departments": case.get("target_departments"),
                },
            )
            body = resp.json() if resp.status_code == 200 else {}
            results.append(
                {
                    "id": case.get("id"),
                    "ok": resp.status_code == 200,
                    "status": body.get("status"),
                    "answer": body.get("answer") or "",
                    "citations": body.get("citations") or [],
                    "retrieved_chunk_ids": body.get("retrieved_chunk_ids") or [],
                    "source_texts": [
                        c.get("snippet") or c.get("title") or ""
                        for c in (body.get("citations") or [])
                    ],
                }
            )

    summary = aggregate_eval(cases, results).to_dict()
    summary["mode"] = "live"
    return results, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--stub", action="store_true")
    parser.add_argument("--output", type=Path, help="Optional path to write full JSON report")
    args = parser.parse_args()

    cases = load_cases(args.cases)
    if args.stub:
        _, summary = run_stub(cases)
    else:
        _, summary = run_live(args.base_url, cases)

    report = {
        "cases": len(cases),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        **summary,
    }
    print(json.dumps(report, indent=2))

    output_path = args.output or DEFAULT_REPORT
    output_path.write_text(json.dumps(report, indent=2))

    status_ok = summary.get("status_pass", 0) == len(cases)
    return 0 if status_ok else 1


if __name__ == "__main__":
    sys.exit(main())
