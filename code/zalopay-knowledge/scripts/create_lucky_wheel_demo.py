"""Create all Lucky Wheel demo content on Confluence + Jira.

Creates 8 Confluence pages across Growth Enablement and Risk spaces,
then creates a Jira ticket (KAN project) in TO DO status linking to the
campaign request page.

Usage:
    cd code/zalopay-knowledge
    python -m scripts.create_lucky_wheel_demo

Idempotent on Confluence pages (skips if title already exists in the space).
Always creates a fresh Jira ticket.

Output: JSON with page IDs and ticket key, e.g.
    {"pages": {...}, "jira_key": "KAN-42"}
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

import httpx

from app.adapters.confluence_credentials import resolve_confluence_api_token
from app.adapters.jira_client import JiraClient
from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Spaces ────────────────────────────────────────────────────────────────────
GROW_SPACE = "ClawathonGrow"   # Growth Enablement space
RISK_SPACE = "ClawathonRisk"   # Risk space
WF_LABEL = "wf-campaign-risk-review"  # must match app/workflow/registry.py key

# ── Page content ─────────────────────────────────────────────────────────────

PAGES: list[dict[str, Any]] = [
    # ─── Growth Enablement ───────────────────────────────────────────────────
    {
        "space": GROW_SPACE,
        "title": "Lucky Wheel - Product Requirements Document (PRD)",
        "parent_title": None,
        "body": """
# Lucky Wheel - Product Requirements Document (PRD)

## 1. Tổng quan

Lucky Wheel là tính năng gamification trên ứng dụng ZaloPay, cho phép người dùng quay vòng xổ số ảo để nhận các phần thưởng (voucher, xu, vé sự kiện). Mục tiêu là tăng Daily Active Users (DAU) và Transaction Volume thông qua incentive hành vi.

**Owner:** Growth Enablement Team
**Version:** 2.4
**Status:** Production

---

## 2. Cấu hình UI

### 2.1 Thiết kế vòng quay
- Số ô (slot) trên vòng quay: cấu hình động, tối đa 12 ô, mặc định 8 ô
- Mỗi ô có: hình ảnh icon (PNG, 80×80px), label hiển thị (tối đa 16 ký tự)
- Animation: CSS spin với easing `cubic-bezier(0.17, 0.67, 0.12, 0.99)`
- Thời gian quay: 3–5 giây (ngẫu nhiên per session)
- Hỗ trợ dark/light mode

### 2.2 Dynamic Config Tool (Internal)
Ops team cấu hình vòng quay qua admin portal `https://ops.zalopay.vn/lucky-wheel-config`:
- Kéo thả sắp xếp slot
- Upload ảnh trực tiếp lên CDN
- Preview real-time trước khi publish
- Schedule thay đổi (áp dụng từ giờ X)

---

## 3. Cấu hình lượt quay

| Tham số | Mô tả | Giá trị mặc định |
|---|---|---|
| `welcome_turns` | Lượt quay chào mừng khi user mới tham gia campaign | 2 |
| `max_turns_per_day` | Giới hạn lượt quay tối đa/ngày/user | 5 |
| `max_turns_per_campaign` | Giới hạn tổng lượt quay/user/campaign | không giới hạn |
| `turn_expiry_hours` | Số giờ lượt quay hết hạn sau khi nhận | 24 |

Lượt quay thêm: user nhận qua hoàn thành Task (xem mục 5).

---

## 4. Cấu hình quà

### 4.1 Gift Pool
Có 2 loại pool:
- **Weekly pool:** thả vào thứ Hai 10:00 hàng tuần, hết sau 7 ngày
- **Campaign pool:** chạy xuyên suốt campaign

### 4.2 Tỉ lệ quay
- Tổng tỉ lệ tất cả slot = 100%
- Hỗ trợ slot "Xu" với tỉ lệ cao (buffer) để đảm bảo budget không bị vượt
- `counter = 1` nghĩa là mỗi user chỉ nhận loại quà đó 1 lần trong campaign

### 4.3 Giới hạn budget
- Hệ thống tự động dừng phát quà khi budget đạt alert threshold
- Alert thresholds: 50%, 75%, 95%
- Email alert gửi đến danh sách được cấu hình

---

## 5. Task để nhận quà (Task List)

User hoàn thành task → nhận thêm lượt quay.

### 5.1 Loại trigger
- **Payment trigger:** user thực hiện giao dịch thanh toán (theo AppID/EventID)
- **FE Event trigger:** user thực hiện hành động trên app (click, view, search)
- **CPS trigger:** Cost Per Sale — ghi nhận khi có giao dịch thành công từ partner

### 5.2 Cấu trúc Task
| Field | Mô tả |
|---|---|
| Segment | Nhóm user áp dụng (Mass, Starter, VIP…) |
| Title | Tên task hiển thị cho user |
| Description | Mô tả điều kiện hoàn thành |
| Trigger type | Payment / FE Event ID / CPS |
| Trigger condition | AppID hoặc EventID cụ thể |
| Reward | Số lượt quay nhận được |
| Frequency | Giới hạn: 1 lần/ngày, 1 lần/tuần, 1 lần/campaign |
| CTA button | Text nút bấm (VD: "Đặt vé ngay") |
| Deeplink | Link mở màn hình trong app |
| Web URL | Link fallback khi không có app |
| Logo | Icon thương hiệu hiển thị trên task card |

---

## 6. Cấu hình TnC (Terms & Conditions)

- Ads_id: ID bài viết TnC trên Content Management System
- TnC hiển thị dưới dạng popup khi user lần đầu vào campaign
- Bắt buộc scroll đến cuối trước khi nhấn "Đồng ý"
- Cập nhật TnC → tự động yêu cầu user xác nhận lại

---

## 7. Cấu hình hình ảnh slot

- Format: PNG, 80×80px, nền trong suốt (transparent)
- CDN: `https://cdn.zalopay.vn/gamification/lucky-wheel/{campaign_id}/slot-{n}.png`
- Fallback: icon mặc định khi ảnh lỗi
- Tool upload: admin portal hoặc API `POST /internal/lucky-wheel/assets`

---

## 8. Điều kiện tham gia (Eligibility)

| Điều kiện | Cấu hình |
|---|---|
| KYC tier | Basic / Verified / All |
| Segment | Mass / Starter / VIP / Custom |
| Visit landing | Có/Không (bắt buộc vào trang campaign trước) |
| Welcome turn | Có/Không (nhận lượt đầu tiên khi mở campaign) |

---

## 9. Edge cases đã xử lý

- User quay đúng lúc slot hết hàng → tự động chuyển sang slot "Xu"
- User có nhiều lượt nhưng tất cả quà đã hết → thông báo "Đang bổ sung quà"
- Double-spin (request gửi 2 lần) → idempotency key ngăn chặn
- User bị block/ban mid-campaign → lượt quay bị hủy, quà đã nhận giữ nguyên
""",
    },
    {
        "space": GROW_SPACE,
        "title": "Lucky Wheel - Technical Spec Backend",
        "parent_title": None,
        "body": """
# Lucky Wheel - Technical Spec Backend

## 1. API Design

### POST /api/v2/lucky-wheel/spin
Thực hiện 1 lượt quay.

**Request:**
```json
{
  "campaign_id": "LW_DGS_260520_585",
  "user_id": "user_123",
  "idempotency_key": "uuid-v4"
}
```

**Response (success):**
```json
{
  "result": "voucher",
  "reward_id": "voucher_cgv_2024",
  "reward_name": "Vé CGV 50k",
  "reward_type": "voucher",
  "turns_remaining": 3,
  "slot_index": 2
}
```

**Response (no turns):**
```json
{
  "error": "NO_TURNS_REMAINING",
  "turns_remaining": 0
}
```

### GET /api/v2/lucky-wheel/status
Trạng thái campaign + số lượt còn lại của user.

### POST /api/v2/lucky-wheel/claim
Xác nhận nhận quà (nếu `claim_required = true`).

---

## 2. Database Schema

```sql
-- Campaign config
CREATE TABLE lw_campaigns (
    id              VARCHAR(64) PRIMARY KEY,
    name            VARCHAR(200),
    start_at        DATETIME,
    end_at          DATETIME,
    status          ENUM('draft','active','paused','ended'),
    config_json     JSON,
    budget_total    BIGINT,
    budget_spent    BIGINT DEFAULT 0,
    budget_alert_50 TINYINT DEFAULT 0,
    budget_alert_75 TINYINT DEFAULT 0,
    budget_alert_95 TINYINT DEFAULT 0,
    created_at      DATETIME DEFAULT NOW()
);

-- Gift pools
CREATE TABLE lw_gifts (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    campaign_id     VARCHAR(64),
    gift_type       ENUM('voucher','xu','ticket','other'),
    name            VARCHAR(200),
    quantity_total  INT,
    quantity_left   INT,
    weight          DECIMAL(5,2),  -- probability weight %
    counter_per_user INT DEFAULT 0, -- 0 = unlimited
    pool_type       ENUM('weekly','campaign'),
    week_number     INT,
    active          TINYINT DEFAULT 1,
    INDEX idx_campaign (campaign_id),
    INDEX idx_pool (campaign_id, pool_type, active)
);

-- User turns ledger
CREATE TABLE lw_user_turns (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    campaign_id     VARCHAR(64),
    user_id         VARCHAR(64),
    turns           INT DEFAULT 0,
    source          VARCHAR(50),  -- 'welcome','task','purchase'
    created_at      DATETIME DEFAULT NOW(),
    expires_at      DATETIME,
    INDEX idx_user (campaign_id, user_id)
);

-- Spin history (audit)
CREATE TABLE lw_spin_history (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    campaign_id     VARCHAR(64),
    user_id         VARCHAR(64),
    gift_id         BIGINT,
    idempotency_key VARCHAR(64) UNIQUE,
    spun_at         DATETIME DEFAULT NOW(),
    claimed         TINYINT DEFAULT 0,
    INDEX idx_user_campaign (campaign_id, user_id)
);
```

---

## 3. Rate Limiting & Fraud Prevention

### Rate limits
- 1 spin/3 giây/user (Redis token bucket)
- 100 spins/phút/IP (circuit breaker)

### AUTO-TRIGGER + RISK CONFIRM rules
Một số payment trigger yêu cầu RISK CONFIRM trước khi credit lượt quay:
- **Chặn VietQR:** giao dịch VietQR không được credit (dễ giả mạo)
- **Chặn Apple Pay:** tương tự VietQR
- **Malicious user check:** user trong blacklist (từ Risk team) → block auto-trigger
- Logic: `if payment.method in BLOCKED_METHODS or user in RISK_BLACKLIST: skip_credit()`

### Idempotency
- Mỗi spin yêu cầu `idempotency_key` (UUID)
- Key lưu trong Redis 24h; duplicate request → trả về kết quả cũ

---

## 4. Budget Control

```python
def check_budget(campaign_id: str, gift_cost: int) -> bool:
    campaign = get_campaign(campaign_id)
    new_spent = campaign.budget_spent + gift_cost
    ratio = new_spent / campaign.budget_total
    if ratio >= 1.0:
        return False  # budget exhausted
    # Trigger alerts
    for threshold in [0.50, 0.75, 0.95]:
        if campaign.budget_spent / campaign.budget_total < threshold <= ratio:
            send_budget_alert(campaign_id, threshold)
    return True
```

---

## 5. Gift Distribution Algorithm

Weighted random selection với exclusion list:
```python
def pick_gift(campaign_id: str, user_id: str) -> Gift:
    # 1. Load available gifts (quantity > 0)
    gifts = get_available_gifts(campaign_id)
    # 2. Exclude gifts this user already received (if counter=1)
    user_received = get_user_received(campaign_id, user_id)
    eligible = [g for g in gifts if g.id not in user_received or g.counter_per_user == 0]
    # 3. Weighted random pick
    if not eligible:
        return get_default_gift(campaign_id)  # fallback: xu
    total_weight = sum(g.weight for g in eligible)
    r = random.uniform(0, total_weight)
    for g in eligible:
        r -= g.weight
        if r <= 0:
            return g
    return eligible[-1]
```
""",
    },
    {
        "space": GROW_SPACE,
        "title": "Lucky Wheel - Technical Spec Frontend",
        "parent_title": None,
        "body": """
# Lucky Wheel - Technical Spec Frontend

## 1. Architecture

- Framework: React Native (iOS/Android) + React Web (PWA fallback)
- State: Redux Toolkit
- Animation: Reanimated 3 (mobile), Framer Motion (web)

---

## 2. UI Flows

### 2.1 Luồng chính (Happy path)

```
Landing page
  └→ [Bấm "Quay ngay"] → Check eligibility
       ├→ [Đủ điều kiện] → Màn hình quay
       │    └→ [Bấm nút quay] → POST /api/v2/lucky-wheel/spin
       │         ├→ [Thành công] → Animation quay → Hiện kết quả popup
       │         │    ├→ [claim_required=false] → Auto nhận → Màn hình "Đã nhận quà"
       │         │    └→ [claim_required=true]  → Nút "Nhận quà" → POST /claim → Done
       │         └→ [Lỗi/hết lượt] → Error state
       └→ [Không đủ điều kiện] → Màn hình guide
```

### 2.2 Error states

| Lỗi | Hiển thị |
|---|---|
| NO_TURNS_REMAINING | Banner "Hết lượt quay — Hoàn thành task để nhận thêm" |
| CAMPAIGN_ENDED | Banner "Chương trình đã kết thúc" |
| BUDGET_EXHAUSTED | Banner "Phần thưởng tạm thời gián đoạn" |
| NETWORK_ERROR | Toast "Lỗi kết nối — thử lại" + retry button |
| DUPLICATE_SPIN | Trả về kết quả spin trước (idempotent) |

---

## 3. Animation Spec

```typescript
// Spin animation parameters (1-1 with PRD §2.1)
const SPIN_CONFIG = {
  minDuration: 3000,   // ms
  maxDuration: 5000,   // ms
  easing: 'cubic-bezier(0.17, 0.67, 0.12, 0.99)',
  minRotations: 5,     // full rotations before landing
  slotCount: 8,        // must match campaign config
}

// Prize highlight animation
const PRIZE_POPUP_DELAY = 500 // ms after spin stops
```

---

## 4. Deeplink Integration

| Deeplink scheme | Mô tả |
|---|---|
| `zalopay://gamification/lucky-wheel/{campaign_id}` | Mở trực tiếp màn hình Lucky Wheel |
| `zalopay://gamification/lucky-wheel/{campaign_id}/task/{task_id}` | Mở task cụ thể |
| `zalopay://scan` | Mở QR scanner |
| `zalopay://pay/{merchant_id}` | Mở thanh toán merchant |

Fallback: nếu deeplink không hỗ trợ → mở Web URL trong WebView.

---

## 5. Ads Banner Integration

Hiển thị 2 ads banner dưới vòng quay:
- Banner 1: `Ads ID 6845` — gọi `AdService.loadBanner(adsId: 6845, placement: 'lucky_wheel_bottom_1')`
- Banner 2: `Ads ID 6846` — gọi `AdService.loadBanner(adsId: 6846, placement: 'lucky_wheel_bottom_2')`

Banner dimensions: 320×50px (standard banner). Lazy load khi vào màn hình.

---

## 6. Task Card Component

```typescript
interface TaskCardProps {
  taskId: string
  segment: string
  title: string
  description: string
  reward: number        // số lượt quay
  frequency: 'daily' | 'weekly' | 'once' | 'campaign'
  ctaText: string
  deeplink: string
  webUrl: string
  logo: string          // URL CDN
  completed: boolean
  completionCount: number
}
```

Task card hiển thị: logo + title + reward badge + CTA button.
Khi `completed=true`: hiển thị checkmark, button disabled.

---

## 7. TnC Popup

- Hiển thị lần đầu tiên user mở campaign
- Scroll-to-bottom required trước khi enable "Đồng ý"
- Sau khi đồng ý: lưu `consent_{campaign_id}=true` trong AsyncStorage
- Nếu TnC thay đổi (version bump): reset consent, hiện lại popup
""",
    },
    {
        "space": GROW_SPACE,
        "title": "Lucky Wheel - QA Test Cases & Operation Guide",
        "parent_title": None,
        "body": """
# Lucky Wheel - QA Test Cases & Operation Guide

## Part 1: QA Test Cases

### 1.1 Happy Path

| ID | Test case | Expected |
|---|---|---|
| HP-01 | User đủ điều kiện mở campaign → bấm quay | Animation quay, hiện kết quả |
| HP-02 | User nhận welcome turn (2 lượt) lần đầu | Số lượt hiển thị = 2 |
| HP-03 | Hoàn thành task → nhận thêm lượt | Turns += reward của task |
| HP-04 | Quay hết tất cả lượt | Hiển thị "Hết lượt quay" |
| HP-05 | Quà weekly được thả đúng thứ Hai 10:00 | Quà mới xuất hiện trong pool |
| HP-06 | Nhận voucher → voucher xuất hiện trong ví | Voucher available trong 24h |
| HP-07 | RISK CONFIRM task (không dùng VietQR) | Credit đúng lượt quay |
| HP-08 | Budget alert 50% → email gửi đi | Email đến trong 5 phút |

### 1.2 Edge Cases

| ID | Test case | Expected |
|---|---|---|
| EC-01 | Double-spin cùng idempotency_key | Trả về kết quả lần 1, không spin lại |
| EC-02 | Quay khi slot hết hàng | Tự chuyển sang slot Xu |
| EC-03 | Tất cả quà hết | Banner "Đang bổ sung quà" |
| EC-04 | User trong blacklist Risk | Không credit turn từ auto-trigger |
| EC-05 | Giao dịch VietQR kích hoạt task | Không credit (blocked method) |
| EC-06 | Giao dịch Apple Pay kích hoạt task | Không credit (blocked method) |
| EC-07 | User quay đúng lúc campaign end | Lượt quay được dùng, kết quả hợp lệ |
| EC-08 | Budget 100% → cố quay | Error "Phần thưởng tạm thời gián đoạn" |
| EC-09 | Network timeout giữa chừng spin | Retry tự động, idempotency đảm bảo không dup |
| EC-10 | User counter=1 đã nhận quà đó rồi | Quà bị exclude khỏi pool khi pick |

### 1.3 Fraud Cases

| ID | Test case | Expected |
|---|---|---|
| FR-01 | 1 user gửi 10 spin/10 giây | Rate limit block từ request thứ 4 |
| FR-02 | 1 IP gửi 200 spin/phút | Circuit breaker kick in |
| FR-03 | Replay attack với idempotency_key cũ | Trả về kết quả cũ, không spin mới |

---

## Part 2: Operation Guide — Config Tool

### Bước 1: Tạo campaign mới
1. Vào `https://ops.zalopay.vn/lucky-wheel-config`
2. Click **"+ Tạo campaign"**
3. Điền: Campaign ID, tên, thời gian, budget tổng

### Bước 2: Cấu hình slot & tỉ lệ
1. Tab **"Vòng quay"** → Upload ảnh slot (8 slot, PNG 80×80px)
2. Nhập label cho từng slot (tối đa 16 ký tự)
3. Tab **"Tỉ lệ quà"** → Nhập weight % (tổng = 100%)
4. Tick **"Counter per user = 1"** cho các quà giá trị cao

### Bước 3: Cấu hình task
1. Tab **"Task list"** → Click **"+ Thêm task"**
2. Điền từng field (xem PRD §5.2 cho mô tả field)
3. Test task bằng cách nhập UserID test và simulate event

### Bước 4: Cấu hình budget alert
1. Tab **"Budget"** → Nhập email alert (1 email/dòng)
2. Tick các ngưỡng: 50%, 75%, 95%

### Bước 5: Preview & Publish
1. Click **"Preview"** → Kiểm tra vòng quay trên device test
2. Nhập UserID testing vào field **"Test users"**
3. Nếu OK → Click **"Publish"** → Campaign active

### Bước 6: Monitor
- Dashboard real-time: `https://ops.zalopay.vn/lucky-wheel-config/{campaign_id}/dashboard`
- Metrics: spins/hour, budget_spent%, gift_distribution, error_rate
""",
    },

    # ─── Risk Space ──────────────────────────────────────────────────────────
    {
        "space": RISK_SPACE,
        "title": "Risk SOP - Campaign Review",
        "parent_title": None,
        "body": """
# Risk SOP - Campaign Review

**Phiên bản:** 3.1
**Hiệu lực từ:** 01/01/2026
**Owner:** Risk Management Team

---

## 1. Mục đích

Quy trình này xác định các bước review và phê duyệt rủi ro cho tất cả chương trình khuyến mãi/campaign trước khi launch, đảm bảo tuân thủ chính sách Risk và kiểm soát chi phí.

---

## 2. Phạm vi áp dụng

Áp dụng cho tất cả campaign có **phát quà/voucher/xu** cho người dùng ZaloPay, bao gồm:
- Lucky Wheel, Scratch Card, Mini Game
- Cashback campaign
- Partnership promotion
- OTA (One-Time Award) campaign

---

## 3. Quy trình

### Bước 1: Biz Team gửi yêu cầu
- **SLA:** Tối thiểu 5 ngày làm việc trước ngày launch
- **Kênh:** Tạo Jira ticket trong project KAN, status = TO DO
- **Nội dung bắt buộc:**
  - Link Confluence đến Campaign Request Document (đầy đủ 8 mục)
  - MKT code + ví ID
  - Phê duyệt FA (Finance) cho ngân sách

### Bước 2: Chuyển sang RISK REVIEW
- Biz Team hoặc PM chuyển ticket sang RISK REVIEW
- Hệ thống (hoặc Risk Lead) assign cho reviewer phù hợp

### Bước 3: Risk Review (SLA: 1 ngày làm việc)
Reviewer đánh giá theo checklist 10 điểm:

| # | Tiêu chí | Mức độ |
|---|---|---|
| 1 | Ngân sách có FA approve | Critical |
| 2 | Giá trị quà/user theo policy | Critical |
| 3 | Không có restricted merchant | High |
| 4 | RISK CONFIRM rules đã khai báo | High |
| 5 | KYC tier requirement rõ ràng | High |
| 6 | Thời gian campaign xác định | Medium |
| 7 | Budget alert đã cấu hình | Medium |
| 8 | Task list & reward hợp lệ | Medium |
| 9 | Voucher config đầy đủ | Medium |
| 10 | UserID testing có | Low |

### Bước 4: Ra quyết định
- **PASS:** Tất cả tiêu chí comply → chuyển RISK DONE
- **PARTIAL_FAIL:** 1-2 tiêu chí Chưa rõ, không có Violate → chuyển RISK DONE kèm comment yêu cầu clarify trong 24h
- **FAIL:** Bất kỳ tiêu chí Critical/High nào Violate → chuyển NEEDS REVISION, Biz phải sửa và gửi lại

### Bước 5: Escalation
- Campaign có ngân sách > 500M VND: cần thêm Risk Lead sign-off
- Campaign với merchant/category mới chưa có precedent: consult Legal
- Không đồng thuận reviewer-Biz: escalate lên Risk Manager

---

## 4. SLA

| Bước | SLA |
|---|---|
| Biz gửi request | T-5 ngày làm việc trước launch |
| Risk review | T+1 ngày làm việc |
| Sửa đổi (nếu NEEDS REVISION) | T+1 ngày làm việc |
| Final approval | T+0.5 ngày làm việc |
""",
    },
    {
        "space": RISK_SPACE,
        "title": "Risk Principles - Promotion & Finance",
        "parent_title": None,
        "body": """
# Risk Principles - Promotion & Finance

**Phiên bản:** 2.0
**Owner:** Risk Management Team
**Approved by:** Chief Risk Officer

---

## 1. Nguyên tắc cơ bản về Promotion Risk

### 1.1 Giới hạn giá trị quà per-user
- Quà tặng trực tiếp (không phải discount): **tối đa 1,000,000 VND** giá trị thị trường/user/campaign
- Xu (ZaloPay coin): **tối đa 500 xu** (tương đương 500,000 VND)/user/campaign
- Vé sự kiện: theo giá niêm yết, không vượt **2,000,000 VND**/vé

### 1.2 Giới hạn tổng ngân sách
- Campaign < 100M VND: PM có thể tự approve
- Campaign 100M–500M VND: cần Finance (FA) approve
- Campaign > 500M VND: cần Risk Lead + CFO approve
- **Không có campaign nào được launch khi chưa có FA approve nếu ngân sách ≥ 100M VND**

### 1.3 Cấu hình bảo vệ chống lạm dụng (RISK CONFIRM)
**Bắt buộc** cho mọi campaign có auto-trigger dựa trên payment:
- Chặn VietQR: VietQR có thể bị tạo fake/reuse → không được dùng làm trigger
- Chặn Apple Pay: tương tự (chưa có fraud detection đủ mạnh)
- User blacklist check: users trong danh sách fraud/suspicious → không credit

Campaign không có RISK CONFIRM rules là **vi phạm chính sách** (Violate).

---

## 2. Merchant Category Policy

### 2.1 Danh mục bị cấm (PROHIBITED)
Không được hợp tác hoặc credit lượt cho giao dịch tại:
- Cờ bạc, casino, đặt cược
- Tiền điện tử, NFT, trading platform
- Adult content
- Rượu/bia (nếu không có phân loại tuổi)

### 2.2 Danh mục restricted (cần Risk pre-approval)
- Tài chính: vay tiền, BNPL, bảo hiểm
- Y tế, dược phẩm
- Giáo dục trực tuyến
- Nền tảng mới chưa có precedent

### 2.3 Danh mục approved
- OTA: Vé máy bay, tàu hỏa, xe khách, khách sạn
- F&B: nhà hàng, coffee
- Bán lẻ: thời trang, mỹ phẩm, siêu thị
- Entertainment: CGV, VinWonders, SunWorld, FUTA
- Telecom: nạp điện thoại, gói data

---

## 3. KYC Requirements

| Loại campaign | KYC minimum |
|---|---|
| Xu / reward coin | Basic verified |
| Voucher < 200k VND | Basic verified |
| Voucher 200k–1M VND | Basic verified + phone verified |
| Voucher > 1M VND / Vé sự kiện > 500k | Full KYC (CCCD verified) |
| Cashback trực tiếp | Full KYC |

Campaign không khai báo KYC tier là **Chưa rõ** (Unclear), phải được clarify.

---

## 4. Budget Alert (bắt buộc)

Mọi campaign phải cấu hình ít nhất ngưỡng alert **75%**. Khuyến nghị cả 3 ngưỡng: 50%, 75%, 95%.

Email alert phải có ít nhất 1 địa chỉ của Risk team.

Campaign không có budget alert là **vi phạm chính sách** (Violate).

---

## 5. Fraud Prevention Principles

### 5.1 Rate limiting
Mọi endpoint trigger lượt quay phải có:
- Per-user rate limit (tối thiểu 1 action/3s)
- Per-IP rate limit (tối thiểu 100 actions/phút)

### 5.2 Idempotency
Tất cả credit operations phải idempotent (có idempotency key).

### 5.3 Monitoring
Campaign phải được monitor real-time:
- Anomaly detection khi 1 user nhận > 10× average reward
- Alert khi error rate > 5%
""",
    },
    {
        "space": RISK_SPACE,
        "title": "Promotion Campaign Request Document",
        "parent_title": None,
        "body": """
# Promotion Campaign Request Document

Trang này là danh mục tổng hợp tất cả các Campaign Request Document đã được gửi đến Risk team để review.

## Hướng dẫn

Mỗi campaign tạo 1 child page theo định dạng:
`[DD/MM/YYYY][MKT_CODE][CAMPAIGN_TYPE][MÔ TẢ NGẮN]`

Ví dụ: `[20/05/2026][DGS_260520_585][LOT_RD_MPU_NW][OTA - Lucky Wheel Vé hè 0đ]`

## Danh sách campaigns

Xem các child page bên dưới.
""",
    },
    # The child page will be created after we get the parent page ID
]

# Child page (needs parent ID from page 7)
CAMPAIGN_REQUEST_CHILD = {
    "space": RISK_SPACE,
    "title": "[20/05/2026][DGS_260520_585][LOT_RD_MPU_NW][OTA - Lucky Wheel Vé hè 0đ]",
    "body": """
# [20/05/2026][DGS_260520_585][LOT_RD_MPU_NW][OTA - Lucky Wheel Vé hè 0đ]

---

## 1. THÔNG TIN CHUNG

| Field | Value |
|---|---|
| MKT_Name | OTA - Lucky Wheel Vé hè 0đ |
| MKT_Code | DGS_260520_585 |
| Tên chương trình | Lucky Wheel Vé hè 0đ |
| Thể lệ (Ads_id) | 8821 |
| Ngân sách tổng | 350,000,000 VND |
| Thời gian Testing | 05/06/2026 – 07/06/2026 |
| Thời gian Live | 08/06/2026 – 26/07/2026 (7 tuần) |

---

## 2. YÊU CẦU CẤU HÌNH CƠ BẢN

**Cảnh báo ngân sách:**
- 50% → email alert
- 75% → email alert (bắt buộc)
- 95% → email alert + Slack notify

**Email nhận alert:**
- phutt2@vng.com.vn
- risk-ops@vng.com.vn
- growthteam@vng.com.vn

**UserID testing:**
- 0901234567 (QA tester 1)
- 0912345678 (QA tester 2)
- 0923456789 (PM Trang)

---

## 3. YÊU CẦU CẤU HÌNH NÂNG CAO

### 3a. Điều kiện tham gia
- Cần visit landing: **CÓ** (user phải vào trang campaign trước)
- Cần bấm task trước khi quay: **KHÔNG** (có welcome turn)
- Tạo link & bật nút chia sẻ landing: **CÓ**
- Welcome turn: **2 lượt** khi lần đầu vào campaign

### 3b. User Profile / Segment
- Segment Mass (ID: 13155): tất cả user ZaloPay đã verify cơ bản
- KYC requirement: Basic verified

### 3c. Điều kiện nhận quà
- Cần bấm claim quà: **CÓ** (user bấm nút "Nhận quà" để xác nhận)

---

## 4. GAME UI

| Field | Value |
|---|---|
| Game Type | Lucky Wheel |
| UI Design Type | MKT gửi KV banner, yêu cầu team Gami adaptation |
| Link asset | https://sharepoint.vng.com.vn/sites/zalopay-mkt/luckywheelvehe2026 |
| Gami Title | Vòng Quay Vé Hè 0đ |

**8 slot icons trên vòng quay:**
1. Nha Trang (ảnh biển)
2. Dấu ? (mystery prize)
3. Đà Nẵng (cầu Rồng)
4. VinWonders (logo)
5. Đà Lạt (hoa)
6. Vietjet Air (logo)
7. Hải Phòng (Cát Bà)
8. FUTA (logo xe khách)

**Ads Banner dưới game:**
- Ads ID: 6845 (slot 1, 320×50px)
- Ads ID: 6846 (slot 2, 320×50px)

---

## 5. THÔNG TIN CẤU HÌNH - ĐIỀU KIỆN PHÁT QUÀ

### 5a. Trigger Type
- **AUTO-TRIGGER** với **RISK CONFIRM** rules:
  - Chặn VietQR payments
  - Chặn Apple Pay
  - Kiểm tra blacklist (malicious users từ Risk team)
  - Không credit lượt cho reversed/refunded transactions

### 5b. Segment & Điều kiện
**Segment Starter (ID: 13155):**
- Welcome: 2 lượt khi lần đầu vào campaign (cần visit landing)
- Task: Hoàn thành task → nhận thêm lượt (tối đa 5 lượt/ngày từ task)

### 5c. Pool quà
- Quà theo tuần: thả vào thứ Hai 10:00 hàng tuần (7 tuần, từ 09/06 – 21/07)
- Quà xuyên suốt chương trình (campaign pool)

---

## 6. TASK LIST (18 tasks)

| # | Segment | Title | Trigger type | Trigger condition | Reward | Frequency |
|---|---|---|---|---|---|---|
| 1 | Mass | Đặt vé máy bay | Payment | AppID: VJA_TICKET | 2 lượt | 1 lần/tuần |
| 2 | Mass | Đặt vé tàu hỏa | Payment | AppID: VNR_TICKET | 2 lượt | 1 lần/tuần |
| 3 | Mass | Đặt vé xe khách | Payment | AppID: VEXERE | 2 lượt | 1 lần/tuần |
| 4 | Mass | Tìm kiếm chuyến bay | FE Event | EventID: SEARCH_FLIGHT | 1 lượt | 1 lần/ngày |
| 5 | Mass | Đặt vé VinWonders | Payment | AppID: VW_TICKET | 3 lượt | 1 lần/tuần |
| 6 | Mass | Đặt vé SunWorld | Payment | AppID: SW_TICKET | 3 lượt | 1 lần/tuần |
| 7 | Mass | Đặt vé FUTA | Payment | AppID: FUTA_BUS | 2 lượt | 1 lần/tuần |
| 8 | Mass | Đặt trên Vexere | CPS | AppID: VEXERE_CPS | 2 lượt | 1 lần/tuần |
| 9 | Mass | Bay với Vietjet | Payment | AppID: VJA_DIRECT | 3 lượt | 1 lần/campaign |
| 10 | Mass | Chơi game H5 | FE Event | EventID: H5_GAME_COMPLETE | 1 lượt | 1 lần/ngày |
| 11 | Mass | Kiểm tra hóa đơn | Payment | AppID: BILL_PAYMENT | 1 lượt | 1 lần/tuần |
| 12 | Mass | Mua TikTok Shop | CPS | AppID: TIKTOK_SHOP | 1 lượt | 1 lần/tuần |
| 13 | Mass | Nạp điện thoại | Payment | AppID: TOPUP | 1 lượt | 1 lần/ngày |
| 14 | Mass | Đặt xe GreenSM | Payment | AppID: GREENSM | 2 lượt | 1 lần/tuần |
| 15 | Mass | Đặt vé phim | Payment | AppID: CINEMA | 2 lượt | 1 lần/tuần |
| 16 | Mass | Follow Fanpage | FE Event | EventID: FOLLOW_FB | 1 lượt | 1 lần/campaign |
| 17 | Mass | Đặt phòng khách sạn | Payment | AppID: HOTEL_BOOKING | 3 lượt | 1 lần/tuần |
| 18 | Mass | Mytour đặt tour | CPS | AppID: MYTOUR_CPS | 2 lượt | 1 lần/tuần |

---

## 7. TỈ LỆ CHIA THƯỞNG

### 7a. Quà theo tuần (7 tuần, 09/06 – 21/07/2026)

**Mỗi tuần thả (thứ Hai 10:00):**

| Item | Số lượng | Tỉ trọng (%) | Counter |
|---|---|---|---|
| CGV 2 vé | 50 | 1.0 | 1 lần/user |
| VTVGo 1 tháng | 100 | 2.0 | 1 lần/user |
| Nạp game 50k | 200 | 4.0 | 1 lần/user |
| Vé máy bay Đà Lạt 0đ | 20 | 0.4 | 1 lần/user |
| Vé máy bay Nha Trang 0đ | 20 | 0.4 | 1 lần/user |
| Vé máy bay Đà Nẵng 0đ | 20 | 0.4 | 1 lần/user |
| Vé máy bay Hải Phòng 0đ | 20 | 0.4 | 1 lần/user |
| Vé xe khách Nha Trang 0đ | 30 | 0.6 | 1 lần/user |
| Vé xe khách Đà Lạt 0đ | 30 | 0.6 | 1 lần/user |
| Vé tàu Đà Nẵng 0đ | 25 | 0.5 | 1 lần/user |
| Vé tàu Hải Phòng 0đ | 25 | 0.5 | 1 lần/user |
| Resort Nha Trang 0đ (2 ngày) | 5 | 0.1 | 1 lần/user |
| **100 xu (buffer)** | 50,000 | **89.6** | không giới hạn |

### 7b. Quà xuyên suốt (~35 items)

| Item | Số lượng | Tỉ trọng (%) |
|---|---|---|
| Vé máy bay Vietjet 199k | 500 | 1.0 |
| Phòng khách sạn Mytour 300k | 300 | 0.6 |
| Vé VinWonders 50% | 1000 | 2.0 |
| Vé SunWorld 30% | 1000 | 2.0 |
| Vé FUTA 100k | 2000 | 4.0 |
| Vé VEXERE 50k | 2000 | 4.0 |
| Grab Food 50k | 3000 | 6.0 |
| The Coffee House 30k | 3000 | 6.0 |
| Shopee Mart 20k | 5000 | 10.0 |
| Guardian 50k | 1000 | 2.0 |
| 10 xu | 100,000 | 62.4 |

---

## 8. REWARDS - CONFIG VOUCHER

| Tên quà | MKT Code | Số lượng | Ngân sách phụ | % giảm | Min order | Max discount | HSD | Điều kiện sử dụng |
|---|---|---|---|---|---|---|---|---|
| Vé máy bay Vietjet 199k | VJA_199K | 500 | 99,500,000 | Giảm còn 199k | Không | Không | 30 ngày | Đặt trực tiếp qua ZaloPay, tuyến nội địa |
| Vé VinWonders 50% | VW_50PCT | 1000 | 150,000,000 | 50% | 100,000 | 300,000 | 30 ngày | App ZaloPay, áp dụng 1 vé/booking |
| Voucher Grab Food 50k | GF_50K | 3000 | 150,000,000 | Giảm 50k | 100,000 | 50,000 | 14 ngày | GrabFood qua ZaloPay |
| Voucher The Coffee House 30k | TCH_30K | 3000 | 90,000,000 | Giảm 30k | 50,000 | 30,000 | 14 ngày | Quét QR tại cửa hàng |
| Voucher Guardian 50k | GRD_50K | 1000 | 50,000,000 | Giảm 50k | 200,000 | 50,000 | 30 ngày | Cửa hàng Guardian toàn quốc |

---

*Approve từ FA cho số lượng xu sử dụng: Đã được FA Nguyễn Minh Tuấn duyệt ngày 15/05/2026*
""",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _confluence_headers(settings) -> dict[str, str]:
    token = resolve_confluence_api_token(settings)
    import base64
    creds = base64.b64encode(
        f"{settings.confluence_email}:{token}".encode()
    ).decode()
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
    url = f"{base_url}/api/v2/pages?spaceId={space_id}&title={title}&limit=1"
    r = httpx.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    results = r.json().get("results") or []
    return results[0]["id"] if results else None


def _create_page(
    base_url: str,
    space_id: str,
    title: str,
    body_md: str,
    headers: dict,
    parent_id: str | None = None,
) -> str:
    """Create a Confluence page and return its page ID."""
    # Convert markdown to simple HTML for Confluence storage
    import re
    html = body_md
    # Convert headers
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    # Convert bold
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    # Convert code blocks
    html = re.sub(r"```[a-z]*\n(.*?)```", r"<code>\1</code>", html, flags=re.DOTALL)
    # Convert inline code
    html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)
    # Convert table rows - skip for now (complex)
    # Convert paragraph breaks
    html = re.sub(r"\n\n+", "</p><p>", html)
    html = f"<p>{html}</p>"

    payload: dict = {
        "type": "page",
        "title": title,
        "space": {"id": space_id},
        "body": {
            "storage": {
                "value": html,
                "representation": "storage",
            }
        },
    }
    if parent_id:
        payload["ancestors"] = [{"id": parent_id}]

    url = f"{base_url}/rest/api/content"
    r = httpx.post(url, headers=headers, json=payload, timeout=60)
    if r.status_code == 400 and "title already used" in r.text.lower():
        logger.warning("Page %r already exists — skipping creation", title)
        return ""
    r.raise_for_status()
    page_id = r.json()["id"]
    logger.info("Created page %r → %s", title, page_id)
    return page_id


def main():
    settings = get_settings()
    if not settings.confluence_base_url or not settings.confluence_email:
        logger.error("CONFLUENCE_BASE_URL and CONFLUENCE_EMAIL must be set in .env")
        sys.exit(1)

    base_url = settings.confluence_base_url.rstrip("/")
    headers = _confluence_headers(settings)

    # Get space IDs
    grow_space_id = _get_space_id(base_url, GROW_SPACE, headers)
    risk_space_id = _get_space_id(base_url, RISK_SPACE, headers)

    if not grow_space_id:
        logger.error("Space %r not found — create it first on Confluence", GROW_SPACE)
        sys.exit(1)
    if not risk_space_id:
        logger.error("Space %r not found — create it first on Confluence", RISK_SPACE)
        sys.exit(1)

    logger.info("Growth space ID: %s, Risk space ID: %s", grow_space_id, risk_space_id)

    # Create the 8 main pages (idempotent)
    page_ids: dict[str, str] = {}
    parent_doc_id: str | None = None

    space_id_map = {GROW_SPACE: grow_space_id, RISK_SPACE: risk_space_id}

    for page in PAGES:
        space_id = space_id_map[page["space"]]
        existing = _find_page_by_title(base_url, space_id, page["title"], headers)
        if existing:
            logger.info("Page %r already exists (id=%s) — skipping", page["title"], existing)
            page_ids[page["title"]] = existing
        else:
            pid = _create_page(base_url, space_id, page["title"], page["body"], headers)
            if pid:
                page_ids[page["title"]] = pid

        if page["title"] == "Promotion Campaign Request Document":
            parent_doc_id = page_ids.get(page["title"])

    # Create child page (campaign request)
    child_title = CAMPAIGN_REQUEST_CHILD["title"]
    existing_child = _find_page_by_title(base_url, risk_space_id, child_title, headers)
    if existing_child:
        logger.info("Child page %r already exists (id=%s) — skipping", child_title, existing_child)
        child_page_id = existing_child
    else:
        child_page_id = _create_page(
            base_url, risk_space_id, child_title,
            CAMPAIGN_REQUEST_CHILD["body"], headers,
            parent_id=parent_doc_id,
        )
    page_ids[child_title] = child_page_id

    # Build the Confluence URL for the child page
    confluence_url = f"{base_url}/pages/viewpage.action?pageId={child_page_id}"

    # Create Jira ticket
    jira = JiraClient(settings)
    if not jira.configured():
        logger.error("Jira not configured — skipping ticket creation")
        result = {"pages": page_ids, "jira_key": None}
    else:
        description = f"""Dear chị Quỳnh. Nguyễn Duy Phương,

cc chị Ly. Lương Thảo Thủy. Võ Thị Thanh. Thư. Tạ Lê Anh

Em gửi plan set-up CT [20/05/2026][DGS_260520_585][LOT_RD_MPU_NW][OTA - Lucky Wheel Vé hè 0đ] theo các thông tin như sau:

MKT code:      DGS_260520_585
Ví ID:         Non Wallet
Confluence:    {confluence_url}

Nhờ chị Quỳnh xem và setup CT giúp em ạ

Cảm ơn chị nhiều.
PhuTT2

Approve từ FA cho số lượng xu sử dụng: Đã được FA Nguyễn Minh Tuấn duyệt ngày 15/05/2026"""

        ticket = jira.create_issue(
            summary="[20/05/2026][DGS_260520_585][LOT_RD_MPU_NW][OTA - Lucky Wheel Vé hè 0đ]",
            description=description,
            issuetype="Task",
        )
        ticket_key = ticket.get("key", "")
        logger.info("Created Jira ticket: %s", ticket_key)

        # Label the ticket for the in-code workflow
        if ticket_key and ticket_key != "DRY-RUN":
            jira.add_labels(key=ticket_key, labels=[WF_LABEL])
            logger.info("Added label %r to ticket %s", WF_LABEL, ticket_key)

        result = {
            "pages": page_ids,
            "jira_key": ticket_key,
            "confluence_url": confluence_url,
        }

    print(f"\nDEMO_CONTENT={json.dumps(result, ensure_ascii=False, indent=2)}")
    logger.info("Done! Confluence pages: %d, Jira: %s", len(page_ids), result.get("jira_key"))


if __name__ == "__main__":
    main()
