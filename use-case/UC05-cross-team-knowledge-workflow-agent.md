# UC05 — Cross-Team Knowledge + Workflow Agent

## Pain Points

- Nhân viên mới hoặc team mới phải đọc hàng chục tài liệu rải rác trên Confluence để hiểu một quy trình.
- Khi cần onboard merchant mới hoặc bắt đầu một dự án liên team, không có nơi nào tổng hợp đủ thứ cần làm.
- Task được tạo thủ công, remider hay bị quên, không ai biết ai đang làm gì.
- Knowledge bị "mắc kẹt" trong đầu người — khi người nghỉ thì process mất theo.

## Input

- Lệnh tự nhiên: "Tạo onboarding checklist cho merchant mới ngành F&B."
- Hoặc: "Quy trình tích hợp API payment cho partner là gì?"

## Agent Behavior

1. **RAG qua Confluence** → tìm toàn bộ tài liệu liên quan đến quy trình được hỏi.
2. **Tổng hợp checklist/task list** từ nội dung đã retrieve — có thứ tự, có owner gợi ý.
3. **Tạo Jira tasks** tương ứng từ checklist — assign đúng team/người nếu có thông tin.
4. **Set reminder/due date** theo timeline gợi ý.
5. **Gửi email tóm tắt** checklist + link Jira cho stakeholder liên quan.
6. Khi được hỏi follow-up — agent query Jira để báo cáo tiến độ.

## Triển Khai

| Bước | Việc cần làm | Dùng gì |
|---|---|---|
| 1 | RAG node: full-text search qua Confluence theo process/topic | OpenSearch (đã có) |
| 2 | Checklist synthesis node: từ retrieved docs → structured task list | LangGraph + prompt |
| 3 | Jira node: bulk create tasks với due date, assignee | Jira API (đã có) |
| 4 | Mail node: gửi tóm tắt + link Jira | Mail |
| 5 | Progress query node: "task X đến đâu rồi?" → query Jira | Jira API |

**Tích hợp cần thêm:** Mail. Không cần tích hợp mới.

## Lợi Ích Trực Tiếp

- Onboarding mới giảm từ vài ngày xuống vài giờ.
- Không ai phải "hỏi lại từ đầu" — agent trả lời và tạo task luôn.
- Knowledge được externalize ra khỏi đầu người — bền vững hơn.

## Giá Trị Khi Mở Rộng

- Template library: lưu checklist đã tạo thành template tái dùng.
- Kết hợp với UC01 (Risk Review) — sau khi checklist risk xong thì agent tự tạo onboarding task.
- Mở rộng sang HR onboarding nhân viên mới.

## Nổi Bật Zalopay Wiki Agent

Use case này là **core value proposition của Zalopay Wiki Agent**: biến knowledge tĩnh trên Confluence thành workflow động. Không chỉ là Q&A — mà là "hỏi xong là có task để làm ngay." Đây là điểm khác biệt rõ ràng so với Confluence search thông thường.

## High-Level System Design

```
[Input: "Tạo onboarding checklist cho merchant X" / process query]
        │
        ▼
[LangGraph Supervisor]
        │
        └──▶ [RAG Node] ──▶ OpenSearch (Confluence: quy trình, SOP, policy)
                    │
                    ▼
        [Checklist Synthesis Node] → structured task list với owner + deadline
                    │
                    ├──▶ [Jira Node] → bulk create tasks
                    ├──▶ [Mail Node] → gửi tóm tắt cho stakeholder
                    └──▶ [Chat Response] → hiển thị checklist + citation

[Follow-up: "Tiến độ đến đâu?"]
        │
        └──▶ [Jira Query Node] → progress report
```
