# TC08 — Explicit grow_enablement: Tech Stack, DB, API Endpoint

| Field | Value |
|-------|-------|
| **Test ID** | TC08 |
| **Mode** | Explicit department — `target_departments: ["grow_enablement"]` |
| **Type** | Edge case — thông tin kỹ thuật chi tiết |
| **Verdict** | 🔴 FAIL — Retrieval miss |

---

## 📤 Request

```
POST http://localhost:8080/chat
X-GreenNode-AgentBase-User-Id: qc-tester
Content-Type: application/json
```

```json
{
  "question": "Lucky Wheel service dùng tech stack gì? Database là gì? API spin endpoint là gì?",
  "target_departments": ["grow_enablement"]
}
```

---

## 📥 Response

| Field | Value |
|-------|-------|
| **status** | ✅ answered |
| **model_used** | `minimax/minimax-m2.5` |
| **source_departments** | `['grow_enablement']` |
| **citations** | 2 |
| **confidence** | `0.640` |

### Answer

## Lucky Wheel Service - Thông tin kỹ thuật

### Tech Stack

| Layer | Công nghệ |
|-------|-----------|
| Backend | Java/Spring [1] |
| Frontend (công cụ config) | React/Next.js [1] |
| End User | Native App [1] |

### Database

Nguồn dữ liệu không nêu rõ tên database cụ thể (MySQL/PostgreSQL). Tuy nhiên, hệ thống sử dụng:

- **Redis** cho caching và quản lý stock (atomic decrement) [1]
- **MySQL/PostgreSQL** cho các bảng dữ liệu: Campaign, Reward Pool, Spin Token Ledger, Spin History, Task [1]

### API Spin Endpoint

Nguồn không cung cấp URL endpoint cụ thể cho API spin. Tuy nhiên, logic spin được mô tả như sau:

**Luồng xử lý spin:**
1. Lấy danh sách reward khả dụng từ reward pool
2. Kiểm tra guaranteed reward (pity system)
3. Random theo trọng số (weight-based)
4. Trừ stock qua Redis atomic DECR (tránh race condition)
5. Ghi ledger + history
6. Phát thưởng async qua queue [1]

**Lưu ý quan trọng:**
- Dùng `idempotency_key` để tránh double spin khi app retry [1]
- Dùng Redis DECR với check `>= 0` để tránh oversell [1]
- Phát thưởng async, không block response spin [1]

---

> **Lưu ý:** Nguồn không cung cấp đường dẫn API endpoint cụ thể. Vui lòng kiểm tra tài liệu API chi tiết hoặc liên hệ đội phát triển để lấy endpoint chính xác.

### Citations

**[1]** [Lucky Wheel Technical Documentation for Developers](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/98343/Lucky+Wheel+Technical+Documentation+for+Developers)
  - Doc type: `Technical` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Technical Documentation Audience: Backend & Frontend Developer Stack: Java/Spring (BE), React/Next.js (FE tool), Native App (end user) Version: 1.0 1. Kiến trúc tổng quan wide 760 2. Dat_

**[2]** [Lucky Wheel Technical Documentation v2: Features, Architecture, and API Updates](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/98359/Lucky+Wheel+Technical+Documentation+v2+Features+Architecture+and+API+Updates)
  - Doc type: `Technical` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Technical Documentation v2 Audience: Backend & Frontend Developer Stack: Java/Spring (BE), React/Next.js (FE tool), Native App (end user) Version: 2.0 Changelog v2 Thay đổi Mô tả wheel_t_


---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Mock Doc (Tech Doc v1) | Agent trả lời | Kết quả |
|---|---|---|---|
| Backend: Java/Spring | ✅ tech doc v1 | ✅ đúng | ✅ Đúng |
| Frontend Tool: React/Next.js | ✅ tech doc v1 | ✅ đúng | ✅ Đúng |
| End User: Native App | ✅ tech doc v1 | ✅ đúng | ✅ Đúng |
| Primary DB: MySQL / PostgreSQL | ✅ tech doc v1 kiến trúc diagram: `MySQL / PostgreSQL` | Agent: "không tìm thấy rõ MySQL/PostgreSQL" | 🔴 **BUG: Retrieval miss** |
| Redis (cache) | ✅ tech doc v1 | ✅ đề cập đầy đủ | ✅ Đúng |
| API endpoint: `POST /api/v1/lucky-wheel/{campaign_id}/spin` | ✅ tech doc v1 §6 API | Agent: "không tìm thấy spin endpoint" | 🔴 **BUG: Retrieval miss** |

## 🐛 Bug Report

**BUG-01: Retrieval miss — Primary DB và Spin API endpoint**

- **Severity:** Medium
- **Expected:** Agent trả về `MySQL/PostgreSQL` và `POST /api/v1/lucky-wheel/{campaign_id}/spin`
- **Actual:** Agent báo "không tìm thấy trong tài liệu"
- **Root cause hypothesis:** Chunk chứa kiến trúc diagram và API endpoint listing trong Tech Doc v1 có thể bị split ra khỏi context hoặc retrieval score thấp hơn threshold khi chunk không chứa keyword match với question. Diagram ASCII art trong Confluence thường không embed text tốt.
- **Suggested fix:** Kiểm tra chunking strategy cho Tech Doc v1 — đặc biệt section `§1 Kiến trúc tổng quan` và `§6 API Endpoints`. Có thể cần tăng `topk` hoặc hạ `grade_threshold` cho technical queries.
