# Solution Design: Multi-Workflow Agent Platform

> Nền tảng để agent có thể hiểu, thực thi, và cải tiến bất kỳ workflow nào của Zalopay — không cần code thêm mỗi khi có workflow mới.

---

## Nguyên Tắc Thiết Kế

1. **Workflow sống trong Confluence, không phải trong code.** Thêm/sửa/xóa workflow = edit Confluence page. Không deploy lại agent.
2. **Agent là executor chung.** Một engine duy nhất đọc được mọi loại workflow, không phải một agent riêng cho mỗi use case.
3. **Cải tiến mở cho mọi người.** Bất kỳ ai có quyền edit Confluence đều có thể cải thiện workflow — không cần qua engineering.
4. **Workflow cross-department.** Mỗi bước có responsible role rõ ràng, không bị siloed theo phòng ban.

---

## Kiến Trúc Tổng Quan

```
┌────────────────────────────────────────────────────────────┐
│                  CONFLUENCE (space: Workflow)               │
│                                                            │
│  Page: Campaign Risk Review — Lucky Wheel  [label: active] │
│  Page: Merchant Onboarding — Standard      [label: active] │
│  Page: CS Ticket — Hoàn tiền thất bại      [label: active] │
│  Page: ...                                 [label: draft]  │
└──────────────────────────┬─────────────────────────────────┘
                           │ ingestion sync (existing pipeline)
                           ▼
┌────────────────────────────────────────────────────────────┐
│                    OpenSearch Index                         │
│  doc_type=Operation, label=zalopay-workflow, space=Workflow │
│  (chunked by step — mỗi step là 1 chunk riêng)            │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│                  Agent — 3 tầng xử lý                      │
│                                                            │
│  [1] DISCOVERY  — tìm đúng workflow cho task              │
│  [2] EXECUTION  — thực thi từng step                      │
│  [3] ACTION     — tạo Jira task, post comment, gửi mail   │
└────────────────────────────────────────────────────────────┘
```

---

## Tầng 1: Workflow Page Template (Confluence)

Mọi workflow đều tuân theo cấu trúc heading chuẩn để agent parse được. Không dùng format đặc biệt — chỉ là Confluence page bình thường với headings nhất quán.

### 1a. Metadata Header (bắt buộc)

```
# [Tên workflow]

| Field            | Value                                             |
|------------------|---------------------------------------------------|
| Trigger          | Khi nào dùng workflow này                         |
| Owner            | Team chịu trách nhiệm chính                       |
| Participants     | Risk Reviewer · Biz Creator · Product Ops         |
| Definition Status| IN DEV                                            |
| Jira Source      | existing-ticket                                   |
| Version          | 2024-06-15 · Người sửa: [tên]                    |
```

### 1b. Instance Lifecycle (mỗi workflow tự define)

```
## Lifecycle

| Status         | Ý nghĩa                              | Bước tiếp theo      |
|----------------|--------------------------------------|---------------------|
| SUBMITTED      | Ticket mới được tạo / gán vào        | → UNDER REVIEW      |
| UNDER REVIEW   | Đang trong quá trình review          | → APPROVED / REJECTED / ESCALATED |
| ESCALATED      | Cần cấp cao hơn quyết định           | → APPROVED / REJECTED |
| APPROVED       | Đã duyệt, chờ thực thi              | → DONE              |
| REJECTED       | Không pass review                    | (terminal)          |
| DONE           | Hoàn thành toàn bộ                   | (terminal)          |

Executable statuses: SUBMITTED, UNDER REVIEW, ESCALATED
```

Agent đọc bảng này từ Confluence — không hardcode bất kỳ status nào trong code. Mỗi workflow có bảng lifecycle riêng, có thể khác nhau hoàn toàn.

Ví dụ workflow **Merchant Onboarding** có lifecycle khác hẳn:
```
INITIATED → KYC CHECK → CONTRACT SIGNED → CONFIG SETUP → TRAINING → LIVE → DONE
```

Ví dụ workflow **CS Ticket** đơn giản hơn:
```
OPEN → IN PROGRESS → RESOLVED / ESCALATED
```

### 1c. Jira Source — Define Per Workflow

```
| Jira Source | existing-ticket |   ← user cung cấp ticket key khi gọi agent
| Jira Source | auto-create     |   ← agent tự tạo Jira epic khi workflow bắt đầu
```

**`existing-ticket`:** Dùng khi workflow được trigger từ ticket đã có sẵn (VD: Biz team tạo ZP-12345 rồi mới gọi Risk review).
Agent yêu cầu user cung cấp Jira key → gắn mọi sub-task vào ticket đó.

**`auto-create`:** Dùng khi workflow là điểm khởi đầu của một case mới (VD: "Onboard merchant ABC Company").
Agent tạo Jira epic mới → điền summary, description, assignee → rồi tạo sub-tasks theo từng step.

### 1d. Step Definition (H2 heading = 1 step)

```
## Step 1: [Tên bước]

**Responsible:** [Role — Department]
**Type:** fetch | rag | checklist | synthesize | action | gate
**Input:** [Dữ liệu/thông tin cần có]
**Action:** [Làm gì cụ thể]
**Output:** [Sản phẩm đầu ra]

Checklist:
- [ ] Item A
- [ ] Item B

> **Policy ref:** [link SOP gốc]

---

## Step 2: ...
```

**Labels bắt buộc trên Confluence page:**
- `zalopay-workflow` — để agent biết đây là workflow, không phải doc thường
- `domain:risk` / `domain:ops` / `domain:cs` / `domain:bd` — để filter nhanh theo domain

---

## Tầng 2: Workflow Discovery

Khi user đưa task vào, agent tìm workflow phù hợp theo 2 cách:

### Cách A — User chỉ định tên
```
"Chạy workflow Campaign Risk Review cho ticket ZP-12345"
  → Agent load đúng workflow đó, không cần tìm kiếm
```

### Cách B — Agent tự tìm (semantic search)
```
"Review campaign Lucky Wheel mới, quà vé máy bay"
  → Agent query OpenSearch:
      filter: label=zalopay-workflow AND label=status:active
      semantic: "campaign lucky wheel risk review"
  → Trả về top 3 workflow matches + score
  → Confirm với user trước khi execute
```

**Output của Discovery:**
```
Tìm thấy workflow phù hợp:

1. Campaign Risk Review — Lucky Wheel (v3.1, cập nhật 2024-06-01)
   Owner: Risk Team | 5 steps | ~10 phút
   → [Chạy workflow này]

2. Campaign Risk Review — General (v2.0)
   → [Xem chi tiết]
```

---

## Tầng 3: Workflow Execution Engine

Agent đọc workflow page → thực thi từng step theo thứ tự. Mỗi step có thể:

### Step types

| Type | Mô tả | Agent làm gì |
|---|---|---|
| **fetch** | Lấy dữ liệu từ nguồn ngoài | Gọi Jira API, Confluence API, MySQL |
| **rag** | Tra cứu policy/precedent | Query OpenSearch, trả kết quả có citation |
| **checklist** | User tự xác nhận | Present danh sách, chờ user tick |
| **synthesize** | Tổng hợp → output | LLM tổng hợp context → draft text |
| **action** | Thực thi hành động | Post Jira comment, tạo task, gửi mail |
| **gate** | Điều kiện phân nhánh | Nếu [condition] → skip step X / escalate |

### Ví dụ execution flow (Campaign Risk Review)

```
Step 1 [fetch]     → Kéo Jira ticket + Confluence campaign page
Step 2 [synthesize]→ Tóm tắt campaign theo template
Step 3 [rag]       → RAG: policy payment method, checklist abuse
Step 4 [checklist] → User tick: VietQR chặn chưa? Starter exclude chưa?
Step 5 [gate]      → Nếu quà > 1 triệu → escalate Head of Risk
Step 6 [synthesize]→ Tổng hợp risk assessment + rule gợi ý
Step 7 [action]    → Draft Jira comment → user approve → post
```

### Cross-department routing — Jira Task

Mỗi step có `Responsible: [Role — Department]`. Khi đến step của department khác, agent **tạo Jira sub-task** assign đúng người, không chỉ notify.

```
Workflow: Merchant Onboarding — Standard

Step 1 [BD]       → Agent assign BD lead → Jira sub-task: "Ký hợp đồng"
Step 2 [Risk]     → Agent assign Risk team → Jira sub-task: "KYC check"
Step 3 [Product Ops] → Agent assign Ops → Jira sub-task: "Setup config"
Step 4 [Ops]      → Agent assign Ops → Jira sub-task: "Training merchant"
```

Jira parent ticket = workflow instance (ví dụ: "Onboard Merchant ABC").
Jira sub-tasks = từng step với đúng assignee và deadline.

Người nhận sub-task xử lý xong → mark Done trên Jira → agent nhận signal → chạy step tiếp theo.
Không cần mọi người vào cùng một chat thread — ai làm step của mình trên Jira như bình thường.

---

## Tầng 4: Improvement Loop

```
Người dùng: "Step 3 thiếu check QR code type mới"
  │
  └─▶ 2 lựa chọn:

  Option A (tự edit):
    Người dùng mở Confluence page → sửa trực tiếp
    Ingestion sync tự động (hoặc manual: make sync-confluence)
    Agent dùng version mới ngay lần sau

  Option B (qua agent — sau này):
    "Thêm checklist item này vào Step 3 giúp mình"
    Agent tạo draft edit → gửi cho workflow owner approve
    Khi approve → Confluence page được cập nhật
```

**Version tracking hoàn toàn miễn phí** — Confluence giữ lịch sử mọi edit, ai sửa gì, khi nào.

---

## Quản Lý 100+ Workflow Không Bị Loạn

### Quy tắc đặt tên
```
[Domain]: [Object] — [Variant/Scope]

Risk: Campaign Review — Lucky Wheel
Risk: Campaign Review — Cashback
Risk: Campaign Review — General
Ops: Merchant Onboarding — Standard
Ops: Merchant Onboarding — Enterprise
CS: Ticket — Hoàn tiền thất bại
CS: Ticket — Tài khoản bị khóa
BD: Partnership — New Bank Due Diligence
Eng: Incident Response — P1
```

### Label taxonomy (filter nhanh)
```
zalopay-workflow          (bắt buộc)
status:active / draft / deprecated
domain:risk / ops / cs / bd / eng / product
scope:internal / cross-team
trigger:jira / manual / scheduled
```

### Workflow definition lifecycle (của bản thân SOP/template)

Đây là status của **workflow page** — không phải của từng case chạy qua workflow đó.

```
NEW → IN DEV → IN PROCESS → DONE
```

- `NEW`: Vừa tạo, chưa có nội dung.
- `IN DEV`: Đang draft, đang review, chưa dùng chính thức.
- `IN PROCESS`: Template đã approve, agent được phép execute.
- `DONE`: Workflow đã deprecated hoặc thay thế bởi version mới.

Agent chỉ execute workflow có `Definition Status = IN PROCESS`. Các status khác: agent có thể search/hiển thị thông tin nhưng không execute.

### Workflow instance lifecycle (của từng case cụ thể)

Mỗi workflow **tự define** instance lifecycle trong section `## Lifecycle` trên Confluence page. Agent đọc bảng đó để biết:
- Status nào là valid.
- Transition nào được phép.
- Status nào là terminal (không có bước tiếp theo).
- Status nào agent được phép tự động chuyển vs. phải chờ user confirm.

Không có lifecycle chung — mỗi workflow có thể phức tạp theo đúng nhu cầu thực tế của nó.

---

## Những Gì Cần Build (Xếp Theo Thứ Tự)

| # | Component | Mô tả | Effort |
|---|---|---|---|
| 1 | **Workflow template** | Tài liệu template + 1–2 workflow mẫu lên Confluence space `Workflow` | Nội dung, không code |
| 2 | **Sync config** | Add space `Workflow` vào `CONFLUENCE_SPACES` trong `.env` | 30 phút |
| 3 | **Workflow Discovery Node** | Query OpenSearch filter `zalopay-workflow + status:active` + semantic match | 1 ngày |
| 4 | **Workflow Parser** | Đọc Confluence page → extract steps từ H2 headings, checklist items, responsible, policy refs | 1 ngày |
| 5 | **Workflow Executor Node** | LangGraph node: iterate steps → dispatch theo step type (fetch/rag/checklist/action) | 2 ngày |
| 6 | **Jira Node** | Read ticket + write comment | 1.5 ngày |
| 7 | **Cross-dept routing** | Step có responsible role khác → tạo Jira task / gửi notification | 1 ngày |

**Tổng để có platform chạy được với 1 workflow thật: ~7 ngày.**
**Phiên bản đủ để demo nội bộ (chỉ #1–4 + chat UI): ~2 ngày sau khi có workflow content.**

---

## Không Trong Scope

- Workflow builder UI (drag-and-drop) — Confluence editor là đủ.
- Workflow versioning system riêng — Confluence page history là đủ.
- Role-based access control per workflow — dùng Confluence page permissions.
- Workflow analytics dashboard — để sau.
