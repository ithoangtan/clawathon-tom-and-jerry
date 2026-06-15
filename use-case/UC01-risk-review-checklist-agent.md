# UC01 — Risk Review Checklist Agent for New Bank/Partner Products

## Pain Points

- Đội Risk/Compliance phải kiểm tra từng sản phẩm/đối tác mới theo nhiều bộ tiêu chí (KYC, AML, giới hạn giao dịch, báo cáo định kỳ).
- Quy trình hiện tại: copy-paste điều khoản từ nhiều tài liệu, check thủ công, gửi email checklist qua lại — tốn thời gian và dễ sót.
- Thiếu chuẩn hóa: mỗi người áp dụng policy theo cách khác nhau, không đồng nhất giữa các deal.

## Input

Mô tả ngắn về sản phẩm hoặc đối tác mới, ví dụ:
> "BNPL product with Bank X for online merchants, transaction limit 5M VND."

## Agent Behavior

1. **RAG qua** risk policy docs, KYC/AML guidelines, previous risk review records (Confluence) → sinh ra:
   - Checklist kiểm tra rủi ro (KYC tier, giới hạn giao dịch, monitoring rule, báo cáo NHNN).
   - Danh sách câu hỏi gửi cho partner/bank để clarify.
2. **Log checklist** vào Jira (task + subtask cho từng mục cần confirm).
3. **Draft email** tóm tắt gửi Risk Committee hoặc đối tác (thay Teams/Outlook bằng Mail).
4. Khi checklist hoàn thành → agent tổng hợp kết quả, đề xuất Approve / Conditional Approve / Reject.

## Triển Khai

| Bước | Việc cần làm | Dùng gì |
|---|---|---|
| 1 | Index toàn bộ risk policy, KYC/AML doc lên OpenSearch | Ingestion pipeline (đã có) |
| 2 | Prompt template: "Sinh checklist từ mô tả + retrieved docs" | LangGraph node mới |
| 3 | Tạo Jira task từ checklist items | Jira API (đã kết nối) |
| 4 | Draft email tóm tắt | Mail integration |
| 5 | UI: form input + hiển thị checklist + status tracking | React (đã có) |

**Tích hợp cần thêm:** Mail (đã xác nhận dùng được). Không cần tích hợp mới.

## Lợi Ích Trực Tiếp

- Giảm 60–70% thời gian chuẩn bị checklist thủ công.
- Đảm bảo coverage đồng nhất — không ai bỏ sót điều khoản.
- Audit trail đầy đủ: mỗi checklist được gắn với nguồn policy cụ thể.

## Giá Trị Khi Mở Rộng

- Thêm template cho các loại đối tác khác nhau (merchant, bank, fintech).
- Học từ lịch sử review để cải thiện độ chính xác checklist theo thời gian.
- Có thể xuất báo cáo định kỳ cho NHNN hoặc internal audit.

## Nổi Bật Zalopay Wiki Agent

Đây là use case **showcase mạnh nhất** cho RAG grounded — mọi mục trong checklist đều phải trích dẫn nguồn từ policy doc cụ thể. Người dùng thấy ngay giá trị: không phải "AI đoán", mà là "AI đọc đúng policy và trả ra đúng checklist có nguồn". Rất thuyết phục với ban lãnh đạo và đội compliance.

## High-Level System Design

```
[User Input: product/partner description]
        │
        ▼
[LangGraph Supervisor]
        │
        ├──▶ [RAG Node] ──▶ OpenSearch (risk policies, KYC/AML, past reviews)
        │         │
        │         ▼
        │   [Grade + Rerank chunks]
        │         │
        ▼         ▼
[Checklist Generator Node] ── prompt template + retrieved context
        │
        ├──▶ [Jira Node] → tạo task/subtask per checklist item
        ├──▶ [Mail Node] → draft email cho Risk Committee / partner
        └──▶ [UI Response] → hiển thị checklist + citation trong chat
```
