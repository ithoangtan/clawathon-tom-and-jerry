from __future__ import annotations

"""Graph assembly — wires the eight nodes into the runnable LangGraph app.

Topology (matches 2-requirements/03-ARCHITECTURE.md §2):

    START → ingest_context → router ─┬─► (Send ×N) dept_subgraph → reconcile → respond → END
                                     └─► respond   (clarify / short-circuit)
            ingest_context ──(index unavailable)──► respond

Each department runs the same compiled **subgraph** (``retrieve → grade →
synthesize → verify``) in parallel, fanned out with the LangGraph ``Send`` API.
The subgraph writes ``dept_results`` / ``evidence`` back into the parent state
through the parent's commutative reducers, so concurrent branches never clobber
each other and ``reconcile`` runs once after all branches join.

Per-branch timeout (FR / failure-mode "Dept branch timeout"): each ``Send``
payload carries a ``deadline_ts`` = ``min(graph deadline, now + BRANCH_TIMEOUT)``.
Every node checks it and degrades to a refusal rather than overrunning, so
``reconcile`` proceeds with whichever branches finished.
"""

import logging
import time
from dataclasses import dataclass
from typing import Callable, Optional

from langgraph.graph import END, START, StateGraph

try:  # langgraph 0.2 exposes Send from .types; older layouts use .constants
    from langgraph.types import Send
except ImportError:  # pragma: no cover - import-path shim
    from langgraph.constants import Send  # type: ignore

from app.config import Settings, get_settings
from app.graph.nodes import (
    make_grade_node,
    make_ingest_context_node,
    make_reconcile_node,
    make_respond_node,
    make_retrieve_node,
    make_router_node,
    make_synthesize_node,
    make_verify_node,
)
from app.graph.nodes.ingest_context import RecallFn
from app.graph.state import DeptResult, DeptState, GraphState
from app.ports.checkpointer import CheckpointerPort
from app.ports.llm import LLMPort
from app.ports.retriever import RetrieverPort

logger = logging.getLogger(__name__)

DEPT_SUBGRAPH = "dept_subgraph"


# ── Dependency bundle ─────────────────────────────────────────────────────────

@dataclass
class GraphDeps:
    """The ports + callables the graph needs, injected at build time.

    Keeping this in one struct lets ``deps.py`` (a later wiring module) decide
    local vs. AgentBase adapters without the build code knowing the difference.
    """

    llm: LLMPort
    retriever: RetrieverPort
    checkpointer: Optional[CheckpointerPort] = None
    recall: Optional[RecallFn] = None
    settings: Optional[Settings] = None


# ── Department subgraph ───────────────────────────────────────────────────────

def build_dept_subgraph(deps: GraphDeps):
    """Compile the per-department pipeline ``retrieve → grade → synthesize → verify``.

    Operates on :class:`DeptState`.  Compiled without its own checkpointer — the
    parent graph's checkpointer covers the whole run.
    """
    cfg = deps.settings or get_settings()
    sg = StateGraph(DeptState)

    sg.add_node("retrieve", make_retrieve_node(deps.retriever, settings=cfg))
    sg.add_node("grade", make_grade_node(deps.llm, settings=cfg))
    sg.add_node("synthesize", make_synthesize_node(deps.llm, settings=cfg))
    sg.add_node("verify", make_verify_node(deps.llm, settings=cfg))

    sg.add_edge(START, "retrieve")
    sg.add_edge("retrieve", "grade")
    sg.add_edge("grade", "synthesize")
    sg.add_edge("synthesize", "verify")
    sg.add_edge("verify", END)

    return sg.compile()


def _make_dept_branch(subgraph) -> Callable[[DeptState], dict]:
    """Wrap the compiled department subgraph as a single fan-out node.

    Why a wrapper instead of adding the compiled subgraph directly: the subgraph
    shares input keys (``question``, ``role``, …) with the parent ``GraphState``.
    If added directly, every parallel branch would write those single-value keys
    back to the parent in the same superstep → ``InvalidUpdateError``.  By
    invoking the subgraph here and returning ONLY the reduced keys
    (``dept_results`` / ``evidence``), branches merge cleanly via the parent's
    commutative reducers.

    It also isolates branch failures: a crash or overrun in one department
    becomes a ``timeout`` :class:`DeptResult` so ``reconcile`` still proceeds
    with the branches that finished (failure-mode "Dept branch timeout").
    """

    def dept_branch(state: DeptState) -> dict:
        department = state.get("department", "?")
        try:
            result = subgraph.invoke(state)
            return {
                "dept_results": result.get("dept_results", []),
                "evidence": result.get("evidence", {}),
            }
        except Exception:  # noqa: BLE001 — never let one branch kill the run
            logger.exception("dept branch %s failed; degrading to timeout", department)
            return {
                "dept_results": [
                    DeptResult(
                        department=department,
                        status="timeout",
                        answer="",
                        citations=[],
                        confidence=0.0,
                        warnings=["branch_error"],
                    )
                ]
            }

    return dept_branch


# ── Top-level graph ───────────────────────────────────────────────────────────

def build_graph(deps: GraphDeps):
    """Build and compile the full agent graph.

    Args:
        deps: Ports and callables (LLM, retriever, optional checkpointer/recall).

    Returns:
        A compiled LangGraph app.  Invoke with
        ``config={"configurable": {"thread_id": session_id, "actor_id": user_id}}``
        and an initial :class:`GraphState`.
    """
    cfg = deps.settings or get_settings()
    dept_subgraph = build_dept_subgraph(deps)

    g = StateGraph(GraphState)
    g.add_node("ingest_context", make_ingest_context_node(deps.retriever, recall=deps.recall, settings=cfg))
    g.add_node("router", make_router_node(deps.llm, settings=cfg))
    g.add_node(DEPT_SUBGRAPH, _make_dept_branch(dept_subgraph))
    g.add_node("reconcile", make_reconcile_node(deps.llm, settings=cfg))
    g.add_node("respond", make_respond_node(settings=cfg))

    g.add_edge(START, "ingest_context")

    # ingest_context refuses early (index not ready) → skip straight to respond.
    g.add_conditional_edges(
        "ingest_context",
        _route_after_ingest,
        {"router": "router", "respond": "respond"},
    )

    # router either fans out to department branches or short-circuits to respond.
    g.add_conditional_edges(
        "router",
        _make_route_after_router(cfg),
        [DEPT_SUBGRAPH, "respond"],
    )

    # every department branch converges on reconcile, then respond.
    g.add_edge(DEPT_SUBGRAPH, "reconcile")
    g.add_edge("reconcile", "respond")
    g.add_edge("respond", END)

    saver = deps.checkpointer.get_saver() if deps.checkpointer else None
    compiled = g.compile(checkpointer=saver)
    logger.info("Graph compiled (checkpointer=%s)", "on" if saver else "off")
    return compiled


# ── Conditional-edge routers ──────────────────────────────────────────────────

def _route_after_ingest(state: GraphState) -> str:
    """Skip routing entirely when ingest produced a terminal refusal."""
    if state.get("status") == "refused":
        return "respond"
    return "router"


def _make_route_after_router(cfg: Settings) -> Callable[[GraphState], object]:
    """Build the post-router branch selector (closes over settings for timeouts)."""

    def _route_after_router(state: GraphState):
        targets = state.get("target_departments") or []
        # Clarify, short-circuit intents, and "no usable department" all land here.
        if not targets or state.get("clarify_question"):
            return "respond"

        deadline = _branch_deadline(state.get("deadline_ts"), cfg.branch_timeout_s)
        return [
            Send(DEPT_SUBGRAPH, _dept_payload(state, dept, deadline))
            for dept in targets
        ]

    return _route_after_router


# ── Helpers ───────────────────────────────────────────────────────────────────

def _branch_deadline(graph_deadline: float | None, branch_timeout_s: float) -> float:
    """Compute a per-branch deadline bounded by the global graph budget."""
    branch = time.time() + branch_timeout_s
    if graph_deadline:
        return min(graph_deadline, branch)
    return branch


def _dept_payload(state: GraphState, department: str, deadline_ts: float) -> DeptState:
    """Build the isolated :class:`DeptState` Send payload for one department."""
    return DeptState(
        department=department,
        question=state.get("question", ""),
        role=state.get("role", ""),
        home_department=state.get("home_department", ""),
        request_language=state.get("request_language", "en"),
        recalled_preferences=state.get("recalled_preferences"),
        deadline_ts=deadline_ts,
    )
