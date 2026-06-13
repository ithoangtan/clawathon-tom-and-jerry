"""Golden set location and schema smoke tests."""

from __future__ import annotations

import json
from pathlib import Path

GOLDEN_PATH = Path(__file__).resolve().parents[2] / "evals" / "golden_cases.json"


def test_golden_cases_file_exists() -> None:
    assert GOLDEN_PATH.is_file()


def test_golden_cases_valid_json_array() -> None:
    cases = json.loads(GOLDEN_PATH.read_text())
    assert isinstance(cases, list)
    assert len(cases) >= 30
