"""Update the live 'Risk: Campaign Review — Lucky Wheel' workflow page.

Rewrites page **1048659** in the Confluence ``Workflow`` space with a complete
definition that mirrors the campaign flow diagrams (Jira status machine
TO DO → RISK REVIEW → RISK DONE → SETUP CAMPAIGN → IN TESTING → LIVE → DONE,
plus REJECT / CANCELLED) and a ``## Triggers`` table whose key rule fires when a
ticket moves **TO DO → RISK REVIEW**: read the campaign doc linked in the ticket
Description (in-system only), look up risk policy in the zalopay wiki, and post a
Quick Risk Report comment.

Targets the page by id (from the URL), reuses the existing title + spaceId, bumps
the version, and re-attaches the workflow labels. Idempotent. Run inside the
container or with the app's env loaded:

    python -m scripts.update_lucky_wheel_workflow            # default page 1048659
    python -m scripts.update_lucky_wheel_workflow 1048659    # explicit page id
"""

from __future__ import annotations

import sys

import httpx

from app.adapters.confluence_credentials import resolve_confluence_api_token
from app.config import get_settings

PAGE_ID = "1048659"
LABELS = ["zalopay-workflow", "status-active", "domain-risk", "wf-risk-campaign-review-lucky-wheel"]

BODY = """
<table><tbody>
<tr><th>Field</th><th>Value</th></tr>
<tr><td>Trigger</td><td>Khi có campaign khuyến mãi (Lucky Wheel) cần review rủi ro trước khi go-live</td></tr>
<tr><td>Owner</td><td>Risk Team</td></tr>
<tr><td>Participants</td><td>Biz Creator · Risk Reviewer · Product Ops</td></tr>
<tr><td>Definition Status</td><td>ACTIVE</td></tr>
<tr><td>Jira Source</td><td>existing-ticket</td></tr>
<tr><td>Version</td><td>2026-06-15 · Người sửa: Risk Platform</td></tr>
</tbody></table>

<h2>Lifecycle</h2>
<table><tbody>
<tr><th>Status</th><th>Ý nghĩa</th><th>Bước tiếp theo</th></tr>
<tr><td>TO DO</td><td>Ticket vừa tạo, chờ cấu hình nháp</td><td>RISK REVIEW</td></tr>
<tr><td>RISK REVIEW</td><td>Agent + Risk đang review rủi ro</td><td>RISK DONE / REJECT</td></tr>
<tr><td>RISK DONE</td><td>Đã duyệt rủi ro</td><td>SETUP CAMPAIGN</td></tr>
<tr><td>SETUP CAMPAIGN</td><td>Product Ops dựng campaign</td><td>IN TESTING</td></tr>
<tr><td>IN TESTING</td><td>Đang kiểm thử</td><td>LIVE / CANCELLED</td></tr>
<tr><td>LIVE</td><td>Đang chạy thật</td><td>DONE / CANCELLED</td></tr>
<tr><td>DONE</td><td>Hoàn thành</td><td>(terminal)</td></tr>
<tr><td>REJECT</td><td>Bị từ chối ở bước review</td><td>(terminal)</td></tr>
<tr><td>CANCELLED</td><td>Bị huỷ</td><td>(terminal)</td></tr>
</tbody></table>
<p>Executable statuses: RISK REVIEW</p>

<h2>Step 1: Đọc tài liệu campaign từ link trong Description</h2>
<p><strong>Responsible:</strong> Risk Reviewer — Risk</p>
<p><strong>Type:</strong> fetch</p>
<p><strong>Input:</strong> Jira ticket key và (các) link tài liệu trong phần Description</p>
<p><strong>Action:</strong> Đọc campaign spec từ link <strong>in-system</strong> trong Description của ticket (Confluence / Jira / Google Drive). Link nằm ngoài hệ thống đã tích hợp thì bỏ qua.</p>
<p><strong>Output:</strong> Nội dung campaign spec đã được tóm tắt</p>

<h2>Step 2: Đối chiếu 11 policy rules trong zalopay wiki</h2>
<p><strong>Responsible:</strong> Risk Reviewer — Risk</p>
<p><strong>Type:</strong> rag</p>
<p><strong>Input:</strong> Tóm tắt campaign spec</p>
<p><strong>Action:</strong> Tra cứu Risk Assessment Policy trong zalopay wiki (Risk space) và đối chiếu campaign với từng policy rule (Comply / Violate)</p>
<p><strong>Output:</strong> Bảng đối chiếu 11 rule có trích dẫn nguồn</p>
<p>Checklist:</p>
<ul>
<li>Payment channel: VietQR / Apple Pay / card direct bị loại trừ rõ ràng?</li>
<li>Abuser segment: loại trừ cả malicious &amp; casual abuser?</li>
<li>High-value reward: giới hạn số lượng &amp; segment chặt cho reward cao nhất?</li>
<li>High-liquidity reward: không phát voucher dễ cashout (App Store / Google Play)?</li>
<li>Self-payment / giao dịch khống: có checkpoint loại trừ giao dịch cùng chủ?</li>
<li>Multi-account farming: giới hạn theo KYC ID &amp; device ID (không chỉ user_id)?</li>
<li>Stacking CTKM: có điều khoản 1 giao dịch = 1 CTKM ưu đãi cao nhất?</li>
<li>Refund: revoke reward khi hoàn tiền &amp; tính GTV net?</li>
<li>KYC: dùng KYC platform sẵn có, không thêm checkpoint trùng lặp?</li>
<li>Legal / brand: không quảng cáo "0đ / 100% trúng", tuân Nghị định khuyến mãi?</li>
<li>Data &amp; privacy: không thu thập dữ liệu dư thừa (CMND / địa chỉ / SĐT người thân)?</li>
</ul>
<p><strong>Policy ref:</strong> Promotional Campaigns — Risk Assessment Policy (Lucky Wheel) (Risk space)</p>

<h2>Step 3: Risk Decision</h2>
<p><strong>Responsible:</strong> Risk Reviewer — Risk</p>
<p><strong>Type:</strong> gate</p>
<p><strong>Condition:</strong> 0 vi phạm → PASS; 1–4 vi phạm có thể sửa (đã rõ cách khắc phục) → PARTIAL_FAIL; vi phạm nghiêm trọng (payment channel / abuser segment / legal) hoặc đa số rule → FAIL.</p>
<p><strong>Output:</strong> Quyết định PASS / PARTIAL_FAIL / FAIL</p>

<h2>Step 4: Đăng Quick Risk Report lên Jira</h2>
<p><strong>Responsible:</strong> Risk Reviewer — Risk</p>
<p><strong>Type:</strong> action</p>
<p><strong>Input:</strong> Bảng đối chiếu 11 rule và quyết định ở Step 3</p>
<p><strong>Action:</strong> Tổng hợp Quick Risk Report (Comply/Violate từng rule + danh sách yêu cầu sửa nếu có) và đăng làm comment trên Jira ticket; kết thúc bằng dòng DECISION</p>
<p><strong>Output:</strong> Comment Quick Risk Report + dòng "DECISION: PASS|PARTIAL_FAIL|FAIL"</p>

<h2>Triggers</h2>
<table><tbody>
<tr><th>Event</th><th>Condition</th><th>Action</th></tr>
<tr><td>status_changed</td><td>TO DO → RISK REVIEW</td><td>Đọc tài liệu campaign từ link in-system trong Description, đối chiếu 11 policy rules trong zalopay wiki, ra quyết định PASS/PARTIAL_FAIL/FAIL và đăng Quick Risk Report lên Jira; áp dụng phản ứng theo bảng Reactions</td></tr>
<tr><td>comment_added</td><td>chứa "@agent recheck"</td><td>Chạy lại đối chiếu policy dựa trên tài liệu trong Description, ra quyết định và đăng Quick Risk Report; áp dụng phản ứng theo bảng Reactions</td></tr>
</tbody></table>

<h2>Reactions</h2>
<table><tbody>
<tr><th>Decision</th><th>Do</th></tr>
<tr><td>PASS</td><td>comment</td></tr>
<tr><td>PARTIAL_FAIL</td><td>comment; reassign:reporter; label:risk-partial-fail</td></tr>
<tr><td>FAIL</td><td>comment; reassign:reporter; label:risk-rejected</td></tr>
</tbody></table>
""".strip()


def main() -> None:
    page_id = sys.argv[1] if len(sys.argv) > 1 else PAGE_ID
    s = get_settings()
    base = (s.confluence_base_url or "").rstrip("/")
    auth = (s.confluence_email, resolve_confluence_api_token(s))

    with httpx.Client(timeout=30.0, auth=auth) as client:
        cur = client.get(
            f"{base}/api/v2/pages/{page_id}", params={"body-format": "storage"}
        )
        cur.raise_for_status()
        cur = cur.json()
        title = cur.get("title") or "Risk: Campaign Review — Lucky Wheel"
        space_id = str(cur.get("spaceId", ""))
        version = int((cur.get("version") or {}).get("number", 1)) + 1

        resp = client.put(
            f"{base}/api/v2/pages/{page_id}",
            json={
                "id": page_id,
                "status": "current",
                "title": title,
                "spaceId": space_id,
                "body": {"representation": "storage", "value": BODY},
                "version": {"number": version, "message": "Update Lucky Wheel risk-review workflow"},
            },
        )
        resp.raise_for_status()
        print(f"Updated page {page_id} (v{version}) — title={title!r}")

        label_resp = client.post(
            f"{base}/rest/api/content/{page_id}/label",
            json=[{"prefix": "global", "name": name} for name in LABELS],
        )
        label_resp.raise_for_status()
        print("Labels attached:", [r["name"] for r in label_resp.json().get("results", [])])
        print("Page URL:", f"{base}/spaces/Workflow/pages/{page_id}")


if __name__ == "__main__":
    main()
