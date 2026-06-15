# Evidence — Zalopay Wiki Agent Agent QC Report

**Date:** 2026-06-15
**Tester:** QC (automated via Claude Code)
**System under test:** Zalopay Internal Knowledge Agent
**Endpoint:** `POST http://localhost:8080/chat` + UI at `http://localhost:5173`
**Index:** 96 chunks — Confluence synced (Risk: 37, Grow: 23, Bank: 36)
**Model:** `minimax/minimax-m2.5` (auto-fallback từ `qwen/qwen3.7-plus` — daily quota exhausted)

---

## Tổng quan kết quả — 30 Test Cases

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
| [TC11](TC11-auto-out-of-scope-ty-gia.md) | Out-of-scope: tỷ giá USD/VND | Auto-route | Edge | ✅ PASS |
| [TC12](TC12-vi-risk-fraud-escalation.md) | VI bilingual: risk fraud escalation | Explicit risk | Happy | ✅ PASS |
| [TC13](TC13-en-campaign-statuses.md) | EN query: campaign statuses | Auto-route | Happy | ✅ PASS |
| [TC14](TC14-explicit-spin-token.md) | Explicit dept: Spin Token | Explicit grow_enablement | Happy | ✅ PASS |
| [TC15](TC15-auto-pity-system-v2.md) | Pity System v2 deep-dive | Auto-route | Happy | ✅ PASS |
| [TC16](TC16-auto-cross-version-slot-count.md) | Cross-version slot count v1 vs v2 | Auto-route | Edge | ✅ PASS |
| [TC17](TC17-health-endpoint-shape.md) | Health endpoints shape | GET /health* | Contract | ✅ PASS |
| [TC18](TC18-feedback-round-trip.md) | Feedback round-trip | POST /chat → /feedback | Happy | ✅ PASS |
| [TC19](TC19-auth-validation-errors.md) | Auth & validation errors | POST /chat | Edge | ✅ PASS |
| [TC20](TC20-dashboard-api-metrics.md) | Dashboard API metrics shape | GET /api/dashboard | Contract | ✅ PASS |
| [TC21](TC21-ui-chat-answered-response.md) | UI: Chat answered response | Browser UI | Happy | ✅ PASS |
| [TC22](TC22-ui-feedback-thumbs-up.md) | UI: Feedback thumbs up | Browser UI | Happy | ✅ PASS |
| [TC23](TC23-ui-dept-picker-modal.md) | UI: Dept picker modal | Browser UI | Happy | ✅ PASS |
| [TC24](TC24-ui-language-toggle-vi.md) | UI: Language toggle EN→VI | Browser UI | Happy | ✅ PASS |
| [TC25](TC25-ui-new-session-empty-state.md) | UI: New session empty state | Browser UI | Happy | ✅ PASS |
| [TC26](TC26-ui-session-history-sidebar.md) | UI: Session history sidebar | Browser UI | Happy | ✅ PASS |
| [TC27](TC27-ui-dashboard-page.md) | UI: Dashboard page metrics | Browser UI | Happy | ✅ PASS |
| [TC28](TC28-ui-settings-page.md) | UI: Settings page | Browser UI | Happy | ✅ PASS |
| [TC29](TC29-ui-admin-knowledge-sync.md) | UI: Admin knowledge sync | Browser UI | Happy | ✅ PASS |
| [TC30](TC30-ui-spa-deeplink-bug.md) | UI: SPA deep-link black screen | Browser UI | 🔴 BUG | 🔴 FAIL |

**Pass rate: 25/30 full pass | 3/30 minor issue/partial | 2/30 fail**

---

## Summary bằng số

| Verdict | Count |
|---------|-------|
| ✅ PASS | 25 |
| ⚠️ PASS with minor issue | 3 |
| 🔴 FAIL / BUG | 2 |
| **Total** | **30** |

---

## Môi trường test

| Item | Value |
|------|-------|
| API Base | `http://localhost:8080` |
| Frontend | `http://localhost:5173` |
| Auth headers | `X-GreenNode-AgentBase-User-Id: qc-tester` |
| Index source | Confluence: Risk (37) + Grow (23) + Bank (36) = 96 chunks |
| GRADE_THRESHOLD | 0.3 |
| TOPK | 8 |
| BRANCH_TIMEOUT_S | 180 |
| GRAPH_BUDGET_S | 240 |
| Embedding model | `baai/bge-m3` |
| Primary model | `qwen/qwen3.7-plus` (quota exhausted → fallback) |
| Fallback model | `minimax/minimax-m2.5` (auto-discovered from `/v1/models`) |
| Vector store | OpenSearch (HCM03) |
| MySQL | AuditStore + FeedbackStore |

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
| **Root cause** | Chunk chứa kiến trúc diagram ASCII và API listing trong Tech Doc v1 có thể bị split không tối ưu |
| **Suggested fix** | Kiểm tra chunk tại `§1 Kiến trúc tổng quan` và `§6 API Endpoints`. Xem xét tăng `topk` hoặc giảm threshold cho technical queries. |

---

### ⚠️ BUG-02 — Router misclassification: out-of-scope thành ambiguous (TC10)

| Field | Detail |
|-------|--------|
| **Severity** | Low–Medium |
| **TC** | [TC10](TC10-auto-not-in-docs-hotline.md) |
| **Question** | "Tôi muốn biết số điện thoại hotline hỗ trợ khách hàng Zalopay là bao nhiêu?" |
| **Expected** | `status: refused` — giải thích không có trong tài liệu |
| **Actual** | Phát sinh `clarifying_question` thay vì refused |
| **Root cause** | Router không nhận diện "hotline" là out-of-scope |
| **Suggested fix** | Bổ sung signal out-of-scope cho contact info (hotline, email, địa chỉ) trong router prompt |

---

### 🔴 BUG-03 — SPA deep-link routing: black screen on direct navigation (TC30)

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **TC** | [TC30](TC30-ui-spa-deeplink-bug.md) |
| **Repro** | Direct browser navigation to `/chat`, `/dashboard`, `/settings`, or any subroute |
| **Expected** | App renders normally |
| **Actual** | Solid black screen — React app fails to mount |
| **Root cause** | SPA routes not falling back to `index.html` on direct access |
| **Suggested fix** | Nginx config: `try_files $uri $uri/ /index.html`; or Vite preview with `historyApiFallback` |

---

### ⚠️ BUG-04 — bge-m3 cold-start: first query after restart exceeds GRAPH_BUDGET_S (known)

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **Observed in** | TC13 first run (248s encoding → false negative) |
| **Expected** | Query returns answer in <240s |
| **Actual** | First POST /chat after process restart fails with "not in docs" (timeout) |
| **Root cause** | bge-m3 CPU encoding takes ~248s cold-start vs GRAPH_BUDGET_S=240 |
| **Workaround** | Send warm-up request after deploy; subsequent requests ~10s |
| **Suggested fix** | Add warm-up endpoint, pre-load embedding model at startup, or increase GRAPH_BUDGET_S |

---

## Observations tổng quát

### ✅ Điều hoạt động tốt

1. **Auto-routing chính xác** — tất cả câu hỏi route đúng dept không cần chỉ định
2. **Model auto-fallback** — khi `qwen/qwen3.7-plus` hết quota, tự switch sang `minimax/minimax-m2.5` liền mạch
3. **Cross-version handling** — phân biệt rõ v1 vs v2, không confuse thông tin
4. **Refusal on real-time data** — từ chối đúng câu hỏi tỷ giá, không hallucinate
5. **Citation-grounded** — mọi answer đều có citations trace ngược về Confluence
6. **Bilingual bidirectional** — VI question → VI answer; EN question → EN answer
7. **Health endpoints** — đầy đủ liveness/readiness probes cho K8s
8. **Feedback round-trip** — POST /chat → feedback_id → POST /feedback 204 hoạt động
9. **Auth validation** — missing headers 400, bad body 422, extra fields rejected
10. **UI i18n** — full EN↔VI toggle instant, tất cả elements translated
11. **Dashboard metrics** — real-time metrics từ MySQL, không mock
12. **Admin sync panel** — live sync status per dept, trigger sync button

### ⚠️ Điểm cần cải thiện

1. **Chunking quality** (BUG-01) — Tech Doc chunks split không tối ưu, mất context API listing
2. **Router out-of-scope coverage** (BUG-02) — Chưa cover contact info intent
3. **SPA deep-link** (BUG-03) — Production Nginx config cần `try_files`
4. **bge-m3 warm-up** (BUG-04) — Cần warm-up sau restart để tránh cold-start timeout
