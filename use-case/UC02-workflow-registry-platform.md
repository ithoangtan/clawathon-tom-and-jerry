# UC02 — Workflow Registry & Continuous Improvement Platform

> Không phải thêm tool. Là nền tảng để mọi workflow của Zalopay sống, chạy, và cải thiện liên tục.

---

## Vấn Đề Khi Có 100 Workflow

Khi số lượng workflow tăng lên — Risk review, CS ticket, onboarding merchant, process phát triển sản phẩm — xuất hiện 3 bài toán không thể giải bằng Confluence thông thường:

**1. Ai biết workflow nào tồn tại?**
Không có registry tập trung. Người mới không biết tìm đâu. Người cũ nhớ link cũ nhưng đã outdated.

**2. Ai đang dùng đúng version?**
Không có cơ chế enforce version. Team A đang dùng SOP v1, team B đã update lên v3, không ai biết.

**3. Workflow liên phòng ban thì ai quản?**
Ví dụ "Onboard merchant mới" cần: BD (ký hợp đồng) → Risk (KYC check) → Product Ops (setup config) → Ops (training). Không phòng ban nào làm chủ toàn bộ, không ai thấy full picture.

---

## Giải Pháp: Confluence Là Workflow Store, Agent Là Executor

**Nguyên tắc cốt lõi:**
> Workflow sống trong Confluence — không phải trong code của agent. Cải tiến workflow = edit Confluence page. Không cần deploy code.

### Thành phần 1: Workflow Registry (Confluence)

Một Confluence space hoặc label (`zalopay-workflow`) làm registry tập trung. Mỗi workflow là một page với template chuẩn:

```
## Workflow: [Tên]
Trigger: [khi nào dùng]
Owner: [team chịu trách nhiệm chính]
Participants:
  - Role: Risk Reviewer  → Department: Risk
  - Role: Deal Creator   → Department: BD
  - Role: Ops Executor   → Department: Product Ops
Version: [ngày] | Người cập nhật: [tên] | Status: [Draft/Active/Deprecated]

### Step 1: [Tên bước]
Responsible: [Role]
Input: [cần gì]
Action: [làm gì]
Output: [sản phẩm đầu ra]
Checklist:
  - [ ] Item A
  - [ ] Item B
Policy ref: [link tài liệu gốc]

### Step 2: ...
```

**Quản lý 100 workflow bằng label Confluence:**

| Label | Ý nghĩa |
|---|---|
| `zalopay-workflow` | Là một workflow (bắt buộc) |
| `domain:risk` | Workflow thuộc domain Risk |
| `domain:ops` | Workflow thuộc domain Ops |
| `domain:cs` | Workflow thuộc CS ticket |
| `status:active` | Đang dùng |
| `status:draft` | Đang draft, chưa active |
| `cross-team` | Liên quan nhiều phòng ban |

Agent chỉ execute workflow có `status:active`. Agent tìm workflow phù hợp bằng label + semantic search.

### Thành phần 2: Workflow Discovery (Agent)

Khi user đưa task vào:
```
User: "Tôi cần onboard merchant mới ngành F&B, bắt đầu từ đâu?"
  │
  └─▶ Agent tìm trong Registry → "Merchant Onboarding — Standard"
       → Hiển thị: tên workflow, version, owner, số steps
       → Hỏi: "Bạn muốn chạy workflow này không?"
```

### Thành phần 3: Workflow Execution (Agent)

Agent thực thi từng step:
- Biết ai responsible (Role/Department) → tạo Jira task assign đúng người.
- Biết cần data gì (Input) → fetch từ Jira, Confluence, MySQL.
- Biết checklist cần verify → present từng item để user tick.
- Biết policy ref ở đâu → RAG để trả lời câu hỏi trong step đó.

### Thành phần 4: Improvement Loop (Mọi Người Đều Có Thể)

```
[Agent chạy workflow]
    │
    ▼
[User: "Step 3 thiếu check VietQR QR code mới"]
    │
    ├─▶ Agent tạo draft edit lên Confluence page
    ├─▶ Gán reviewer (workflow owner)
    └─▶ Khi được approve → version mới active
         → Lần sau agent tự dùng version mới
```

**Không cần engineer để cải tiến workflow.** Risk team, CS team, BD team — ai cũng edit được trong Confluence.

---

## Ví Dụ Workflow Thực Tế Zalopay

| Workflow | Domain | Departments |
|---|---|---|
| Campaign Risk Review — Lucky Wheel | Risk | Risk, Biz, Product Ops |
| Campaign Risk Review — Cashback | Risk | Risk, Biz, Product Ops |
| Merchant Onboarding — Standard | Ops | BD, Risk, Legal, Product Ops |
| CS Ticket — Hoàn tiền thất bại | CS | CS, Ops, Finance |
| CS Ticket — Tài khoản bị khóa | CS | CS, Risk, Compliance |
| New Bank Partnership — Due Diligence | BD | BD, Risk, Legal, Finance |
| Production Incident — P1 Response | Engineering | Eng, Ops, Risk |
| Product Feature — Risk Sign-off | Product | Product, Risk, Legal |

Mỗi cái là 1 Confluence page. Agent có thể execute bất kỳ cái nào.

---

## Đây Là Điều Zalopay Wiki Agent Cần Để Không Bị Lỗi Thời

Hầu hết internal knowledge tool sau 6 tháng sẽ bị outdated vì:
- Docs cũ, không ai update.
- Người dùng mất tin tưởng.
- Tool bị bỏ.

**Workflow Registry giải quyết vòng đời này:**

```
Người dùng thấy thiếu/sai
    → Edit Confluence (quen rồi, không cần học tool mới)
    → Agent dùng version mới
    → Output tốt hơn
    → Người dùng tin tưởng hơn
    → Lại contribute thêm
```

Confluence là nguồn truth duy nhất — agent chỉ là executor.

---

## Đánh Giá Khả Thi Demo

### ✅ Đã có trong codebase

| Component | Chi tiết |
|---|---|
| RAG / OpenSearch | Retrieve + grade + synthesize — đây là exact core capability |
| Confluence ingestion | Sync pages vào OpenSearch, giữ labels trong metadata |
| Doc type phân loại | Ingestion nhận diện "sop/playbook" → type `Operation` — workflow map vào đây |
| Label indexing | `serialize_labels()` trong metadata.py — labels đã được lưu per chunk |
| Chat UI | Hiển thị answer + citation + source link |

### ❌ Còn thiếu — cần build

| Component | Cụ thể cần làm | Ước lượng |
|---|---|---|
| **Workflow template** | Viết template Confluence page chuẩn + 3–5 workflow mẫu lên Confluence | **1 ngày** (nội dung, không code) |
| **Workflow discovery node** | Query OpenSearch filter `label=zalopay-workflow AND status=active` + semantic match tên workflow | **1 ngày** |
| **Workflow parser** | Đọc Confluence page → parse steps (heading H3 = step, checklist items, responsible role) | **1 ngày** |
| **Workflow executor node** | LangGraph node: iterate steps → per-step RAG + action (Jira, Mail) | **2 ngày** |
| **Jira task creator** | Tạo Jira task per step, assign đúng responsible role | **1 ngày** |

**Tổng MVP: ~5–6 ngày để demo end-to-end với 1 workflow thật.**

### ⚡ Phiên bản demo tối giản (2 ngày)

1. **Ngày 1:** Tạo 1 workflow page trên Confluence (Campaign Risk Review). Sync vào OpenSearch.
2. **Ngày 2:** Agent fetch workflow page → parse steps → hiển thị từng step trong chat → user tick checklist.

Không cần Jira, không cần executor phức tạp. Chỉ cần show: "agent đọc workflow từ Confluence và guide user đi từng bước."

---

## High-Level System Design

```
                    ┌─────────────────────────────────────┐
                    │       CONFLUENCE WORKFLOW REGISTRY  │
                    │  (label: zalopay-workflow)          │
                    │                                     │
                    │  • Campaign Risk Review — LW  v3.1 │
                    │  • Merchant Onboarding — Std  v2.0 │
                    │  • CS Ticket — Hoàn tiền      v1.5 │
                    │  • ... (100+ workflows)            │
                    └──────────────┬──────────────────────┘
                                   │ sync (daily / on-demand)
                                   ▼
                    ┌─────────────────────────────────────┐
                    │         OpenSearch Index            │
                    │  (doc_type=Operation, labels,       │
                    │   chunked steps, policy refs)       │
                    └──────────────┬──────────────────────┘
                                   │
[User: "Review ZP-12345"]          │
        │                          │
        ▼                          ▼
┌───────────────────────────────────────────┐
│            LangGraph Agent                │
│                                           │
│  [Discovery Node]                         │
│    → tìm workflow phù hợp                │
│    → confirm với user                     │
│                                           │
│  [Executor Node] — iterate steps          │
│    Step N:                                │
│      → [RAG Node] policy + precedent      │
│      → [Data Node] Jira / MySQL           │
│      → present checklist to user         │
│      → [Action Node] tạo Jira task       │
│                                           │
│  [Synthesis Node]                         │
│    → structured output per workflow       │
└───────────────────────────────────────────┘
        │
        ▼
[User review → approve → Jira comment / Mail]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPROVEMENT LOOP (không cần code deploy):

  User thấy thiếu bước
    → Edit Confluence page
    → Ingestion sync lại (tự động / manual)
    → Agent dùng version mới ngay
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Mối Quan Hệ UC01 ↔ UC02

```
UC02 = Platform (Workflow Registry + Executor)
UC01 = Use case đầu tiên chạy trên platform đó

UC01 là bằng chứng UC02 hoạt động.
UC02 là lý do UC01 scale được.
```

Demo sequence tốt nhất:
1. Show UC02: "Đây là registry, có 5 workflow mẫu, ai cũng edit được."
2. Show UC01: "Agent thực thi đúng workflow Campaign Risk Review — không cứng code."
3. Live edit workflow page → chạy lại → output khác → "Đây là continuous improvement."
