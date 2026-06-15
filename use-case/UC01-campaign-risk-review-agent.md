# UC01 — Campaign Risk Review Agent (Workflow-Driven)

> Agent không "đoán" SOP — agent **đọc đúng workflow** từ Confluence, thực thi từng bước, cite rõ nguồn.

---

## Vấn Đề Gốc Rễ

**Biz team** tạo Jira ticket/epic cho campaign mới, đính kèm Confluence page chứa:
- Format campaign (Lucky Wheel / hoàn tiền / coupon…), T&C, danh sách quà
- Segment ID, trigger/event, task list, điều kiện phát quà

**Risk team** phải:
1. Đọc Confluence (dài, nhiều chi tiết nhỏ).
2. Áp từng mục trong SOP risk review vào campaign — thủ công, không có template nhất quán.
3. Đề xuất rule & endpoint cho Product Ops.
4. Viết comment lên Jira.

**Pain:** Mỗi người áp SOP theo cách khác nhau → output không đồng nhất → dễ bỏ sót → abuse xảy ra.

---

## Giải Pháp Cốt Lõi: Workflow-Driven Execution

Thay vì SOP là tài liệu thụ động, agent **đọc workflow từ Confluence và thực thi từng bước**.

```
Workflow page trên Confluence
  → Agent fetch + parse step-by-step
  → Thực thi: kéo data, RAG, đánh giá, gợi ý rule
  → Draft comment đã structured, có citation
  → Risk team review → approve → post Jira
```

**Kết quả:** Mọi campaign review đều đi qua đúng bộ bước. Khi SOP thay đổi, chỉ cần edit Confluence page — agent tự dùng version mới lần sau. Không cần deploy code.

---

## Workflow Page Template (Lưu Trên Confluence)

Mỗi workflow là một Confluence page có nhãn `zalopay-workflow` và cấu trúc chuẩn:

```markdown
## Workflow: Campaign Risk Review — Lucky Wheel
**Trigger:** Khi có Jira ticket campaign Lucky Wheel cần review
**Owner:** Risk Team
**Tham gia:** Risk (lead) · Biz (cung cấp data) · Product Ops (thực thi rule)
**Version:** 2024-06-01 | Người sửa cuối: [tên]

---

### Step 1: Tóm tắt campaign
- **Data cần lấy:** format, quà, segment, trigger, điều kiện tham gia
- **Nguồn:** Confluence page đính kèm ticket

### Step 2: Kiểm tra payment method risk
- **Checklist:**
  - [ ] Có chặn VietQR không? (bắt buộc nếu quà > 500K)
  - [ ] Có chặn Apple Pay không?
  - [ ] Có chặn direct card không?
- **Policy tham chiếu:** [link SOP Payment Risk v3]

### Step 3: Kiểm tra segment & abuse risk
- **Checklist:**
  - [ ] Segment có include "Starter" account không?
  - [ ] Có danh sách malicious abuser để exclude?
  - [ ] Cap reward: tối đa X lần/user/ngày?
- **Policy tham chiếu:** [link SOP Segment Risk v2]

### Step 4: Đánh giá reward value
- **Rule:** Quà > 1 triệu VND → escalate lên Head of Risk trước khi approve
- **Policy tham chiếu:** [link High-Value Reward Policy]

### Step 5: Tổng hợp & draft comment
- **Output:** Risk summary + danh sách rule gợi ý + risk level (Low/Med/High)
```

Agent đọc page này → thực thi từng step → output structured theo đúng template.

---

## Luồng Sử Dụng

### Flow A — Risk team gọi agent
```
Risk: "Review ZP-12345 theo workflow Lucky Wheel"
  │
  ├─ [1] Agent fetch Jira ZP-12345 → lấy summary + link Confluence
  ├─ [2] Agent fetch Confluence page campaign → parse nội dung
  ├─ [3] Agent tìm workflow phù hợp trong Registry → "Campaign Risk Review — Lucky Wheel"
  ├─ [4] Agent thực thi từng step trong workflow:
  │       Step 1: tóm tắt campaign từ Confluence data
  │       Step 2: check payment method → flag VietQR chưa được chặn
  │       Step 3: check segment → phát hiện Starter account chưa exclude
  │       Step 4: reward value = vé máy bay 0đ → flag High, cần escalate
  │       Step 5: tổng hợp → draft comment
  └─ [5] Hiển thị draft comment trong chat

Risk: "OK, post lên Jira"
  └─ Agent POST comment vào ZP-12345
```

### Flow B — Agent tự động (nâng cấp sau)
Jira webhook khi ticket mới tạo → agent chạy workflow → gửi draft qua Mail cho Risk team duyệt.

---

## Đánh Giá Khả Thi Demo

### ✅ Đã có trong codebase

| Component | Chi tiết |
|---|---|
| RAG / OpenSearch | Retrieve → grade → synthesize hoàn chỉnh |
| Confluence read | `ConfluenceClient` có `get_page_content()` — fetch bất kỳ page nào bằng URL |
| Doc type classifier | Ingestion tự nhận diện "sop/playbook/operating procedure" → type `Operation` |
| Label + metadata indexing | Confluence labels được index → có thể filter `zalopay-workflow` |
| LangGraph nodes | Có thể thêm node mới mà không refactor toàn bộ graph |
| Chat UI + citation | Source link hiển thị sẵn trong response |

### ❌ Còn thiếu — cần build

| Component | Cụ thể cần làm | Ước lượng |
|---|---|---|
| **Jira client (read)** | Gọi `GET /rest/api/3/issue/{key}`, parse description + Confluence URL | **1 ngày** |
| **Jira comment writer** | `POST /rest/api/3/issue/{key}/comment` | **0.5 ngày** |
| **Workflow executor node** | LangGraph node: fetch workflow page → parse steps → thực thi tuần tự | **1.5 ngày** |
| **Workflow template** | Viết 1–2 workflow page mẫu lên Confluence (nội dung, không phải code) | **0.5 ngày** |
| **Risk SOP docs** | Cần đội Risk đưa SOP lên Confluence → sync vào OpenSearch | **0.5 ngày prep** |

**Tổng: ~4 ngày để demo Flow A hoàn chỉnh.**

### ⚡ Phiên bản demo tối giản (1.5 ngày)
- Bỏ qua Jira: user paste Confluence URL trực tiếp.
- Bỏ qua workflow executor: dùng RAG thường + prompt template cứng.
- Output: risk assessment trong chat, không post Jira.
- Đủ để show concept và lấy feedback từ Risk team.

---

## High-Level System Design

```
[Input: "Review ZP-12345"]
        │
        ▼
┌──────────────────┐
│   Jira Node      │ ← CẦN BUILD
│ fetch ticket     │ → summary + Confluence URL
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Confluence Node  │ ← ĐÃ CÓ (wire vào)
│ fetch campaign   │ → full T&C + quà + segment
│ page content     │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────┐
│   Workflow Registry Node     │ ← CẦN BUILD
│ tìm workflow phù hợp         │ → parse steps từ Confluence
│ (label: zalopay-workflow)    │
└────────┬─────────────────────┘
         │
         ▼  (thực thi từng step)
┌──────────────────┐
│   RAG Node       │ ← ĐÃ CÓ
│ per-step context │ → SOP, policy, precedent
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Synthesis Node   │ ← ĐÃ CÓ (tune prompt)
│ risk summary     │ → structured draft comment
│ + rule gợi ý     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Jira Comment     │ ← CẦN BUILD
│ Node             │ → POST comment khi user approve
└──────────────────┘
```

---

## Lợi Ích & Khác Biệt

| | Không có agent | Có agent |
|---|---|---|
| Thời gian review | 30–60 phút/ticket | 5–10 phút |
| Đồng nhất | Phụ thuộc người | 100% theo workflow |
| Audit trail | Ghi tay vào comment | Tự động, có citation |
| Cải tiến SOP | Cần training lại | Chỉ cần edit Confluence page |
| Scale | Tắc nghẽn theo người | Không giới hạn |
