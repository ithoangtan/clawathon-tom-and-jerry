"""One-off: publish the sample 'Risk: Campaign Review — Lucky Wheel' workflow page.

Creates (or updates) an ACTIVE workflow definition in the Confluence ``Workflow``
space following the Tầng-1 template, with labels zalopay-workflow / status-active /
domain-risk so the agent's discovery can find and execute it. Idempotent by title.
"""

from __future__ import annotations

import httpx

from app.adapters.confluence_credentials import resolve_confluence_api_token
from app.config import get_settings

SPACE_KEY = "Workflow"
SPACE_ID = "1867779"
TITLE = "Risk: Campaign Review — Lucky Wheel"
LABELS = ["zalopay-workflow", "status-active", "domain-risk", "wf-risk-campaign-review-lucky-wheel"]

BODY = """
<table><tbody>
<tr><th>Field</th><th>Value</th></tr>
<tr><td>Trigger</td><td>Khi có campaign khuyến mãi mới cần review rủi ro trước khi go-live</td></tr>
<tr><td>Owner</td><td>Risk Team</td></tr>
<tr><td>Participants</td><td>Risk Reviewer · Biz Creator · Product Ops</td></tr>
<tr><td>Definition Status</td><td>ACTIVE</td></tr>
<tr><td>Jira Source</td><td>existing-ticket</td></tr>
<tr><td>Version</td><td>2026-06-15 · Người sửa: Risk Platform</td></tr>
</tbody></table>

<h2>Lifecycle</h2>
<table><tbody>
<tr><th>Status</th><th>Ý nghĩa</th><th>Bước tiếp theo</th></tr>
<tr><td>SUBMITTED</td><td>Ticket mới được gán vào</td><td>UNDER REVIEW</td></tr>
<tr><td>UNDER REVIEW</td><td>Đang review</td><td>APPROVED / REJECTED / ESCALATED</td></tr>
<tr><td>ESCALATED</td><td>Cần cấp cao hơn duyệt</td><td>APPROVED / REJECTED</td></tr>
<tr><td>APPROVED</td><td>Đã duyệt</td><td>DONE</td></tr>
<tr><td>REJECTED</td><td>Không đạt</td><td>(terminal)</td></tr>
<tr><td>DONE</td><td>Hoàn thành</td><td>(terminal)</td></tr>
</tbody></table>
<p>Executable statuses: SUBMITTED, UNDER REVIEW, ESCALATED</p>

<h2>Step 1: Lấy thông tin ticket và campaign</h2>
<p><strong>Responsible:</strong> Risk Reviewer — Risk</p>
<p><strong>Type:</strong> fetch</p>
<p><strong>Input:</strong> Jira ticket key của campaign</p>
<p><strong>Action:</strong> Đọc Jira ticket để lấy mô tả campaign, loại quà tặng và ngân sách</p>
<p><strong>Output:</strong> Bối cảnh campaign đã được tóm tắt</p>

<h2>Step 2: Kiểm tra chính sách phương thức thanh toán</h2>
<p><strong>Responsible:</strong> Risk Reviewer — Risk</p>
<p><strong>Type:</strong> rag</p>
<p><strong>Input:</strong> Tóm tắt campaign</p>
<p><strong>Action:</strong> Tra cứu chính sách lạm dụng phương thức thanh toán và quy định loại trừ tài khoản starter</p>
<p><strong>Output:</strong> Các phát hiện có trích dẫn nguồn</p>
<p>Checklist:</p>
<ul>
<li>VietQR đã bị chặn cho campaign này chưa?</li>
<li>Tài khoản starter đã được loại trừ chưa?</li>
<li>Có giới hạn số lần nhận quà mỗi user chưa?</li>
</ul>
<p><strong>Policy ref:</strong> Payment Method Abuse Policy (Risk space)</p>

<h2>Step 3: Cổng điều kiện giá trị quà tặng</h2>
<p><strong>Responsible:</strong> Risk Reviewer — Risk</p>
<p><strong>Type:</strong> gate</p>
<p><strong>Condition:</strong> Nếu giá trị quà tặng &gt; 1.000.000 VND thì escalate cho Head of Risk; ngược lại tiếp tục</p>
<p><strong>Output:</strong> Quyết định proceed / escalate</p>

<h2>Step 4: Đăng đánh giá rủi ro lên Jira</h2>
<p><strong>Responsible:</strong> Risk Reviewer — Risk</p>
<p><strong>Type:</strong> action</p>
<p><strong>Input:</strong> Toàn bộ phát hiện và quyết định ở các bước trên</p>
<p><strong>Action:</strong> Tổng hợp risk assessment và đăng làm comment trên Jira ticket gốc</p>
<p><strong>Output:</strong> Comment risk assessment trên Jira</p>

<h2>Triggers</h2>
<table><tbody>
<tr><th>Event</th><th>Condition</th><th>Action</th></tr>
<tr><td>status_changed</td><td>UNDER REVIEW → APPROVED</td><td>Tổng hợp kết quả review và cập nhật lên Confluence page, đồng thời comment tóm tắt lên Jira</td></tr>
<tr><td>status_changed</td><td>* → ESCALATED</td><td>Tóm tắt lý do cần escalate và comment cho Head of Risk trên Jira</td></tr>
<tr><td>comment_added</td><td>chứa "@agent recheck"</td><td>Chạy lại kiểm tra chính sách thanh toán và comment kết quả</td></tr>
</tbody></table>
""".strip()


def main() -> None:
    s = get_settings()
    base = (s.confluence_base_url or "").rstrip("/")
    auth = (s.confluence_email, resolve_confluence_api_token(s))

    with httpx.Client(timeout=30.0, auth=auth) as client:
        # Idempotent: find existing page by title via CQL.
        existing = client.get(
            f"{base}/rest/api/content/search",
            params={"cql": f'space="{SPACE_KEY}" and title="{TITLE}" and type=page'},
        ).json().get("results", [])

        if existing:
            page_id = existing[0]["id"]
            cur = client.get(
                f"{base}/api/v2/pages/{page_id}", params={"body-format": "storage"}
            ).json()
            version = (cur.get("version") or {}).get("number", 1) + 1
            resp = client.put(
                f"{base}/api/v2/pages/{page_id}",
                json={
                    "id": page_id,
                    "status": "current",
                    "title": TITLE,
                    "spaceId": SPACE_ID,
                    "body": {"representation": "storage", "value": BODY},
                    "version": {"number": version},
                },
            )
            resp.raise_for_status()
            print(f"Updated page {page_id} (v{version})")
        else:
            resp = client.post(
                f"{base}/api/v2/pages",
                json={
                    "spaceId": SPACE_ID,
                    "status": "current",
                    "title": TITLE,
                    "body": {"representation": "storage", "value": BODY},
                },
            )
            resp.raise_for_status()
            page_id = resp.json()["id"]
            print(f"Created page {page_id}")

        # Attach labels via the v1 label endpoint (v2 has no label-create).
        label_resp = client.post(
            f"{base}/rest/api/content/{page_id}/label",
            json=[{"prefix": "global", "name": name} for name in LABELS],
        )
        label_resp.raise_for_status()
        print("Labels attached:", [r["name"] for r in label_resp.json().get("results", [])])

        url = f"{base}/wiki/spaces/{SPACE_KEY}/pages/{page_id}"
        print("Page URL:", url)


if __name__ == "__main__":
    main()
