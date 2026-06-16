"""Split the promotion risk content so the RAG corpus is clean.

Problem: the combined assessment doc (page 2097171) + the 3 demo campaign specs
live in the risk space, so RAG over `risk` mixes all 3 campaigns and mis-grades a
compliant campaign. Fix — split into:

  - a **rules-only policy** page (11 rules + decision rubric, no campaign examples)
    → stays in the risk space as the clean RAG source;
  - **campaign specs** → the personal space (NOT in CONFLUENCE_SPACES → never indexed).

This script: publishes the clean policy page, recreates the CTKM1 spec in the
personal space, and deletes the polluting pages. Prints a JSON summary.

    python -m scripts.split_risk_policy
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx

from app.adapters.confluence_credentials import resolve_confluence_api_token
from app.common.markdown_storage import md_to_storage
from app.config import get_settings
from scripts.seed_demo_campaigns import _campaign_sections

RISK_SPACE_KEY = "ClawathonRisk"
PERSONAL_SPACE_ID = "65811"  # ~5f30c02142959b00392fdcc6 — not synced into any RAG corpus
POLICY_TITLE = "Promotion Campaign Risk Policy (11 Rules)"
POLICY_LABELS = ["risk-policy", "promotion"]
DELETE_PAGE_IDS = ["2097171", "2195466", "2228236", "2293769"]  # combined doc + 3 demo specs
MD = Path(__file__).resolve().parents[3] / "promotional_campaigns_risk_assessment.md"

POLICY_MD = """# Promotion Campaign Risk Policy — 11 Rules

Khung đánh giá rủi ro cho chương trình khuyến mãi (CTKM). Mỗi rule nêu yêu cầu tuân thủ (Comply) và dấu hiệu vi phạm (Violate). Reviewer đối chiếu campaign spec với 11 rule này.

## 1. Payment channel
Comply: T&C loại trừ rõ các kênh rủi ro cao (VietQR, Apple Pay, card direct, NFC, chuyển tiền); chỉ cho phép thanh toán qua ví đã liên kết tài khoản ngân hàng.
Violate: cho phép mọi kênh hoặc không nêu loại trừ.

## 2. Abuser segment
Comply: exclude malicious abuser; casual abuser chỉ được phép nếu có ghi chú accepted risk; segment yêu cầu KYC + tài khoản hoạt động đủ lâu.
Violate: không exclude abuser, mở cho cả tài khoản mới chưa KYC.

## 3. High-value reward
Comply: reward giá trị cao bị giới hạn số lượng và thu hẹp segment.
Violate: jackpot/giải lớn không giới hạn số lượng hoặc mở cho toàn bộ user.

## 4. High-liquidity reward
Comply: không phát reward dễ cashout/resell (voucher App Store / Google Play).
Violate: có voucher dễ quy đổi tiền mặt.

## 5. Self-payment / giao dịch khống
Comply: yêu cầu giao dịch thực tế tới merchant bên thứ ba; có checkpoint loại trừ giao dịch cùng chủ; loại trừ top-up / nạp ví / chuyển tiền.
Violate: tính nạp ví hoặc giao dịch cùng chủ làm điều kiện mà không lọc.

## 6. Multi-account farming
Comply: giới hạn theo KYC ID và device ID (không chỉ user_id).
Violate: chỉ giới hạn theo user_id hoặc thiếu device ID.

## 7. Stacking CTKM
Comply: T&C quy định rõ 1 giao dịch chỉ hưởng 1 CTKM ưu đãi cao nhất.
Violate: không có điều khoản chống stacking với cashback/referral/CTKM khác.

## 8. Refund
Comply: revoke reward khi giao dịch bị hoàn trong thời hạn quy định; tính GTV net.
Violate: không revoke reward sau hoàn tiền; tính GTV gross.

## 9. KYC
Comply: dùng KYC platform sẵn có, không thêm checkpoint KYC trùng lặp.
Violate: thêm checkpoint KYC riêng trùng lặp gây nhầm lẫn/friction.

## 10. Legal / brand
Comply: tuân Nghị định khuyến mãi; không quảng cáo "0đ" / "100% trúng thưởng"; công bố rõ số lượng và điều kiện.
Violate: quảng cáo gian dối hoặc không công bố giới hạn.

## 11. Data & privacy
Comply: chỉ dùng dữ liệu sẵn có trên platform; không thu thập dư thừa.
Violate: yêu cầu nhập thêm dữ liệu cá nhân (CMND, địa chỉ, SĐT người thân) không cần cho reward.

## Decision rubric
- PASS: 0 rule Violate.
- PARTIAL_FAIL: 1–4 rule Violate nhưng có thể khắc phục (nêu rõ yêu cầu sửa).
- FAIL: vi phạm rule nghiêm trọng (Payment channel / Abuser segment / Legal) hoặc đa số rule.
"""


def main() -> None:
    cfg = get_settings()
    base = (cfg.confluence_base_url or "").rstrip("/")
    auth = (cfg.confluence_email, resolve_confluence_api_token(cfg))
    out: dict = {}

    # CTKM1 spec (info + T&C only) for the new clean ticket.
    ctkm1_md = next(body for n, body in _campaign_sections(MD.read_text(encoding="utf-8")) if n == 1)

    with httpx.Client(timeout=30.0, auth=auth) as client:
        risk_space_id = str(client.get(
            f"{base}/api/v2/spaces", params={"keys": RISK_SPACE_KEY, "limit": 1}
        ).json()["results"][0]["id"])

        # 1. Clean rules-only policy page → risk space (idempotent by title).
        existing = client.get(
            f"{base}/rest/api/content/search",
            params={"cql": f'space="{RISK_SPACE_KEY}" and title="{POLICY_TITLE}" and type=page'},
        ).json().get("results", [])
        body = md_to_storage(POLICY_MD)
        if existing:
            pid = existing[0]["id"]
            cur = client.get(f"{base}/api/v2/pages/{pid}", params={"body-format": "storage"}).json()
            ver = int((cur.get("version") or {}).get("number", 1)) + 1
            client.put(f"{base}/api/v2/pages/{pid}", json={
                "id": pid, "status": "current", "title": POLICY_TITLE, "spaceId": risk_space_id,
                "body": {"representation": "storage", "value": body}, "version": {"number": ver},
            }).raise_for_status()
        else:
            pid = client.post(f"{base}/api/v2/pages", json={
                "spaceId": risk_space_id, "status": "current", "title": POLICY_TITLE,
                "body": {"representation": "storage", "value": body},
            }).json()["id"]
        client.post(f"{base}/rest/api/content/{pid}/label",
                    json=[{"prefix": "global", "name": n} for n in POLICY_LABELS])
        out["policy_page"] = {"id": pid, "url": f"{base}/spaces/{RISK_SPACE_KEY}/pages/{pid}"}

        # 2. CTKM1 campaign spec → personal space (non-synced; read by link only).
        spec_title = "[Demo] Campaign Spec — Lucky Wheel CTKM 1 (clean)"
        existing_spec = client.get(
            f"{base}/rest/api/content/search",
            params={"cql": f'title="{spec_title}" and type=page'},
        ).json().get("results", [])
        spec_body = md_to_storage(ctkm1_md)
        if existing_spec:
            spid = existing_spec[0]["id"]
            cur = client.get(f"{base}/api/v2/pages/{spid}", params={"body-format": "storage"}).json()
            ver = int((cur.get("version") or {}).get("number", 1)) + 1
            client.put(f"{base}/api/v2/pages/{spid}", json={
                "id": spid, "status": "current", "title": spec_title, "spaceId": PERSONAL_SPACE_ID,
                "body": {"representation": "storage", "value": spec_body}, "version": {"number": ver},
            }).raise_for_status()
        else:
            spid = client.post(f"{base}/api/v2/pages", json={
                "spaceId": PERSONAL_SPACE_ID, "status": "current", "title": spec_title,
                "body": {"representation": "storage", "value": spec_body},
            }).json()["id"]
        # personal space web path uses the space key with a leading ~
        out["ctkm1_spec"] = {"id": spid, "url": f"{base}/spaces/~5f30c02142959b00392fdcc6/pages/{spid}"}

        # 3. Delete the polluting pages (combined doc + old in-risk specs).
        deleted = []
        for pid_del in DELETE_PAGE_IDS:
            r = client.delete(f"{base}/api/v2/pages/{pid_del}")
            deleted.append({"id": pid_del, "status": r.status_code})
        out["deleted"] = deleted

    print("SPLIT_RESULT=" + json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
