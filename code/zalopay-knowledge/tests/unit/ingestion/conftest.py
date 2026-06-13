from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import numpy as np
import pytest

# Stub optional runtime deps so ingestion tests collect without full requirements.txt.
if "pypdf" not in sys.modules:
    _pypdf = ModuleType("pypdf")
    _pypdf.PdfReader = MagicMock()
    sys.modules["pypdf"] = _pypdf

from app.common.departments import DepartmentKey
from app.config import Settings
from app.ingestion.metadata import serialize_acl, serialize_labels
from app.store.meta import MetaStore

# ── Sample content fixtures ───────────────────────────────────────────────────

SAMPLE_HTML = """
<h1>Risk Escalation Policy</h1>
<p>Contact <strong>risk@zalopay.vn</strong> for urgent issues.</p>
<ul>
  <li>Step one: assess severity</li>
  <li>Step two: notify on-call</li>
</ul>
<table><tr><td>Level</td><td>SLA</td></tr></table>
"""

SAMPLE_PLAIN_TEXT = """# Risk Escalation Policy

Contact risk@zalopay.vn for urgent issues.

## Severity levels

Step one: assess severity.
Step two: notify on-call.
"""

LONG_PARAGRAPH = (
    "This paragraph describes operational procedures for incident response. "
    * 80
).strip()


@pytest.fixture
def index_builder_cls():
    """Import IndexBuilder while avoiding the adapters↔graph circular import."""
    saved = {
        key: sys.modules.get(key)
        for key in ("app.graph", "app.graph.build", "app.adapters", "app.adapters.deps")
    }
    graph_build = ModuleType("app.graph.build")
    graph_build.GraphDeps = type("GraphDeps", (), {})
    graph_pkg = ModuleType("app.graph")
    graph_pkg.__path__ = []  # type: ignore[attr-defined]
    sys.modules["app.graph"] = graph_pkg
    sys.modules["app.graph.build"] = graph_build

    for key in ("app.adapters.deps", "app.adapters", "app.ingestion.indexer"):
        sys.modules.pop(key, None)

    from app.ingestion.indexer import IndexBuilder

    yield IndexBuilder

    for key, module in saved.items():
        if module is None:
            sys.modules.pop(key, None)
        else:
            sys.modules[key] = module


@pytest.fixture
def sample_html() -> str:
    return SAMPLE_HTML


@pytest.fixture
def sample_text() -> str:
    return SAMPLE_PLAIN_TEXT


@pytest.fixture
def long_text() -> str:
    return LONG_PARAGRAPH


@pytest.fixture
def confluence_settings(tmp_path: Path) -> Settings:
    return Settings(
        confluence_base_url="https://acme.atlassian.net",
        confluence_email="bot@example.com",
        confluence_api_token="secret-token",
        index_dir=str(tmp_path / "index"),
    )


@pytest.fixture
def gdrive_settings(tmp_path: Path) -> Settings:
    return Settings(
        gdrive_folder_id="folder-abc123",
        gdrive_api_key="gdrive-key",
        index_dir=str(tmp_path / "index"),
    )


@pytest.fixture
def faiss_index_dir(tmp_path: Path) -> Path:
    index_dir = tmp_path / "index"
    (index_dir / "faiss").mkdir(parents=True)
    return index_dir


@pytest.fixture
def meta_store(tmp_path: Path) -> MetaStore:
    return MetaStore(tmp_path / "meta.db")


@pytest.fixture
def sample_chunks() -> list[dict]:
    return [
        {
            "chunk_id": "risk-abc12345-deadbeef",
            "department": DepartmentKey.RISK.value,
            "vec_pos": 0,
            "doc_type": "Risk",
            "title": "Escalation Policy",
            "source": "12345",
            "url": "https://acme.atlassian.net/wiki/spaces/RISK/pages/1",
            "anchor": "severity-levels",
            "section": "Severity levels",
            "space": "RISK",
            "labels": serialize_labels(["policy", "risk"]),
            "last_modified": "2025-01-15T10:00:00Z",
            "author": "risk.owner@example.com",
            "acl": serialize_acl(None),
            "lifecycle_state": "active",
            "source_type": "confluence",
            "page": None,
            "text": "First chunk about risk escalation procedures.",
        },
        {
            "chunk_id": "risk-fedcba98-cafebabe",
            "department": DepartmentKey.RISK.value,
            "vec_pos": 1,
            "doc_type": "Risk",
            "title": "Escalation Policy",
            "source": "12345",
            "url": "https://acme.atlassian.net/wiki/spaces/RISK/pages/1",
            "anchor": "severity-levels",
            "section": "Severity levels",
            "space": "RISK",
            "labels": serialize_labels(["policy", "risk"]),
            "last_modified": "2025-01-15T10:00:00Z",
            "author": "risk.owner@example.com",
            "acl": serialize_acl(None),
            "lifecycle_state": "active",
            "source_type": "confluence",
            "page": None,
            "text": "Second chunk covering on-call notification steps.",
        },
    ]


@pytest.fixture
def mock_embedding_dim() -> int:
    return 8


@pytest.fixture
def mock_encode_passages(mock_embedding_dim: int):
    """Return deterministic unit vectors for mocked passage encoding."""

    def _encode(texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, mock_embedding_dim), dtype=np.float32)
        rows = []
        for text in texts:
            digest = hashlib.sha256(text.encode()).digest()
            vec = np.frombuffer(digest[: mock_embedding_dim * 4], dtype=np.float32)[
                :mock_embedding_dim
            ]
            norm = np.linalg.norm(vec)
            rows.append(vec / norm if norm > 0 else vec)
        return np.stack(rows, axis=0).astype(np.float32)

    return _encode


@pytest.fixture
def confluence_page_response() -> dict:
    return {
        "id": "12345",
        "title": "Risk Escalation Policy",
        "version": {"number": 3, "createdAt": "2025-01-15T10:00:00Z"},
        "_links": {"webui": "/spaces/RISK/pages/12345"},
        "body": {
            "storage": {
                "value": SAMPLE_HTML,
            }
        },
    }


@pytest.fixture
def confluence_list_response() -> dict:
    return {
        "results": [
            {"id": "12345", "title": "Risk Escalation Policy"},
            {"id": "67890", "title": "On-call Runbook"},
        ],
        "_links": {},
    }
