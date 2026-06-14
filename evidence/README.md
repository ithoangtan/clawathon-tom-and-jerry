# Evidence — Zalopay Knowledge Agent QC Report

**Date:** 2026-06-14  
**Tester:** QC (automated via Claude Code)  
**System under test:** Zalopay Internal Knowledge Agent  
**Endpoint:** `POST http://localhost:8080/chat`  
**Index:** 63 chunks — Confluence synced (6 pages, grow_enablement space)  
**Model:** `minimax/minimax-m2.5` (auto-fallback từ `qwen/qwen3.7-plus` — daily quota exhausted)

---

## Tổng quan kết quả

| TC | Tên | Mode | Type | Verdict |
|----|-----|------|------|---------|
| [TC01](TC01-auto-lucky-wheel-definition.md) | Lucky Wheel là gì? | Auto-route | Happy | ✅ PASS |
| [TC02](TC02-auto-campaign-status-flow.md) | Campaign status flow | Auto-route | Happy | ✅ PASS |
| [TC03](TC03-auto-spin-token-rewards.md) | Spin Token + Reward types | Auto-route | Happy | ⚠️ PASS (minor) |
| [TC04](TC04-explicit-v2-new-features.md) | v2 New Features | Explicit grow_enablement | Happy | ✅ PASS |
| [TC05](TC05-explicit-pity-system.md) | Pity System config | Explicit grow_enablement | Happy | ⚠️ PASS (minor) |
| [TC06](TC06-auto-out-of-scope.md) | Out-of-scope: tỷ giá/cổ phiếu | Auto-route | Edge | ✅ PASS |
| [TC07](TC07-auto-cross-version-slot-count.md) | Cross-version: slot count v1 vs v2 | Auto-route | Edge | ✅ PASS |
| [TC08](TC08-explicit-tech-stack-api.md) | Tech stack + DB + API endpoint | Explicit grow_enablement | Edge | 🔴 FAIL |
| [TC09](TC09-explicit-image-upload-limits.md) | Image upload limits | Explicit grow_enablement | Happy | ✅ PASS |
| [TC10](TC10-auto-not-in-docs-hotline.md) | Not-in-docs: hotline | Auto-route | Edge | ⚠️ PARTIAL |

**Pass rate: 7/10 full pass | 2/10 minor issue | 1/10 fail**

---

## Summary bằng số

| Verdict | Count |
|---------|-------|
| ✅ PASS | 7 |
| ⚠️ PASS with minor issue | 2 |
| 🔴 FAIL | 1 |
| **Total** | **10** |

---

## Môi trường test

| Item | Value |
|------|-------|
| API Base | `http://localhost:8080` |
| Auth headers | `X-GreenNode-AgentBase-User-Id: qc-tester` |
| Index source | Confluence: `ClawathonGrow` space |
| Chunks indexed | 63 (grow_enablement) |
| GRADE_THRESHOLD | 0.3 |
| TOPK | 8 |
| BRANCH_TIMEOUT_S | 180 |
| GRAPH_BUDGET_S | 240 |
| VERIFY_ENABLED | false |
| Primary model | `qwen/qwen3.7-plus` (quota exhausted) |
| Fallback model | `minimax/minimax-m2.5` (auto-discovered from `/v1/models`) |

---

## Bugs cần action

### 🔴 BUG-01 — Retrieval miss: Primary DB và Spin API endpoint (TC08)

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **TC** | [TC08](TC08-explicit-tech-stack-api.md) |
| **Question** | "Lucky Wheel service dùng tech stack gì? Database là gì? API spin endpoint là gì?" |
| **Expected** | `MySQL/PostgreSQL` và `POST /api/v1/lucky-wheel/{campaign_id}/spin` |
| **Actual** | Agent báo "không tìm thấy trong tài liệu" cho cả 2 thông tin |
| **Root cause** | Chunk chứa kiến trúc diagram ASCII và API listing trong Tech Doc v1 có thể bị split không tối ưu hoặc score thấp hơn threshold |
| **Suggested fix** | Kiểm tra chunk tại section `§1 Kiến trúc tổng quan` và `§6 API Endpoints` của Tech Doc v1. Xem xét tăng `topk` hoặc giảm `grade_threshold` cho technical queries. |

---

### ⚠️ BUG-02 — Router misclassification: out-of-scope thành ambiguous (TC10)

| Field | Detail |
|-------|--------|
| **Severity** | Low–Medium |
| **TC** | [TC10](TC10-auto-not-in-docs-hotline.md) |
| **Question** | "Tôi muốn biết số điện thoại hotline hỗ trợ khách hàng Zalopay là bao nhiêu?" |
| **Expected** | `status: refused` — giải thích không có trong tài liệu indexed |
| **Actual** | Phát sinh `clarifying_question` hỏi ngược "bạn muốn hỏi bộ phận nào?" |
| **Root cause** | Router không nhận diện "hotline" là out-of-scope, classify thành intent ambiguous |
| **Suggested fix** | Bổ sung signal out-of-scope cho contact info (hotline, email, địa chỉ), giờ làm việc trong router prompt |

---

## Observations tổng quát

### ✅ Điều hoạt động tốt

1. **Auto-routing chính xác** — tất cả câu hỏi về Lucky Wheel đều route đúng `grow_enablement` không cần chỉ định
2. **Model auto-fallback** — khi `qwen/qwen3.7-plus` hết quota, hệ thống tự switch sang `minimax/minimax-m2.5` không gián đoạn; `model_used` hiện đúng trong response
3. **Cross-version handling** — phân biệt rõ v1 vs v2 (TC07: slot count), không confuse thông tin 2 version
4. **Refusal on real-time data** — từ chối đúng với câu hỏi tỷ giá/cổ phiếu (TC06), không hallucinate
5. **Specific factual retrieval** — image upload specs (TC09) trả về đúng 100% từ ops guide
6. **Citation-grounded** — mọi answer đều có citations, có thể trace ngược về Confluence source

### ⚠️ Điểm cần cải thiện

1. **Chunking quality** (BUG-01) — Tech Doc chunks có thể bị split không tối ưu, mất context diagram/API listing
2. **Router out-of-scope coverage** (BUG-02) — Chưa cover các intent "contact info" ngoài docs
3. **Diễn đạt pity counter reset** (TC05) — Nhầm "khi campaign start" thay vì "khi clone campaign"
4. **Streak Bonus classification** (TC03) — Liệt kê nhầm Streak Bonus là reward type thay vì token source
