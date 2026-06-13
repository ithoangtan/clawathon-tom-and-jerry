from __future__ import annotations

import time

from app.graph.pipeline import (
    DEPT_STEP_ORDER,
    NODE_STEP_MAP,
    PipelineEmitter,
    PipelineTracker,
    build_pipeline_event,
    map_node_to_step_key,
    next_dept_step,
)


def test_node_step_map_covers_dept_subgraph_nodes() -> None:
    assert set(NODE_STEP_MAP) == {"router", "retrieve", "grade", "synthesize", "verify"}
    assert DEPT_STEP_ORDER == ("retrieve", "grade", "synthesize", "verify")


def test_map_node_to_step_key_unknown_returns_none() -> None:
    assert map_node_to_step_key("ingest_context") is None
    assert map_node_to_step_key("reconcile") is None


def test_next_dept_step_order() -> None:
    assert next_dept_step("retrieve") == "grade"
    assert next_dept_step("grade") == "synthesize"
    assert next_dept_step("synthesize") == "verify"
    assert next_dept_step("verify") is None


def test_build_pipeline_event_includes_timing_fields() -> None:
    started = time.perf_counter()
    time.sleep(0.001)
    payload = build_pipeline_event(
        step_key="router",
        phase="end",
        node="router",
        departments=["risk"],
        stream_started=started,
        step_started=started,
    )
    assert payload["step_key"] == "router"
    assert payload["phase"] == "end"
    assert payload["node"] == "router"
    assert payload["departments"] == ["risk"]
    assert payload["elapsed_ms"] >= 0
    assert payload["step_elapsed_ms"] is not None
    assert payload["ts"].endswith("Z")


def test_pipeline_tracker_start_and_end() -> None:
    tracker = PipelineTracker()
    start = tracker.start_event("retrieve", node="retrieve", departments=["risk"])
    assert start["phase"] == "start"
    assert start["step_elapsed_ms"] is None

    end = tracker.end_event("retrieve", node="retrieve", departments=["risk"])
    assert end["phase"] == "end"
    assert end["step_elapsed_ms"] is not None


def test_pipeline_emitter_streams_dept_steps() -> None:
    emitted: list[dict] = []

    def writer(payload: dict) -> None:
        emitted.append(payload)

    emitter = PipelineEmitter(writer, department="risk")
    emitter.branch_start()
    emitter.on_node_complete("retrieve")
    emitter.on_node_complete("grade")

    assert emitted[0]["step_key"] == "retrieve"
    assert emitted[0]["phase"] == "start"
    assert emitted[0]["departments"] == ["risk"]

    assert emitted[1]["step_key"] == "retrieve"
    assert emitted[1]["phase"] == "end"

    assert emitted[2]["step_key"] == "grade"
    assert emitted[2]["phase"] == "start"

    assert emitted[3]["step_key"] == "grade"
    assert emitted[3]["phase"] == "end"

    assert emitted[4]["step_key"] == "synthesize"
    assert emitted[4]["phase"] == "start"
