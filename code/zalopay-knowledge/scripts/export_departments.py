#!/usr/bin/env python3
"""Export department registry to frontend/src/lib/departments.data.json.

Run from the zalopay-knowledge project root::

    python scripts/export_departments.py

The JSON file is the frontend mirror of ``app/common/departments.py``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.common.departments import export_frontend_catalog  # noqa: E402

OUT = ROOT / "frontend" / "src" / "lib" / "departments.data.json"


def main() -> None:
    payload = export_frontend_catalog()
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(payload['departments'])} departments)")


if __name__ == "__main__":
    main()
