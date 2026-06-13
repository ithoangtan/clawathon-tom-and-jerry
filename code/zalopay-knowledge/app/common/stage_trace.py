from __future__ import annotations

"""Per-stage query tracing for ops/audit (G5).

Builds a structured trace from terminal LangGraph state:
query → rewrite → chunks+scores → grades → answer → citations → verify.
"""

from typing import Any


def _chunk_summary(chunk: dict) -> dict[str, Any]:
    return {
        "chunk_id": chunk.get("chunk_id"),
        "score": chunk.get("score"),
        "title": chunk.get("title"),
        "url": chunk.get("url"),
        "doc_type": chunk.get("doc_type"),
        "lifecycle_state": chunk.get("lifecycle_state"),
    }


def _citation_summary(citation: dict) -> dict[str, Any]:
    return {
        "title": citation.get("title"),
        "url": citation.get("url"),
        "chunk_id": citation.get("chunk_id"),
        "section": citation.get("section"),
        "page": citation.get("page"),
    }


def build_stage_trace(state: dict[str, Any]) -> dict[str, Any]:
    """Extract an ops-friendly pipeline trace from graph terminal state."""
    evidence = state.get("evidence") or {}
    chunks_trace: dict[str, list[dict[str, Any]]] = {}
    if isinstance(evidence, dict):
        for dept, chunks in evidence.items():
            if isinstance(chunks, list):
                chunks_trace[str(dept)] = [
                    _chunk_summary(c) for c in chunks if isinstance(c, dict)
                ]

    grades_trace: dict[str, dict[str, Any]] = {}
    verify_trace: dict[str, dict[str, Any]] = {}
    dept_results = state.get("dept_results") or []
    if isinstance(dept_results, list):
        for row in dept_results:
            if not isinstance(row, dict):
                continue
            dept = row.get("department")
            if not dept:
                continue
            grades_trace[str(dept)] = {
                "status": row.get("status"),
                "confidence": row.get("confidence"),
                "warnings": list(row.get("warnings") or []),
            }
            verify_trace[str(dept)] = {
                "status": row.get("status"),
                "citation_count": len(row.get("citations") or []),
            }

    citations = state.get("citations") or []
    citation_trace = [
        _citation_summary(c) for c in citations if isinstance(c, dict)
    ]

    answer = state.get("answer") or ""
    answer_preview = answer[:500] if answer else ""
    return {
        "query": state.get("question"),
        "rewrite": state.get("retrieval_query"),
        "routing": {
            "intent": state.get("intent"),
            "target_departments": list(state.get("target_departments") or []),
            "confidence": state.get("routing_confidence"),
        },
        "chunks": chunks_trace,
        "grades": grades_trace,
        "answer": answer_preview,
        "answer_chars": len(answer),
        "citations": citation_trace,
        "verify": verify_trace,
        "refusals": list(state.get("refusals") or []),
        "status": state.get("status"),
    }
