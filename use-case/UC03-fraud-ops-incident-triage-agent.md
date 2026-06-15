# UC03 — Fraud Ops Incident Triage Agent

## Pain Points

- Đội Fraud Ops nhận hàng trăm case mỗi ngày từ nhiều queue — không đủ người review hết thủ công trong thời gian hợp lý.
- Phải tra cứu lịch sử giao dịch, policy xử lý fraud, precedent từ case cũ — mỗi cái nằm ở một nơi khác nhau.
- Thời gian triage chậm → fraud tiếp tục xảy ra → thiệt hại tăng.
- Quyết định không đồng nhất giữa các analyst.

## Input

- Case ID hoặc mô tả giao dịch nghi vấn: amount, merchant, user profile, transaction pattern.
- Hoặc agent tự pull từ queue (batch mode).

## Agent Behavior

1. **Retrieve context** song song:
   - Lịch sử giao dịch user từ MySQL.
   - Fraud policy và AML rules từ Confluence qua RAG.
   - Case tương tự đã xử lý trước đây (RAG qua past case notes).
2. **Đề xuất:**
   - Risk score (Low / Medium / High / Critical).
   - Recommended action: Allow / Flag for review / Block / Escalate.
   - Lý do + citation từ policy.
3. **Tạo/cập nhật Jira ticket** với đầy đủ context + recommendation.
4. Nếu Critical → **draft email** báo cáo ngay cho Fraud Manager.

## Triển Khai

| Bước | Việc cần làm | Dùng gì |
|---|---|---|
| 1 | MySQL node: query transaction history by user/merchant | MySQL (đã có) |
| 2 | RAG node: fraud policy, AML rules, past cases | OpenSearch (đã có) |
| 3 | Scoring node: tổng hợp context → risk score + recommendation | LangGraph + prompt |
| 4 | Jira node: tạo/update ticket với full context | Jira API (đã có) |
| 5 | Mail node: alert cho manager khi Critical | Mail |

**Tích hợp cần thêm:** Mail. Không cần tích hợp mới.

> **Lưu ý:** Nếu muốn pull case từ queue tự động, cần hỏi thêm: queue này đang ở đâu (MySQL table, Jira, hay hệ thống riêng)?

## Lợi Ích Trực Tiếp

- Giảm 50–70% thời gian triage thủ công.
- Đồng nhất hóa quyết định — mọi recommendation đều có policy citation rõ ràng.
- Analyst chỉ cần review recommendation thay vì làm từ đầu → tập trung vào case phức tạp.

## Giá Trị Khi Mở Rộng

- Học từ feedback của analyst (accept/reject recommendation) để cải thiện model.
- Mở rộng sang dispute resolution, chargeback triage.
- Tích hợp real-time alerting khi phát hiện pattern fraud mới.

## Nổi Bật Zalopay Wiki Agent

Use case này là **killer demo cho stakeholder**: agent đưa ra recommendation có trích dẫn chính sách cụ thể — không phải black box. Audit trail hoàn chỉnh. Nếu sau này bị kiểm toán, mọi quyết định đều có nguồn gốc rõ ràng từ policy doc.

## High-Level System Design

```
[Input: case description / case ID / batch queue]
        │
        ▼
[LangGraph Supervisor]
        │
        ├──▶ [MySQL Node] ─────────▶ transaction history, user profile
        ├──▶ [RAG Node] ───────────▶ fraud policy, AML rules (Confluence)
        └──▶ [RAG Node] ───────────▶ similar past cases (OpenSearch)
                │
                ▼
        [Scoring Node] → risk score + recommended action + citations
                │
                ├──▶ [Jira Node] → create/update ticket
                └──▶ [Mail Node] → alert (if Critical)
```
