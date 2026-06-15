# UC02 — Campaign Precedent & Policy Q&A Agent

> "Campaign kiểu này mình đã từng làm chưa? Lần trước rule thế nào?"

## Bối Cảnh Thực Tế

Trong lúc review một campaign mới, Risk team thường gặp câu hỏi:

- *"Lucky Wheel nào trước đây có quà vé máy bay? Họ chặn payment method nào?"*
- *"Segment NPU/Churn đã dùng cho campaign nào? Có incident abuse không?"*
- *"Rule cap 3 lần/user/ngày có SOP gốc ở đâu? Ai approve lần trước?"*

Hiện tại: tự nhớ, hỏi đồng nghiệp, mò qua Jira cũ — mất thời gian và hay ra kết quả không nhất quán. Agent giải quyết bài toán này bằng cách trở thành **bộ nhớ institutional của đội Risk**.

## Agent Làm Gì

### Trả lời câu hỏi về policy
RAG qua Confluence (SOP, policy risk, checklist abuse chuẩn):
- "Rule nào áp dụng cho campaign có quà > 1 triệu VND?"
- "Khi nào thì bắt buộc chặn VietQR?"
- Trả về: câu trả lời + trích dẫn đúng tài liệu + link nguồn.

### Tìm precedent campaign tương tự
RAG qua lịch sử campaign đã được index (Confluence pages của các campaign cũ):
- "Lucky Wheel nào trước đây có cơ chế auto-trigger?"
- "Campaign nào dùng segment Churn + quà high-value?"
- Trả về: danh sách campaign tương tự + tóm tắt rule đã áp dụng + link tham chiếu.

### Giải thích lý do một rule cụ thể tồn tại
- "Tại sao rule X lại require exclude danh sách abuser?"
- Agent truy ngược lại SOP gốc và giải thích context.

## Ví Dụ Hội Thoại Thực Tế

```
Risk: "Mình đang review Lucky Wheel có quà resort 0đ.
       Trước đây có campaign nào tương tự không? Họ config rule gì?"

Agent: Tìm thấy 2 campaign tương tự:

  1. Lucky Wheel Q3/2024 — Quà resort Phú Quốc (Confluence: [link])
     → Chặn VietQR + Apple Pay
     → Cap 1 lần/user, exclude danh sách abuser Level 2
     → Không có incident abuse

  2. Lucky Wheel Tết 2024 — Quà vé máy bay + resort (Confluence: [link])
     → Chặn tất cả QR payment
     → Require hoàn thành 3 task trong 7 ngày
     → Ghi nhận 12 case abuse nhưng đã được chặn bởi rule

  Gợi ý cho campaign hiện tại: áp dụng config của Q3/2024 + thêm
  reward cap theo SOP section 3.2 [link].
```

## Tại Sao Đây Là UC Đúng Để Làm Sau UC01

UC01 và UC02 bổ sung cho nhau trong cùng một workflow:

| | UC01 | UC02 |
|---|---|---|
| **Trigger** | Có ticket campaign mới cần review | Có câu hỏi về policy hoặc precedent |
| **Input** | Jira key / Confluence URL | Câu hỏi tự nhiên |
| **Output** | Risk assessment + draft comment | Câu trả lời + citation + link precedent |
| **Stack** | Jira + Confluence + RAG | Confluence + RAG (đơn giản hơn) |

UC02 có thể dùng **độc lập** hoặc **trong lúc đang review UC01** — Risk team hỏi thêm để confirm rule trước khi approve draft comment.

---

## Đánh Giá Khả Thi Demo

### Những gì hệ thống đã có ✅

| Component | Trạng thái |
|---|---|
| RAG / OpenSearch | ✅ Đang chạy — đây là exact use case hệ thống được build cho |
| Confluence read + ingestion pipeline | ✅ Đã có — sync pages vào OpenSearch index |
| LangGraph retrieve → grade → synthesize | ✅ Đã có end-to-end |
| Chat UI với citation + source link | ✅ Đã có |
| Bilingual VI + EN | ✅ Đã có |

### Những gì còn thiếu ❌

| Component | Thiếu gì | Ước lượng |
|---|---|---|
| **Risk SOP docs trong OpenSearch** | Cần đội Risk sync Confluence space chứa SOP, checklist, policy vào index | ~0.5 ngày — chạy `make sync-confluence` với đúng space key |
| **Lịch sử campaign cũ** | Cần Confluence pages của các campaign đã chạy được index — nếu đang ở space khác thì cần thêm space key | ~0.5 ngày config + sync |
| **Prompt tuning** | Prompt mặc định tốt cho Q&A chung, cần fine-tune cho risk context (nhận diện "precedent", so sánh campaign) | ~1 ngày |

### Đây Là UC Demo Được Nhanh Nhất

**Không cần build thêm gì mới về code** — chỉ cần:
1. Có Confluence pages chứa SOP risk + lịch sử campaign.
2. Sync vào OpenSearch (chạy lệnh có sẵn).
3. Hỏi trong chat UI.

**Nếu có data ngay hôm nay → demo được trong 1 ngày.**

### Lộ Trình Demo (1–2 ngày)

**Ngày 1 sáng:** Xác định Confluence space nào chứa SOP risk + past campaign → add space key vào config → chạy `make sync-confluence`.

**Ngày 1 chiều:** Test một số câu hỏi thực tế, tune prompt nếu output chưa đúng format.

**Ngày 2 (nếu cần):** Tinh chỉnh prompt để output luôn có citation rõ + format precedent list thân thiện.

---

## High-Level System Design

```
[Input: câu hỏi tự nhiên về policy / precedent]
        │
        ▼
[LangGraph Supervisor] ──▶ route → risk department
        │
        ▼
[Retrieve Node] ──▶ OpenSearch                         ← ĐÃ CÓ
        │              ├── SOP / policy docs (Confluence)
        │              └── Past campaign pages (Confluence)
        ▼
[Grade Node] ──▶ lọc chunk liên quan                   ← ĐÃ CÓ
        │
        ▼
[Synthesize Node] ──▶ câu trả lời + citation           ← ĐÃ CÓ (tune prompt)
        │
        ▼
[Chat UI] ──▶ hiển thị answer + source links           ← ĐÃ CÓ

Data prep (one-time):
  Confluence spaces (SOP + past campaigns) ──▶ sync ──▶ OpenSearch index
```

## Giá Trị Khi Mở Rộng

- Kết hợp với UC01: trong lúc review campaign, hỏi precedent ngay trong cùng chat thread.
- Mở rộng sang các team khác: BD hỏi precedent deal, Legal hỏi precedent contract clause.
- Sau này index thêm Jira comments (decisions đã approve) → precedent càng phong phú hơn.
