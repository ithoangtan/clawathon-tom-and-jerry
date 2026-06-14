# TC27 — UI: Dashboard page — Usage & Health metrics

| Field | Value |
|-------|-------|
| **Test ID** | TC27 |
| **Mode** | UI — Browser navigation |
| **Type** | Happy case — dashboard metrics rendering |
| **Verdict** | ✅ PASS |

---

## 🖱️ UI Interaction

| Step | Action | Selector / Method |
|------|--------|-------------------|
| 1 | Navigate to app root | `http://localhost:5173/` |
| 2 | Click "Dashboard" in top nav | `a[href="/dashboard"]` |
| 3 | Observe metrics cards | Full dashboard rendered |

---

## 📸 Observed UI State

**Page title:** "Usage & Health"
**Subtitle:** "Real-time usage metrics, sync health, and query history for your knowledge agent."

**Metric cards (observed values at test time):**

| Card | Value |
|------|-------|
| TOTAL QUERIES | **20** |
| DEFLECTION RATE | **75.0%** |
| ANSWERED-WRONG RATE | **40.0%** |
| REFUSAL RATE | **25.0%** |
| PARTIAL ANSWER RATE | **0.0%** |
| CONFLICT RATE | **0.0%** |
| LATENCY P50 | **21.9 s** |
| LATENCY P95 | **206.0 s** |
| THUMBS UP | **3** |
| THUMBS DOWN | **2** |
| EVAL FAITHFULNESS | **75.7%** |
| REFUSAL PRECISION | **100.0%** |

---

## 🔍 Đối chiếu UI

| UI Element | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| Dashboard nav item active (underline) | ✅ | ✅ | ✅ |
| Total queries card | ≥ 1 | 20 | ✅ |
| Deflection rate in [0%, 100%] | ✅ | 75.0% | ✅ |
| Feedback counts (up/down) | ✅ | 3 / 2 | ✅ |
| Latency metrics visible | ✅ | P50=21.9s, P95=206s | ✅ |
| Eval metrics visible | ✅ | faithfulness, precision | ✅ |
| "Dashboard Mock: tắt" badge | visible | ✅ visible | ✅ |

---

## 📝 Ghi chú

- P95 latency = 206s phản ánh bge-m3 cold-start bug (TC30) — first query sau restart mất >200s
- P50 = 21.9s là warm latency sau bge-m3 đã được cache
- `Dashboard Mock: tắt` badge xác nhận data từ real MySQL, không phải mock
- REFUSAL PRECISION = 100% — agent không refuse câu hỏi có trong docs (precision tốt)
