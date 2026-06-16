from __future__ import annotations

"""Hardcoded workflow definition for Campaign Risk Review (Lucky Wheel demo).

This definition is identical in shape to a parsed Confluence workflow page —
the handler uses it directly, bypassing Confluence page loading and LLM parsing.

Jira label that activates this workflow: ``wf-campaign-risk-review``
"""

from app.workflow.models import (
    WorkflowDefinition,
    WorkflowReaction,
    WorkflowStep,
    WorkflowTrigger,
)

CAMPAIGN_RISK_REVIEW = WorkflowDefinition(
    name="Campaign Risk Review",
    owner="Risk Team",
    definition_status="ACTIVE",
    jira_source="existing-ticket",
    triggers=[
        WorkflowTrigger(
            event_type="status_changed",
            from_status=None,  # any
            to_status="RISK REVIEW",
            action=(
                "Đánh giá campaign theo checklist risk review dưới đây. "
                "Dựa hoàn toàn vào nội dung ticket Jira và tài liệu campaign spec được đính kèm. "
                "Đối chiếu với chính sách Risk được cung cấp trong phần Ngữ cảnh. "
                "Format từng mục: '- <mục>: **Comply/Violate/Chưa rõ** — <dẫn chứng ngắn>'. "
                "Kết thúc bằng 'DECISION: PASS', 'DECISION: PARTIAL_FAIL' hoặc 'DECISION: FAIL'."
            ),
        ),
    ],
    steps=[
        WorkflowStep(
            index=1,
            title="Checklist đánh giá rủi ro campaign",
            type="checklist",
            checklist=[
                "Tổng ngân sách chiến dịch được khai báo rõ ràng và có phê duyệt FA",
                "Giá trị quà tối đa mỗi user không vượt ngưỡng cho phép theo chính sách",
                "Không sử dụng merchant/category bị cấm hoặc restricted",
                "Cấu hình RISK CONFIRM đã được khai báo (chặn VietQR, Apple Pay, malicious users)",
                "Điều kiện KYC của user tham gia được xác định rõ",
                "Thời gian campaign được xác định (ngày bắt đầu và kết thúc)",
                "Budget alert đã được cấu hình (ít nhất 1 mốc: 50%/75%/95%)",
                "Task list và reward pool không vi phạm chính sách khuyến mãi hiện hành",
                "Các voucher được cấu hình có điều kiện sử dụng (SOF, min order, HSD) rõ ràng",
                "Campaign có danh sách UserID testing để kiểm tra trước khi launch",
            ],
        ),
        WorkflowStep(
            index=2,
            title="Gate quyết định",
            type="gate",
            condition=(
                "PASS nếu tất cả mục đều Comply. "
                "PARTIAL_FAIL nếu 1-2 mục Chưa rõ nhưng không có Violate. "
                "FAIL nếu có bất kỳ mục nào Violate."
            ),
        ),
    ],
    reactions=[
        WorkflowReaction(
            decision="PASS",
            verbs=["comment", "update_status:RISK DONE"],
        ),
        WorkflowReaction(
            decision="PARTIAL_FAIL",
            verbs=["comment", "update_status:RISK DONE"],
        ),
        WorkflowReaction(
            decision="FAIL",
            verbs=["comment", "update_status:REJECT"],
        ),
    ],
)
