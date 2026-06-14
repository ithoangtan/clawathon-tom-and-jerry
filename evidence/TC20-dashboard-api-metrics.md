# TC20 — Dashboard API metrics shape

| Field | Value |
|-------|-------|
| **Test ID** | TC20 |
| **Mode** | API — `GET /api/dashboard` |
| **Type** | Contract — metrics fields & ranges |
| **Verdict** | ✅ PASS |

---

## 📤 Request

```
GET http://localhost:8080/api/dashboard
X-GreenNode-AgentBase-User-Id: qc-tester
X-GreenNode-AgentBase-Session-Id: tc20-<timestamp>
```

---

## 📥 Response

| Field | Value |
|-------|-------|
| **status_code** | `200` |
| **query_count** | `14` |
| **deflection_rate** | `0.714` (71.4%) |
| **answered_wrong_rate** | `0.5` (50%) |
| **feedback_up** | `2` |
| **feedback_down** | `2` |
| **refusal_rate** | `0.286` (28.6%) |
| **partial_rate** | `0.0` |
| **latency_p50_ms** | present |
| **latency_p95_ms** | present |
| **eval_faithfulness** | present |
| **eval_answer_relevance** | present |
| **eval_refusal_precision** | present |
| **eval_refusal_recall** | present |
| **eval_context_recall_at_5** | present |
| **eval_context_precision_at_5** | present |
| **history** | present (time series) |

### All rate fields in [0.0, 1.0]

| Rate Field | Value | In range? |
|------------|-------|-----------|
| deflection_rate | 0.714 | ✅ |
| answered_wrong_rate | 0.5 | ✅ |
| refusal_rate | 0.286 | ✅ |
| partial_rate | 0.0 | ✅ |
| conflict_rate | 0.0 | ✅ |

---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| `status_code` = 200 | ✅ | 200 | ✅ |
| `query_count` ≥ 0 | ✅ | 14 | ✅ |
| `deflection_rate` in [0,1] | ✅ | 0.714 | ✅ |
| `feedback_up` và `feedback_down` present | ✅ | 2 each | ✅ |
| Eval metrics fields present | ✅ | all 6 present | ✅ |
| `history` time-series present | ✅ | present | ✅ |
| All rates in [0.0, 1.0] | ✅ | ✅ all | ✅ |

---

## 📝 Ghi chú

- Dashboard API expose đầy đủ metrics theo spec: query count, rates, feedback counts, latency percentiles
- Eval metrics (faithfulness, answer_relevance, context_recall/precision) từ RAG eval harness
- `deflection_rate` = tỷ lệ câu hỏi không được trả lời đầy đủ (refused + partial)
- Total 14 queries logged trong MySQL `queries` table tại thời điểm test
