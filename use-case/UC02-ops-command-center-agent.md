# UC02 — Ops Command Center Agent

## Pain Points

- Đội Ops mỗi sáng phải mở 4–5 tab (Jira, dashboard, email, chat) để nắm được tình hình: ticket nào đang chờ, KPI hôm qua thế nào, incident nào chưa đóng.
- Không có nơi tổng hợp — mỗi người tự tổng hợp theo cách riêng, thông tin hay bị trễ hoặc bỏ sót.
- Khi cần action (gán ticket, gửi update) phải nhảy qua lại nhiều tool.

## Input

- Không cần input phức tạp: agent chạy theo lịch (sáng / chiều) hoặc theo lệnh "Tổng hợp tình hình hôm nay."
- Hoặc query cụ thể: "Ticket nào của tôi đang quá hạn?"

## Agent Behavior

1. **Pull dữ liệu song song:**
   - Jira: ticket đang open / overdue / assigned to me.
   - Confluence: runbook / playbook liên quan đến issue đang có.
   - MySQL: KPI ops hôm qua (transaction volume, error rate).
2. **Tổng hợp bản Daily Ops Briefing** — bullet list ưu tiên, phân loại: 🔴 cần xử lý ngay / 🟡 cần theo dõi / 🟢 on-track.
3. **Đề xuất action** có thể click-to-execute:
   - "Assign ticket JIRA-123 cho team A" → gọi Jira API.
   - "Gửi update tình hình cho manager" → soạn draft Mail.
4. Nếu có incident đang mở → gợi ý bước xử lý từ runbook (RAG qua Confluence).

## Triển Khai

| Bước | Việc cần làm | Dùng gì |
|---|---|---|
| 1 | Jira query node: fetch ticket by assignee/status/priority | Jira API (đã có) |
| 2 | MySQL query node: pull KPI metrics | MySQL (đã có) |
| 3 | RAG node: match incident → runbook từ Confluence | OpenSearch (đã có) |
| 4 | Synthesis node: tổng hợp briefing | LangGraph + prompt |
| 5 | Action nodes: update Jira, draft Mail | Jira API + Mail |

**Tích hợp cần thêm:** Mail. Không cần tích hợp mới ngoài Mail.

## Lợi Ích Trực Tiếp

- Tiết kiệm 20–30 phút/ngày/người cho daily sync.
- Không bỏ sót ticket overdue hoặc incident chưa đóng.
- Ops lead có cái nhìn tổng thể real-time thay vì chờ báo cáo thủ công.

## Giá Trị Khi Mở Rộng

- Tích hợp thêm alerting: khi KPI vượt ngưỡng → agent tự tạo incident ticket + ping đúng người.
- Mở rộng cho nhiều team Ops khác nhau với briefing template riêng.
- Dashboard tổng hợp lịch sử briefing để tracking trend.

## Nổi Bật Zalopay Wiki Agent

Use case này chứng minh agent không chỉ "trả lời câu hỏi" mà còn **chủ động tổng hợp và thực thi**. RAG được dùng để match incident với runbook — đây là điểm mà search thông thường không làm được (phải hiểu ngữ cảnh incident để tìm đúng playbook).

## High-Level System Design

```
[Trigger: schedule/user command]
        │
        ▼
[LangGraph Supervisor]
        │
        ├──▶ [Jira Node] ──────────▶ tickets (open, overdue, mine)
        ├──▶ [MySQL Node] ─────────▶ KPI metrics
        └──▶ [RAG Node] ───────────▶ OpenSearch (runbooks, playbooks)
                │
                ▼
        [Synthesis Node] → Daily Briefing (prioritized, cited)
                │
                ├──▶ [Action: Jira update]
                └──▶ [Action: Mail draft → send]
```
