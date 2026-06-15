# UC04 — Partnership Deal Desk Agent

## Pain Points

- Mỗi deal với bank/merchant mới đòi hỏi soạn thảo term sheet, theo dõi trạng thái hợp đồng, pull KPI hiệu suất — mỗi việc ở một tool khác nhau.
- Business Dev hay mất thời gian tìm lại template cũ, sửa thủ công cho từng đối tác.
- Thiếu visibility: không rõ deal đang ở bước nào, ai đang hold, deadline bao giờ.
- Draft email/báo cáo cho internal cũng tốn nhiều thời gian.

## Input

- Mô tả deal: tên đối tác, loại hợp tác, điều khoản chính, timeline.
- Hoặc query: "Tình trạng deal với Bank Y hiện tại?"

## Agent Behavior

1. **Generate term sheet draft** — RAG qua Confluence (template cũ, policy ký kết) → sinh ra term sheet phù hợp với loại đối tác.
2. **Track contract status** — query Jira (các task liên quan đến deal) + tổng hợp vào timeline.
3. **Pull KPI** từ MySQL: volume giao dịch, revenue, error rate của đối tác hiện có.
4. **Draft email/báo cáo** — soạn email update cho internal stakeholder hoặc đối tác qua Mail.
5. Nếu deal có rủi ro (deadline gần, task overdue) → cảnh báo và đề xuất action.

## Triển Khai

| Bước | Việc cần làm | Dùng gì |
|---|---|---|
| 1 | RAG node: template term sheet, policy ký kết từ Confluence | OpenSearch (đã có) |
| 2 | Jira node: query task/status theo deal label | Jira API (đã có) |
| 3 | MySQL node: KPI đối tác (volume, revenue) | MySQL (đã có) |
| 4 | Document generation node: sinh term sheet draft | LangGraph + prompt |
| 5 | Mail node: draft + send email update | Mail |

**Tích hợp cần thêm:** Mail. Không cần tích hợp mới.

> **Hỏi thêm:** Hiện tại term sheet/contract đang lưu ở đâu — Confluence hay Google Drive? Để biết cần index thêm nguồn nào.

## Lợi Ích Trực Tiếp

- Giảm 60% thời gian soạn thảo term sheet.
- BD team có visibility 360° về deal chỉ bằng một câu hỏi.
- Không bỏ sót deadline hoặc task chưa assign.

## Giá Trị Khi Mở Rộng

- Thêm e-signature workflow khi hợp đồng được approve.
- Tạo dashboard deal pipeline tự động từ Jira + MySQL.
- Mở rộng sang merchant onboarding: agent tự tạo onboarding checklist, gửi link, track tiến độ.

## Nổi Bật Zalopay Wiki Agent

Đây là use case **thể hiện rõ nhất khả năng kết hợp RAG + action**. Agent không chỉ search tài liệu mà còn tổng hợp cross-source (Confluence docs + Jira tasks + MySQL KPI) và tạo ra output actionable (term sheet, email). Rất phù hợp demo cho ban lãnh đạo BD.

## High-Level System Design

```
[Input: deal description / partner name / query]
        │
        ▼
[LangGraph Supervisor]
        │
        ├──▶ [RAG Node] ───────────▶ Confluence (templates, policy ký kết)
        ├──▶ [Jira Node] ──────────▶ tasks, status, timeline của deal
        └──▶ [MySQL Node] ─────────▶ KPI đối tác (volume, revenue)
                │
                ▼
        [Synthesis Node]
                │
                ├──▶ [Doc Gen Node] → Term sheet draft (Markdown / plain text)
                └──▶ [Mail Node] → email update cho stakeholder / đối tác
```
