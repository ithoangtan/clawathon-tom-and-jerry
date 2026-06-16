"""Create test data for 10 end-to-end test cases.

Cases:
  1-2  : RAG knowledge happy cases — print recommended Q&A (no data created)
  3-4  : Multi-department Lucky Wheel — create Bank page, print questions
  5    : Jira workflow — no Confluence link → expect invalid comment + To Do
  6    : Jira workflow — fake Confluence link → expect unreadable comment + To Do
  7    : Jira workflow — ALL PASS criteria
  8    : Jira workflow — PARTIAL_FAIL (2-3 Chưa rõ)
  9    : Jira workflow — FAIL (critical violation: VietQR + no FA)
  10   : Jira workflow — PARTIAL_FAIL (minor issues)
  11   : Jira workflow — FAIL (multiple violations)

Usage:
    cd code/zalopay-knowledge
    python -m scripts.create_test_data_10_cases

Output: prints Confluence page URLs + Jira ticket keys for each case.
"""
from __future__ import annotations

import base64
import json
import logging
import re
import sys
from typing import Any

import httpx

from app.adapters.confluence_credentials import resolve_confluence_api_token
from app.adapters.jira_client import JiraClient
from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BANK_SPACE = "ClawathonBank"
RISK_SPACE = "ClawathonRisk"
WF_LABEL = "wf-campaign-risk-review"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _confluence_headers(settings) -> dict[str, str]:
    token = resolve_confluence_api_token(settings)
    creds = base64.b64encode(f"{settings.confluence_email}:{token}".encode()).decode()
    return {
        "Authorization": f"Basic {creds}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _get_space_id(base_url: str, space_key: str, headers: dict) -> str | None:
    url = f"{base_url}/api/v2/spaces?keys={space_key}&limit=1"
    r = httpx.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    results = r.json().get("results") or []
    return results[0]["id"] if results else None


def _find_page_by_title(base_url: str, space_id: str, title: str, headers: dict) -> str | None:
    from urllib.parse import urlencode
    params = urlencode({"spaceId": space_id, "title": title, "limit": 1})
    url = f"{base_url}/api/v2/pages?{params}"
    r = httpx.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    results = r.json().get("results") or []
    return results[0]["id"] if results else None


def _md_to_html(body_md: str) -> str:
    """Convert simple markdown to Confluence storage-format HTML (no nested block issues)."""
    lines = body_md.split("\n")
    out: list[str] = []
    in_list = False
    in_para = False

    def _close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    def _close_para():
        nonlocal in_para
        if in_para:
            out.append("</p>")
            in_para = False

    def _inline(text: str) -> str:
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        return text

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped == "---":
            _close_list()
            _close_para()
            continue
        m = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if m:
            _close_list()
            _close_para()
            level = len(m.group(1))
            out.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
            continue
        if stripped.startswith("| ") and stripped.endswith("|"):
            _close_list()
            _close_para()
            continue
        li_m = re.match(r"^-\s+(.+)$", stripped)
        if li_m:
            _close_para()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_inline(li_m.group(1))}</li>")
            continue
        _close_list()
        if not in_para:
            out.append("<p>")
            in_para = True
        else:
            out.append(" ")
        out.append(_inline(stripped))

    _close_list()
    _close_para()
    return "\n".join(out)


def _create_page(
    base_url: str,
    space_id: str,
    title: str,
    body_md: str,
    headers: dict,
    parent_id: str | None = None,
) -> str:
    existing = _find_page_by_title(base_url, space_id, title, headers)
    if existing:
        logger.info("Page %r already exists (id=%s) — reusing", title, existing)
        return existing
    html = _md_to_html(body_md)
    payload: dict[str, Any] = {
        "type": "page",
        "title": title,
        "space": {"id": space_id},
        "body": {"storage": {"value": html, "representation": "storage"}},
    }
    if parent_id:
        payload["ancestors"] = [{"id": parent_id}]
    url = f"{base_url}/rest/api/content"
    r = httpx.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    page_id = r.json()["id"]
    logger.info("Created page %r → id=%s", title, page_id)
    return page_id


def _create_ticket(jira: JiraClient, summary: str, description: str) -> str:
    ticket = jira.create_issue(summary=summary, description=description, issuetype="Task")
    key = ticket.get("key", "")
    logger.info("Created ticket: %s", key)
    return key


def _label_and_review(jira: JiraClient, key: str) -> None:
    jira.add_labels(key=key, labels=[WF_LABEL])
    # Jira workflow: To Do → Darft config → RISK REVIEW
    # Try direct first; if not available, go through intermediate "Darft config".
    try:
        jira.update_issue_status(key=key, transition_name="RISK REVIEW")
        logger.info("%s → moved to RISK REVIEW (direct)", key)
        return
    except Exception:  # noqa: BLE001
        pass
    try:
        jira.update_issue_status(key=key, transition_name="Darft config")
        logger.info("%s → moved to Darft config", key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("%s — could not move to Darft config: %s", key, exc)
        return
    try:
        jira.update_issue_status(key=key, transition_name="RISK REVIEW")
        logger.info("%s → moved to RISK REVIEW (via Darft config)", key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("%s — could not move to RISK REVIEW from Darft config: %s", key, exc)


# ── Page content templates ────────────────────────────────────────────────────

BANK_PAGE_BODY = """
# Lucky Wheel — Bank Partnerships Integration

**Owner:** Bank Partnerships Team
**Version:** 1.0
**Status:** Production

---

## 1. Tổng quan

Lucky Wheel là tính năng gamification của ZaloPay. Phần này mô tả các yêu cầu và ràng buộc liên quan đến bank partnerships khi triển khai campaign Lucky Wheel.

---

## 2. Settlement & Refund Policy theo Bank

### 2.1 Ngân hàng liên kết hỗ trợ

| Ngân hàng | Settlement T+ | Refund SLA | Ghi chú |
|---|---|---|---|
| Vietcombank | T+1 | 3–5 ngày làm việc | Hỗ trợ auto-refund |
| Techcombank | T+1 | 3–5 ngày làm việc | Hỗ trợ auto-refund |
| ACB | T+2 | 5–7 ngày làm việc | Manual refund qua CS |
| MB Bank | T+1 | 3–5 ngày làm việc | Hỗ trợ auto-refund |
| VPBank | T+2 | 5–7 ngày làm việc | Manual refund qua CS |
| BIDV | T+1 | 3–5 ngày làm việc | Hỗ trợ auto-refund |

### 2.2 Refund Conditions

- Refund chỉ áp dụng khi giao dịch bị lỗi sau khi đã debit từ tài khoản ngân hàng
- Voucher đã claim **không được hoàn lại** (theo điều khoản sử dụng)
- Xu ZaloPay: hoàn tự động trong 24 giờ nếu không claim được do lỗi hệ thống

---

## 3. Merchant Restrictions theo Bank Agreement

### 3.1 Restricted Categories (không được làm reward)

Theo thoả thuận với các bank đối tác, các merchant/category sau **không được** phép là reward trong Lucky Wheel:

- **Cờ bạc / Gambling**: casino, cá cược thể thao online
- **Tiền mã hoá / Crypto exchanges**: binance, bybit, okx
- **Dịch vụ cho vay nặng lãi** (lãi suất > 20%/năm)
- **Merchant chưa được KYC bởi ZaloPay** (unverified merchants)

### 3.2 Allowed Payment Methods

- Tài khoản ngân hàng liên kết (linked bank account)
- ZaloPay Balance (ví ZaloPay)
- **VietQR: CHỈ cho top-up ví, KHÔNG dùng để thanh toán trực tiếp trong Lucky Wheel rewards**
- Apple Pay / Google Pay: được phép cho giao dịch dưới 2,000,000 VND

---

## 4. Bank Reporting Requirements

Campaign có reward liên quan đến bank transfer (> 2,000,000 VND/user) cần:

- Báo cáo định kỳ: T+5 sau khi campaign kết thúc
- Format: Excel theo template Bank Reporting v2.3
- Recipient: partnerships@zalopay.vn + cc: reporting@bank-partner.vn

---

## 5. Regulatory Compliance

### 5.1 AML/KYC Requirements

- Tất cả reward > 5,000,000 VND/user yêu cầu **KYC Level 2 trở lên**
- Giao dịch tích luỹ > 50,000,000 VND/tháng: báo cáo STR theo Thông tư 09/2023/TT-NHNN

### 5.2 Reporting to State Bank of Vietnam (SBV)

- Campaign với tổng ngân sách > 5 tỷ VND: cần thông báo SBV trước 15 ngày
- Merchant nước ngoài: cần phê duyệt NHNN cho cross-border payment

---

## 6. Contact & Escalation

- **Bank Partnerships Lead:** partnerships@zalopay.vn
- **Settlement Issues:** finance-ops@zalopay.vn
- **Dispute Resolution:** cs-bank@zalopay.vn
"""

# ── Workflow test case pages ───────────────────────────────────────────────────

CASE7_PASS_BODY = """
# Campaign Spec — TC07 — Summer Lucky Wheel 2026 (All Pass)

**MKT Code:** DGS_070626_TC07
**Ngân sách tổng:** 200,000,000 VND
**FA Approve:** Nguyễn Thành Tâm — Finance — 10/06/2026
**Testing:** 15/06/2026
**Live time:** 10:00 20/06/2026 – 23:59 30/06/2026

---

## Ngân sách và phê duyệt

Tổng ngân sách: 200M VND. FA đã phê duyệt bởi Nguyễn Thành Tâm (Finance) ngày 10/06/2026.
Budget alert đã cấu hình: 50% / 75% / 95%.

---

## Giá trị quà tối đa per user

Mỗi user tối đa nhận 200,000 VND (voucher) per campaign. Đây là dưới ngưỡng 1,000,000 VND theo chính sách.

---

## Merchant và Category

- Chỉ dùng merchant đã được ZaloPay KYC và approved
- Không sử dụng bất kỳ merchant/category bị restricted
- Reward: voucher Shopee, GrabFood (đều là merchant hợp lệ)

---

## RISK CONFIRM

- Chặn VietQR payment (đã cấu hình)
- Chặn Apple Pay (đã cấu hình)
- Loại malicious users theo list Risk team (update ngày 01/06/2026)

---

## KYC Requirements

User tham gia yêu cầu KYC Basic (Level 1) trở lên. Đã xác định rõ trong config.

---

## Thời gian campaign

Ngày bắt đầu: 20/06/2026 lúc 10:00. Ngày kết thúc: 30/06/2026 lúc 23:59. Rõ ràng và cụ thể.

---

## Task List và Reward

- Task 1: Đặt vé máy bay → 2 lượt/tuần (hợp lệ)
- Task 2: Bill thanh toán → 1 lượt/tuần (hợp lệ)
- Reward: Voucher 50K, 100K, 200K Shopee và GrabFood
- Không vi phạm chính sách khuyến mãi hiện hành

---

## Voucher Configuration

- Shopee 50K: min order 200K, SOF = ZaloPay, HSD 30 ngày
- GrabFood 100K: min order 150K, SOF = ZaloPay, HSD 30 ngày
- Tất cả voucher đều có điều kiện sử dụng rõ ràng

---

## UserID Testing List

- UserID_Test_01: 181211000004278
- UserID_Test_02: 200124000486951
- UserID_Test_03: 181002000000026
- UserID_Test_04: 180219000003633
- UserID_Test_05: 200807000019734
"""

CASE8_PARTIAL_BODY = """
# Campaign Spec — TC08 — Autumn Lucky Wheel (Partial Issues)

**MKT Code:** DGS_080626_TC08
**Ngân sách tổng:** 150,000,000 VND
**FA Approve:** Lê Minh Phúc — Finance — 12/06/2026
**Testing:** 18/06/2026
**Live time:** 01/07/2026 – 31/07/2026

---

## Ngân sách và phê duyệt

Tổng ngân sách: 150M VND. FA phê duyệt bởi Lê Minh Phúc ngày 12/06/2026.
Budget alert: đã cấu hình mốc 75%.

---

## Giá trị quà tối đa per user

Campaign có nhiều loại reward nhưng chưa nêu rõ ngưỡng tổng giá trị quà tối đa mỗi user có thể nhận trong toàn bộ campaign.

---

## Merchant và Category

Chỉ dùng merchant đã được ZaloPay approve. Không có merchant restricted.

---

## RISK CONFIRM

- Chặn VietQR (đã cấu hình)
- Chặn malicious users (đã cấu hình)
- Apple Pay: chưa xác nhận có chặn hay không trong config hiện tại.

---

## KYC Requirements

User tham gia yêu cầu đăng nhập ZaloPay. KYC level cụ thể chưa được nêu trong spec này.

---

## Thời gian campaign

Ngày bắt đầu: 01/07/2026. Ngày kết thúc: 31/07/2026. Rõ ràng.

---

## Task List và Reward

- Task 1: Đặt vé → 2 lượt/tuần
- Task 2: Thanh toán bill → 1 lượt/tuần
- Reward: Voucher Tiki, Lazada

---

## Voucher Configuration

- Tiki 50K: min order 200K, SOF = ZaloPay, HSD 30 ngày
- Lazada 100K: SOF = ZaloPay, HSD 30 ngày (thiếu min order)

---

## UserID Testing

Chưa có danh sách UserID testing trong spec này.
"""

CASE9_FAIL_BODY = """
# Campaign Spec — TC09 — Flash Sale Wheel (Critical Violations)

**MKT Code:** DGS_090626_TC09
**Ngân sách tổng:** 300,000,000 VND
**Người duyệt ngân sách:** PM tự approve (chưa có FA sign-off)
**Testing:** 25/06/2026
**Live time:** 01/07/2026 – 15/07/2026

---

## Ngân sách và phê duyệt

Tổng ngân sách: 300M VND. Hiện tại PM tự phê duyệt, chưa gửi FA review. Sẽ xin FA sau khi Risk approve.

---

## Giá trị quà tối đa per user

Mỗi user có thể nhận tối đa 500,000 VND trong campaign.

---

## Merchant và Category

Chỉ dùng merchant hợp lệ. Reward là cashback vào ví ZaloPay.

---

## RISK CONFIRM

Cấu hình thanh toán:
- **Cho phép VietQR** để người dùng thanh toán nhanh qua QR (tiện lợi hơn cho user)
- Chặn malicious users

---

## KYC Requirements

Tất cả user ZaloPay đều có thể tham gia, không cần KYC.

---

## Thời gian campaign

Bắt đầu: 01/07/2026. Kết thúc: 15/07/2026.

---

## Task List và Reward

- Task 1: Thanh toán qua ZaloPay → 3 lượt/tuần
- Task 2: Mời bạn → 1 lượt/campaign
- Reward: Cashback 5% vào ví (tối đa 50K)

---

## Voucher Configuration

Cashback tự động, không cần voucher code.

---

## UserID Testing

- Test_01: 181211000004278
- Test_02: 200124000486951
"""

CASE10_MINOR_BODY = """
# Campaign Spec — TC10 — Weekend Bonus Wheel (Minor Issues)

**MKT Code:** DGS_100626_TC10
**Ngân sách tổng:** 80,000,000 VND
**FA Approve:** Trần Thị Hương — Finance — 11/06/2026
**Testing:** 20/06/2026
**Live time:** 28/06/2026 – 28/07/2026

---

## Ngân sách và phê duyệt

Tổng ngân sách: 80M VND. FA phê duyệt bởi Trần Thị Hương (Finance) ngày 11/06/2026.
Budget alert: đã cấu hình mốc 90% (chỉ 1 mốc).

---

## Giá trị quà tối đa per user

Mỗi user tối đa 100,000 VND per campaign. Dưới ngưỡng chính sách.

---

## Merchant và Category

Merchant hợp lệ, đã KYC. Không có restricted merchant.

---

## RISK CONFIRM

- Chặn VietQR (đã cấu hình)
- Chặn Apple Pay (đã cấu hình)
- Chặn malicious users (đã cấu hình)

---

## KYC Requirements

User yêu cầu KYC Basic. Đã xác định rõ.

---

## Thời gian campaign

Bắt đầu: 28/06/2026. Kết thúc: 28/07/2026. Rõ ràng.

---

## Task List và Reward

- Task 1: Thanh toán bill → 2 lượt/tuần
- Task 2: Mua sắm online → 1 lượt/tuần
- Reward: Voucher 30K, 50K, 100K Sendo

---

## Voucher Configuration

- Sendo 30K: min order 150K, HSD 30 ngày (thiếu SOF)
- Sendo 50K: SOF = ZaloPay, min order 200K, HSD 30 ngày

---

## UserID Testing

- Test_01: 181211000004278
- Test_02: 200124000486951
- Test_03: 181002000000026
"""

CASE11_ALL_FAIL_BODY = """
# Campaign Spec — TC11 — Mega Wheel Blitz (Multiple Violations)

**MKT Code:** DGS_110626_TC11
**Ngân sách tổng:** 500,000,000 VND
**Phê duyệt ngân sách:** Team leader tự duyệt, không qua FA
**Testing:** 30/06/2026
**Live time:** 01/07/2026 – 31/07/2026

---

## Ngân sách và phê duyệt

Tổng ngân sách: 500M VND. Team leader tự phê duyệt, chưa có FA sign-off vì "urgent campaign".

---

## Giá trị quà tối đa per user

Chưa xác định giới hạn quà tối đa per user. Sẽ phụ thuộc vào số lần quay của user.

---

## Merchant và Category

- Merchant chính: Shopee, Lazada (hợp lệ)
- **Thêm merchant VNShark.io** (crypto exchange — chưa được KYC bởi ZaloPay)

---

## RISK CONFIRM

- **Cho phép VietQR** để tăng conversion rate
- **Không cấu hình chặn Apple Pay** (muốn hỗ trợ iOS users)
- Không có cơ chế chặn malicious users trong spec này

---

## KYC Requirements

Không có yêu cầu KYC cụ thể — muốn maximize reach.

---

## Thời gian campaign

Bắt đầu: 01/07/2026. Kết thúc: 31/07/2026.

---

## Task List và Reward

- Task 1: Quay Lucky Wheel → không giới hạn lượt
- Task 2: Invite friends → 5 lượt/ngày (không giới hạn)
- Reward: Voucher + Xu (chưa xác định pool cụ thể)

---

## Voucher Configuration

Chưa có điều kiện sử dụng cụ thể — sẽ cấu hình sau khi launch.

---

## UserID Testing

Chưa có. Sẽ dùng production users để test.
"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    settings = get_settings()
    if not settings.confluence_base_url or not settings.confluence_email:
        logger.error("CONFLUENCE_BASE_URL and CONFLUENCE_EMAIL must be set in .env")
        sys.exit(1)

    base_url = settings.confluence_base_url.rstrip("/")
    headers = _confluence_headers(settings)

    # ── Get space IDs ──────────────────────────────────────────────────────────
    bank_space_id = _get_space_id(base_url, BANK_SPACE, headers)
    risk_space_id = _get_space_id(base_url, RISK_SPACE, headers)

    if not bank_space_id:
        logger.error("Space %r not found — create it on Confluence first", BANK_SPACE)
        sys.exit(1)
    if not risk_space_id:
        logger.error("Space %r not found — create it on Confluence first", RISK_SPACE)
        sys.exit(1)

    logger.info("Bank space ID: %s, Risk space ID: %s", bank_space_id, risk_space_id)

    jira = JiraClient(settings)
    if not jira.configured():
        logger.error("Jira not configured — check .env for JIRA credentials")
        sys.exit(1)

    result: dict = {}

    # ── Cases 1-2: RAG Happy Cases ────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("CASES 1-2: RAG Knowledge Happy Cases")
    print("=" * 70)
    print("Không cần tạo data. Dùng Confluence pages đã có.")
    print()
    print("CASE 1 — Risk SOP:")
    print("  Q: 'Quy trình Risk Review cho một campaign Lucky Wheel bao gồm những bước nào?'")
    print("  Expected: Trả lời từ Risk SOP (ClawathonRisk), cite source")
    print()
    print("CASE 2 — Lucky Wheel PRD:")
    print("  Q: 'Lucky Wheel campaign gồm những loại task nào và reward distribution như thế nào?'")
    print("  Expected: Trả lời từ Lucky Wheel PRD (ClawathonGrow), cite source")

    # ── Cases 3-4: Multi-department ──────────────────────────────────────────
    print("\n" + "=" * 70)
    print("CASES 3-4: Multi-department Lucky Wheel")
    print("=" * 70)

    bank_page_id = _create_page(
        base_url, bank_space_id,
        "Lucky Wheel — Bank Partnerships Integration",
        BANK_PAGE_BODY, headers,
    )
    bank_page_url = f"{base_url}/pages/viewpage.action?pageId={bank_page_id}"
    result["case3_4_bank_page"] = {"id": bank_page_id, "url": bank_page_url}
    logger.info("Bank page: %s", bank_page_url)

    print()
    print("Bank Partnerships page created (or reused):")
    print(f"  {bank_page_url}")
    print()
    print("CASE 3 — Multi-dept query:")
    print("  Q: 'Lucky Wheel ảnh hưởng đến các bank partnerships như thế nào? Liên quan Risk và Growth Enablement?'")
    print("  Expected: response có nội dung từ cả 3 department")
    print()
    print("CASE 4 — Payment methods:")
    print("  Q: 'Các quy định về payment method nào được phép trong Lucky Wheel theo Risk, Growth và Bank Partnerships?'")
    print("  Expected: multi-source synthesis từ 3 spaces")
    print("  NOTE: Sync ClawathonBank trước khi test: make sync-confluence")

    # ── Cases 5-11: Jira Workflow Cases ───────────────────────────────────────
    print("\n" + "=" * 70)
    print("CASES 5-11: Jira Workflow End-to-End")
    print("=" * 70)

    # Case 5 — No Confluence link
    key5 = _create_ticket(
        jira,
        summary="[TC05] No Confluence Link — Campaign Setup Request",
        description=(
            "# Campaign Request TC05\n\n"
            "**Tên campaign:** Summer Flash Sale 2026\n"
            "**MKT Code:** DGS_050626_TC05\n"
            "**Ngân sách:** 50,000,000 VND (FA approved)\n\n"
            "## Mô tả\n\n"
            "Campaign khuyến mãi mùa hè. Các thông tin chi tiết sẽ được cập nhật sau.\n\n"
            "Vui lòng review và approve.\n"
        ),
    )
    _label_and_review(jira, key5)
    result["case5"] = {"key": key5, "expected": "invalid: no_confluence_link → To Do"}
    print(f"\nCase 5 (No link): {key5}")

    # Case 6 — Fake Confluence link
    fake_page_url = f"{base_url}/spaces/ClawathonRisk/pages/9999999/Fake-Campaign-Spec-Page"
    key6 = _create_ticket(
        jira,
        summary="[TC06] Fake Confluence Link — Campaign Setup Request",
        description=(
            "# Campaign Request TC06\n\n"
            "**Tên campaign:** Autumn Bonanza 2026\n"
            "**MKT Code:** DGS_060626_TC06\n"
            "**Ngân sách:** 100,000,000 VND (FA approved)\n\n"
            "## Links\n\n"
            f"- **Confluence Campaign Doc:** {fake_page_url}\n\n"
            "Campaign spec đầy đủ được lưu tại link Confluence trên.\n"
        ),
    )
    _label_and_review(jira, key6)
    result["case6"] = {"key": key6, "expected": "invalid: confluence_unreadable → To Do"}
    print(f"Case 6 (Fake link): {key6}")

    # Case 7 — ALL PASS
    page7_id = _create_page(
        base_url, risk_space_id,
        "TC07 — Summer Lucky Wheel 2026 (All Pass)",
        CASE7_PASS_BODY, headers,
    )
    page7_url = f"{base_url}/pages/viewpage.action?pageId={page7_id}"
    key7 = _create_ticket(
        jira,
        summary="[TC07][DGS_070626_TC07] Summer Lucky Wheel 2026 — All criteria comply",
        description=(
            "# Campaign Request TC07 — All PASS\n\n"
            "**MKT Code:** DGS_070626_TC07\n"
            "**Ngân sách:** 200,000,000 VND (FA approved)\n\n"
            "## Links\n\n"
            f"- **Confluence Campaign Doc:** {page7_url}\n\n"
            "Campaign spec đầy đủ tại link trên. Tất cả criteria đã được chuẩn bị đầy đủ.\n"
        ),
    )
    _label_and_review(jira, key7)
    result["case7"] = {"key": key7, "page_url": page7_url, "expected": "DECISION: PASS → Done"}
    print(f"Case 7 (All PASS): {key7} | page: {page7_url}")

    # Case 8 — PARTIAL_FAIL (2-3 Chưa rõ)
    page8_id = _create_page(
        base_url, risk_space_id,
        "TC08 — Autumn Lucky Wheel (Partial Issues)",
        CASE8_PARTIAL_BODY, headers,
    )
    page8_url = f"{base_url}/pages/viewpage.action?pageId={page8_id}"
    key8 = _create_ticket(
        jira,
        summary="[TC08][DGS_080626_TC08] Autumn Lucky Wheel — partial unclear items",
        description=(
            "# Campaign Request TC08 — PARTIAL_FAIL expected\n\n"
            "**MKT Code:** DGS_080626_TC08\n"
            "**Ngân sách:** 150,000,000 VND (FA approved)\n\n"
            "## Links\n\n"
            f"- **Confluence Campaign Doc:** {page8_url}\n\n"
            "Campaign spec tại link trên. Một số mục chưa rõ ràng cần clarify.\n"
        ),
    )
    _label_and_review(jira, key8)
    result["case8"] = {"key": key8, "page_url": page8_url, "expected": "DECISION: PARTIAL_FAIL → Done"}
    print(f"Case 8 (PARTIAL_FAIL): {key8} | page: {page8_url}")

    # Case 9 — FAIL (critical: VietQR + no FA)
    page9_id = _create_page(
        base_url, risk_space_id,
        "TC09 — Flash Sale Wheel (Critical Violations)",
        CASE9_FAIL_BODY, headers,
    )
    page9_url = f"{base_url}/pages/viewpage.action?pageId={page9_id}"
    key9 = _create_ticket(
        jira,
        summary="[TC09][DGS_090626_TC09] Flash Sale Wheel — critical violations",
        description=(
            "# Campaign Request TC09 — FAIL expected\n\n"
            "**MKT Code:** DGS_090626_TC09\n"
            "**Ngân sách:** 300,000,000 VND (chưa FA approve)\n\n"
            "## Links\n\n"
            f"- **Confluence Campaign Doc:** {page9_url}\n\n"
            "Campaign spec tại link trên. Urgent campaign — cần approve gấp.\n"
        ),
    )
    _label_and_review(jira, key9)
    result["case9"] = {"key": key9, "page_url": page9_url, "expected": "DECISION: FAIL → REJECT"}
    print(f"Case 9 (FAIL - critical): {key9} | page: {page9_url}")

    # Case 10 — PARTIAL_FAIL (minor issues)
    page10_id = _create_page(
        base_url, risk_space_id,
        "TC10 — Weekend Bonus Wheel (Minor Issues)",
        CASE10_MINOR_BODY, headers,
    )
    page10_url = f"{base_url}/pages/viewpage.action?pageId={page10_id}"
    key10 = _create_ticket(
        jira,
        summary="[TC10][DGS_100626_TC10] Weekend Bonus Wheel — minor issues",
        description=(
            "# Campaign Request TC10 — PARTIAL_FAIL expected (minor)\n\n"
            "**MKT Code:** DGS_100626_TC10\n"
            "**Ngân sách:** 80,000,000 VND (FA approved)\n\n"
            "## Links\n\n"
            f"- **Confluence Campaign Doc:** {page10_url}\n\n"
            "Campaign spec tại link trên. Hầu hết đã chuẩn bị đầy đủ.\n"
        ),
    )
    _label_and_review(jira, key10)
    result["case10"] = {"key": key10, "page_url": page10_url, "expected": "DECISION: PARTIAL_FAIL → Done"}
    print(f"Case 10 (PARTIAL_FAIL - minor): {key10} | page: {page10_url}")

    # Case 11 — FAIL (multiple violations)
    page11_id = _create_page(
        base_url, risk_space_id,
        "TC11 — Mega Wheel Blitz (Multiple Violations)",
        CASE11_ALL_FAIL_BODY, headers,
    )
    page11_url = f"{base_url}/pages/viewpage.action?pageId={page11_id}"
    key11 = _create_ticket(
        jira,
        summary="[TC11][DGS_110626_TC11] Mega Wheel Blitz — multiple violations",
        description=(
            "# Campaign Request TC11 — FAIL expected (multiple violations)\n\n"
            "**MKT Code:** DGS_110626_TC11\n"
            "**Ngân sách:** 500,000,000 VND (chưa FA approve)\n\n"
            "## Links\n\n"
            f"- **Confluence Campaign Doc:** {page11_url}\n\n"
            "Campaign spec tại link trên. Urgent — cần approve trước cuối ngày.\n"
        ),
    )
    _label_and_review(jira, key11)
    result["case11"] = {"key": key11, "page_url": page11_url, "expected": "DECISION: FAIL → REJECT"}
    print(f"Case 11 (FAIL - multiple): {key11} | page: {page11_url}")

    # ── Summary ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()
    print("Next steps:")
    print("  1. Sync Confluence: make sync-confluence  (để RAG index có data mới)")
    print("  2. Check Chat UI: xem từng ticket có được tạo session không")
    print("  3. Verify Jira comments cho từng ticket")
    print()
    print("TEST_RESULT=" + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
