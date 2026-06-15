# UC06 — Meeting-to-Execution Auto-Agent

## Pain Points

- Sau meeting, action items thường bị ghi vào notes riêng của từng người — không có nơi tập trung, hay bị quên.
- Việc tạo task từ meeting notes là thủ công: copy từng dòng, assign, set deadline — mất 15–30 phút.
- Không có ai remind nếu task bị miss.
- Meeting recap gửi cho team/stakeholder cũng phải viết tay.

## Input

- Paste meeting notes hoặc transcript vào chat.
- Hoặc link đến Confluence page chứa meeting minutes.

## Agent Behavior

1. **Parse meeting notes** → extract:
   - Decisions (quyết định đã đưa ra).
   - Action items (ai làm gì, deadline bao giờ).
   - Open questions (chưa giải quyết, cần follow-up).
2. **Tạo Jira tasks** cho từng action item — với assignee, due date, link về context.
3. **Set reminder** — nếu deadline gần → agent nhắc lại qua email.
4. **Draft meeting recap email** → gửi cho participants hoặc team channel qua Mail.
5. Lưu notes + action items lên Confluence page tương ứng (nếu có).

## Triển Khai

| Bước | Việc cần làm | Dùng gì |
|---|---|---|
| 1 | Extraction node: parse notes → structured {decisions, actions, questions} | LangGraph + prompt |
| 2 | Jira node: tạo task per action item | Jira API (đã có) |
| 3 | Mail node: draft + send recap email | Mail |
| 4 | Confluence write node: lưu structured notes lên page | Confluence API (đã kết nối) |
| 5 | Reminder logic: nếu deadline < 24h → trigger email | Mail + scheduler |

**Tích hợp cần thêm:** Mail. Không cần tích hợp mới.

> **Hỏi thêm:** Meeting transcript hiện đang đến từ đâu — Zoom, Google Meet, hay chỉ notes tay? Nếu từ transcript tự động thì cần connector phù hợp.

## Lợi Ích Trực Tiếp

- Tiết kiệm 15–30 phút/meeting cho người ghi chú.
- 100% action item được tạo task và track — không bị rơi.
- Recap email ra ngay sau meeting, không phải ngồi viết lại.

## Giá Trị Khi Mở Rộng

- Tích hợp với lịch họp → agent tự nhận transcript từ Zoom/Google Meet.
- Trend analysis: team nào hay có meeting mà không ra action item → insight về process.
- Kết nối với UC02 (Ops Command Center) → action items từ meeting tự vào daily briefing.

## Nổi Bật Zalopay Wiki Agent

Use case này đóng vòng lặp: knowledge từ Confluence → trả lời câu hỏi (Q&A agent) → tạo task (Jira) → meeting output quay lại thành knowledge mới lên Confluence. Agent không chỉ đọc wiki mà còn **viết lại wiki** — biến nó thành living document, không phải tài liệu chết.

## High-Level System Design

```
[Input: meeting notes paste / Confluence page URL]
        │
        ▼
[Extraction Node]
        │
        ├──▶ Decisions list
        ├──▶ Action items [{owner, task, deadline}]
        └──▶ Open questions list
                │
                ▼
        [LangGraph Supervisor]
                │
                ├──▶ [Jira Node] ──────▶ create tasks (one per action item)
                ├──▶ [Mail Node] ───────▶ send recap to participants
                ├──▶ [Confluence Node] ─▶ save structured notes to page
                └──▶ [Reminder Node] ───▶ schedule follow-up email if deadline < 24h
```
