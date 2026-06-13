from __future__ import annotations

from app.common.stage_trace import build_stage_trace
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


def test_build_stage_trace_maps_pipeline_stages() -> None:
    state = {
        "question": "What is KYC?",
        "retrieval_query": "KYC know your customer policy",
        "intent": "policy_lookup",
        "target_departments": [RISK],
        "routing_confidence": 0.82,
        "evidence": {
            RISK: [
                {
                    "chunk_id": "risk-1",
                    "score": 0.91,
                    "title": "KYC Policy",
                    "url": "https://example.com/kyc",
                    "doc_type": "policy",
                    "lifecycle_state": "active",
                }
            ]
        },
        "dept_results": [
            {
                "department": RISK,
                "status": "answered",
                "confidence": 0.88,
                "warnings": [],
                "citations": [{"title": "KYC Policy", "url": "https://example.com/kyc"}],
            }
        ],
        "answer": "KYC requires identity verification [1]",
        "citations": [
            {
                "title": "KYC Policy",
                "url": "https://example.com/kyc",
                "chunk_id": "risk-1",
            }
        ],
        "status": "answered",
        "refusals": [],
    }

    trace = build_stage_trace(state)

    assert trace["query"] == "What is KYC?"
    assert trace["rewrite"] == "KYC know your customer policy"
    assert trace["routing"]["intent"] == "policy_lookup"
    assert trace["chunks"][RISK][0]["chunk_id"] == "risk-1"
    assert trace["chunks"][RISK][0]["score"] == 0.91
    assert trace["grades"][RISK]["status"] == "answered"
    assert trace["verify"][RISK]["citation_count"] == 1
    assert trace["citations"][0]["chunk_id"] == "risk-1"
    assert trace["answer"] == state["answer"]
    assert trace["answer_chars"] == len(state["answer"])
    assert trace["status"] == "answered"
