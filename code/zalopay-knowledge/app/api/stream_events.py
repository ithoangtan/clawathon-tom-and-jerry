from __future__ import annotations

"""SSE event enrichment for POST /chat/stream (FR-6.2 timeline)."""

from typing import Any

from app.graph.pipeline import PipelineStepKey, map_node_to_step_key

Department = str

# Human-readable labels for top-level ``node`` events (FE may override via i18n).
STEP_LABELS: dict[str, str] = {
    "ingest_context": "Preparing request",
    "router": "Routing to departments",
    "retrieve": "Searching internal documents",
    "grade": "Grading relevance",
    "synthesize": "Synthesizing answer",
    "verify": "Verifying citations",
    "reconcile": "Reconciling department answers",
    "respond": "Finalizing response",
}

# Top-level LangGraph node → timeline step_key on legacy ``node`` events.
TOP_LEVEL_NODE_STEP: dict[str, str] = {
    "ingest_context": "ingest_context",
    "router": "router",
    "dept_subgraph": "retrieve",
    "reconcile": "reconcile",
    "respond": "respond",
}


def _unique_departments(values: list[str]) -> list[Department]:
    seen: set[str] = set()
    out: list[Department] = []
    for dept in values:
        if dept and dept not in seen:
            seen.add(dept)
            out.append(dept)
    return out


def extract_departments(state: dict[str, Any]) -> list[Department] | None:
    """Best-effort department list from a graph state snapshot or node update."""
    depts: list[str] = []
    for key in ("target_departments", "source_departments", "pinned"):
        raw = state.get(key)
        if isinstance(raw, list):
            depts.extend(str(d) for d in raw if d)

    dept_results = state.get("dept_results")
    if isinstance(dept_results, list):
        for row in dept_results:
            if isinstance(row, dict) and row.get("department"):
                depts.append(str(row["department"]))

    evidence = state.get("evidence")
    if isinstance(evidence, dict):
        depts.extend(str(k) for k in evidence.keys())

    unique = _unique_departments(depts)
    return unique or None


def step_label_for(step_key: str) -> str | None:
    return STEP_LABELS.get(step_key)


def build_node_event_data(
    node_name: str,
    update: dict[str, Any] | None,
    *,
    elapsed_ms: int,
    accumulated: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build backward-compatible SSE ``node`` event payload with optional enrichment."""
    data: dict[str, Any] = {"node": node_name, "elapsed_ms": elapsed_ms}

    step_key = TOP_LEVEL_NODE_STEP.get(node_name) or map_node_to_step_key(node_name)
    if step_key:
        data["step_key"] = step_key
        label = step_label_for(step_key)
        if label:
            data["step_label"] = label

    departments = None
    if isinstance(update, dict):
        departments = extract_departments(update)
    if not departments and isinstance(accumulated, dict):
        departments = extract_departments(accumulated)
    if departments:
        data["departments"] = departments

    return data


def is_pipeline_timeline_step(step_key: str) -> bool:
    """True when ``step_key`` is one of the five FE timeline stages."""
    return step_key in {"router", "retrieve", "grade", "synthesize", "verify"}


def pipeline_step_keys() -> tuple[PipelineStepKey, ...]:
    from app.graph.pipeline import DEPT_STEP_ORDER

    return ("router",) + DEPT_STEP_ORDER
