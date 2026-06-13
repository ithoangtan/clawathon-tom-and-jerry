from __future__ import annotations

from app.common.stage_trace import build_stage_trace


def test_build_stage_trace_maps_pipeline_stages() -> None:
    state = {
        "question": "What is KYC?",
        "retrieval_query": "KYC know your customer policy",
        "intent": "policy_lookup",
        "target_departments": ["risk"],
        "routing_confidence": 0.82,
        "evidence": {
            "risk": [
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
                "department": "risk",
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
    assert trace["chunks"]["risk"][0]["chunk_id"] == "risk-1"
    assert trace["chunks"]["risk"][0]["score"] == 0.91
    assert trace["grades"]["risk"]["status"] == "answered"
    assert trace["verify"]["risk"]["citation_count"] == 1
    assert trace["citations"][0]["chunk_id"] == "risk-1"
    assert trace["answer"] == state["answer"]
    assert trace["answer_chars"] == len(state["answer"])
    assert trace["status"] == "answered"
