from __future__ import annotations

from app.api.stream_events import build_node_event_data, extract_departments
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


def test_extract_departments_from_target_and_evidence() -> None:
    depts = extract_departments(
        {
            "target_departments": [RISK, GROW],
            "evidence": {BANK:  []},
        }
    )
    assert depts == ALL_DEPARTMENT_KEYS


def test_build_node_event_data_enriches_known_nodes() -> None:
    data = build_node_event_data(
        "router",
        {"target_departments": [RISK]},
        elapsed_ms=120,
        accumulated={},
    )
    assert data["node"] == "router"
    assert data["step_key"] == "router"
    assert data["step_label"] == "Routing to departments"
    assert data["elapsed_ms"] == 120
    assert data["departments"] == [RISK]


def test_build_node_event_data_backward_compatible_unknown_node() -> None:
    data = build_node_event_data("custom_node", None, elapsed_ms=5, accumulated={})
    assert data == {"node": "custom_node", "elapsed_ms": 5}
