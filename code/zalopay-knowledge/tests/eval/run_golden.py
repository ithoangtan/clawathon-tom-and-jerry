"""Run golden-set eval from ``tests/golden/golden_set.yaml`` (Eval MUST 🟢)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_YAML = ROOT / "tests" / "golden" / "golden_set.yaml"

sys.path.insert(0, str(ROOT))

from evals.metrics import (  # noqa: E402
    aggregate_eval,
    context_precision_at_k,
    context_recall_at_k,
    faithfulness_score,
    refusal_counts,
)


def load_golden_yaml(path: Path) -> list[dict[str, Any]]:
    raw = yaml.safe_load(path.read_text())
    cases = raw.get("cases") if isinstance(raw, dict) else raw
    if not isinstance(cases, list):
        raise ValueError(f"Invalid golden set at {path}")
    return cases


def yaml_to_eval_cases(yaml_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map YAML schema to ``evals.metrics`` case shape."""
    out: list[dict[str, Any]] = []
    for row in yaml_cases:
        behavior = row.get("expected_behavior", "answer")
        must_refuse = behavior == "refuse"
        status = "refused" if must_refuse else "answered"
        expect: dict[str, Any] = {
            "status": status,
            "must_refuse": must_refuse,
        }
        if row.get("answer_keywords"):
            expect["answer_keywords"] = row["answer_keywords"]
        if row.get("expected_citation_url") and row["expected_citation_url"] != "none":
            expect["citation_keywords"] = [row["expected_citation_url"]]

        case: dict[str, Any] = {
            "id": row["id"],
            "question": row["question"],
            "expect": expect,
        }
        if row.get("department"):
            case["department"] = row["department"]
        if row.get("target_departments"):
            case["target_departments"] = row["target_departments"]
        if row.get("retrieval"):
            case["retrieval"] = row["retrieval"]
        out.append(case)
    return out


def run_stub(yaml_cases: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Perfect stub run — status matches labels; retrieval ids echoed when present."""
    eval_cases = yaml_to_eval_cases(yaml_cases)
    results: list[dict[str, Any]] = []
    for row, eval_case in zip(yaml_cases, eval_cases, strict=True):
        behavior = row.get("expected_behavior", "answer")
        status = "refused" if behavior == "refuse" else "answered"
        retrieval = row.get("retrieval") or {}
        chunk_ids = retrieval.get("relevant_chunk_ids") or []
        answer = ""
        source_texts: list[str] = []
        if status == "answered":
            kws = row.get("answer_keywords") or ["policy"]
            answer = " ".join(kws) + " per internal documentation."
            source_texts = [answer + " source excerpt from indexed docs."]
        results.append(
            {
                "id": row["id"],
                "status": status,
                "answer": answer,
                "retrieved_chunk_ids": list(chunk_ids),
                "source_texts": source_texts,
                "citation_urls": [row.get("expected_citation_url", "")],
            }
        )

    summary = aggregate_eval(eval_cases, results)
    payload = summary.to_dict()
    payload["cases"] = len(yaml_cases)
    payload["mode"] = "stub"
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    return results, payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Golden-set eval runner (YAML source)")
    parser.add_argument("--cases", type=Path, default=DEFAULT_YAML)
    parser.add_argument("--stub", action="store_true", help="Offline perfect-label stub run")
    parser.add_argument("--output", type=Path, default=None, help="Write JSON report path")
    parser.add_argument("--k", type=int, default=5, help="k for recall/precision spot check")
    args = parser.parse_args(argv)

    yaml_cases = load_golden_yaml(args.cases)
    if args.stub:
        _, report = run_stub(yaml_cases)
    else:
        print("Only --stub is supported in MVP; use evals/run_eval.py for live HTTP.", file=sys.stderr)
        return 2

    if args.output:
        args.output.write_text(json.dumps(report, indent=2))
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
