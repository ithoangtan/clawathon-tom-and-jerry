"""Eval runner smoke tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_run_eval_stub_exits_zero_and_writes_report(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "evals" / "run_eval.py"),
            "--stub",
            "--output",
            str(report),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    body = json.loads(report.read_text())
    assert 30 <= body["cases"] <= 50
    assert body["mode"] == "stub"
    assert "faithfulness" in body
    assert "refusal_precision" in body
    assert body["generated_at"]
