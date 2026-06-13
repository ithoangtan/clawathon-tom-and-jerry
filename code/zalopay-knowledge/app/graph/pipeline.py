from __future__ import annotations

"""Pipeline step mapping and SSE event payloads for the LangGraph timeline.

Maps raw LangGraph node names to stable ``step_key`` values the frontend can
translate (router → retrieve → grade → synthesize → verify).
"""

import time
from datetime import datetime, timezone
from typing import Any, Callable, Literal

PipelineStepKey = Literal["router", "retrieve", "grade", "synthesize", "verify"]
PipelinePhase = Literal["start", "end"]

# Raw node name → stable step_key for FE i18n.
NODE_STEP_MAP: dict[str, PipelineStepKey] = {
    "router": "router",
    "retrieve": "retrieve",
    "grade": "grade",
    "synthesize": "synthesize",
    "verify": "verify",
}

# Department subgraph execution order (matches build_dept_subgraph topology).
DEPT_STEP_ORDER: tuple[PipelineStepKey, ...] = (
    "retrieve",
    "grade",
    "synthesize",
    "verify",
)

_PIPELINE_STEP_SET = frozenset(NODE_STEP_MAP.values())


def map_node_to_step_key(node_name: str) -> PipelineStepKey | None:
    """Return the stable pipeline step for a LangGraph node, if any."""
    return NODE_STEP_MAP.get(node_name)


def is_pipeline_step(step_key: str) -> bool:
    return step_key in _PIPELINE_STEP_SET


def next_dept_step(step_key: PipelineStepKey) -> PipelineStepKey | None:
    """Return the step that follows ``step_key`` inside a department branch."""
    try:
        idx = DEPT_STEP_ORDER.index(step_key)
    except ValueError:
        return None
    if idx + 1 >= len(DEPT_STEP_ORDER):
        return None
    return DEPT_STEP_ORDER[idx + 1]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_pipeline_event(
    *,
    step_key: PipelineStepKey,
    phase: PipelinePhase,
    node: str,
    departments: list[str] | None = None,
    stream_started: float,
    step_started: float | None = None,
) -> dict[str, Any]:
    """Build a structured pipeline payload for SSE ``pipeline`` events."""
    now = time.perf_counter()
    elapsed_ms = int((now - stream_started) * 1000)
    step_elapsed_ms: int | None = None
    if phase == "end" and step_started is not None:
        step_elapsed_ms = int((now - step_started) * 1000)

    return {
        "step_key": step_key,
        "phase": phase,
        "node": node,
        "departments": list(departments or []),
        "ts": utc_now_iso(),
        "elapsed_ms": elapsed_ms,
        "step_elapsed_ms": step_elapsed_ms,
    }


class PipelineTracker:
    """Tracks per-step timing while translating graph updates to pipeline events."""

    def __init__(self, stream_started: float | None = None) -> None:
        self._stream_started = stream_started if stream_started is not None else time.perf_counter()
        self._step_started: dict[str, float] = {}

    @property
    def stream_started(self) -> float:
        return self._stream_started

    def _tracking_key(self, step_key: PipelineStepKey, departments: list[str]) -> str:
        if len(departments) == 1:
            return f"{step_key}:{departments[0]}"
        return step_key

    def start_event(
        self,
        step_key: PipelineStepKey,
        *,
        node: str,
        departments: list[str] | None = None,
    ) -> dict[str, Any]:
        depts = list(departments or [])
        key = self._tracking_key(step_key, depts)
        self._step_started[key] = time.perf_counter()
        return build_pipeline_event(
            step_key=step_key,
            phase="start",
            node=node,
            departments=depts,
            stream_started=self._stream_started,
        )

    def end_event(
        self,
        step_key: PipelineStepKey,
        *,
        node: str,
        departments: list[str] | None = None,
    ) -> dict[str, Any]:
        depts = list(departments or [])
        key = self._tracking_key(step_key, depts)
        step_started = self._step_started.pop(key, None)
        return build_pipeline_event(
            step_key=step_key,
            phase="end",
            node=node,
            departments=depts,
            stream_started=self._stream_started,
            step_started=step_started,
        )


class PipelineEmitter:
    """Emits custom stream payloads from inside graph nodes (e.g. dept branches)."""

    def __init__(
        self,
        writer: Callable[[dict[str, Any]], None],
        *,
        department: str,
        stream_started: float | None = None,
    ) -> None:
        self._writer = writer
        self._department = department
        self._tracker = PipelineTracker(stream_started)

    def _emit(self, payload: dict[str, Any]) -> None:
        self._writer(payload)

    def branch_start(self) -> None:
        """Signal the first department-scoped step is starting."""
        self._emit(
            self._tracker.start_event(
                "retrieve",
                node="retrieve",
                departments=[self._department],
            )
        )

    def on_node_complete(self, node_name: str) -> None:
        """Emit end for a completed subgraph node and start the next step."""
        step_key = map_node_to_step_key(node_name)
        if step_key is None or step_key == "router":
            return

        depts = [self._department]
        self._emit(
            self._tracker.end_event(step_key, node=node_name, departments=depts)
        )

        nxt = next_dept_step(step_key)
        if nxt is not None:
            self._emit(
                self._tracker.start_event(nxt, node=nxt, departments=depts)
            )
