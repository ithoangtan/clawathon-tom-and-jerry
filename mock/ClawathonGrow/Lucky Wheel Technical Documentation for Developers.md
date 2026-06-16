# Lucky Wheel – Technical Documentation

> **Audience:** Backend & Frontend Developer  
> **Stack:** Java/Spring (BE), React/Next.js (FE tool), Native App (end user)  
> **Version:** 1.0

---

## 1. Kiến trúc tổng quan

```
┌────────────────────┐     ┌──────────────────────┐
│   Config Tool (Web)│     │   End User App        │
│   (Ops dùng)       │     │   (Native iOS/Android)│
└────────┬───────────┘     └──────────┬────────────┘
         │                            │
         ▼                            ▼
┌─────────────────────────────────────────────────┐
│              Lucky Wheel Service (Java/Spring)  │
│  - Campaign CRUD                                │
│  - Config management                            │
│  - Spin logic + Random engine                   │
│  - Token ledger                                 │
│  - Task tracking                                │
└──────┬──────────────────────────┬───────────────┘
       │                          │
       ▼                          ▼
┌─────────────┐         ┌──────────────────┐
│  Reward Svc │         │  Task / Segment  │
│  (phát thưởng)│        │  Service         │
└─────────────┘         └──────────────────┘
       │
       ▼
┌─────────────┐
│  Database   │
│  (MySQL /   │
│   PostgreSQL│
│  + Redis)   │
└─────────────┘
```

---

## 2. Data Model

### 2.1 Campaign

```sql
campaigns
├── id                    BIGINT PK
├── name                  VARCHAR(255)           -- internal name
├── status                ENUM(DRAFT, SCHEDULED, ACTIVE, ENDED)
├── start_time            TIMESTAMP
├── end_time              TIMESTAMP
├── currency_type         VARCHAR(50)            -- loại token: EGG, COIN, TICKET...
├── ui_config             JSON                   -- toàn bộ UI config (xem §3)
├── spin_config           JSON                   -- cấu hình nút spin, giới hạn...
├── reward_pool_id        BIGINT FK → reward_pools
├── tnc_content           TEXT                   -- HTML hoặc plain text
├── tnc_display_type      ENUM(POPUP, BOTTOM_SHEET)
├── segment_rule          JSON                   -- rule phân luồng user
├── created_at            TIMESTAMP
└── updated_at            TIMESTAMP
```

### 2.2 Reward Pool

```sql
reward_pools
├── id                    BIGINT PK
├── campaign_id           BIGINT FK
├── name                  VARCHAR(255)
├── pool_type             ENUM(REPLACEABLE, NON_REPLACEABLE)
└── guaranteed_after_n    INT NULL               -- trúng chắc sau N lần, NULL = không dùng

reward_items
├── id                    BIGINT PK
├── pool_id               BIGINT FK
├── reward_type           ENUM(COIN, VOUCHER, ITEM, JACKPOT, MISS)
├── reward_value          JSON                   -- {amount: 1000} hoặc {voucher_code_pool_id: 5}
├── weight                INT                    -- xác suất tương đối
├── stock                 INT NULL               -- NULL = unlimited
├── remaining_stock       INT NULL               -- track realtime (Redis recommended)
├── slot_index            INT                    -- gắn với slot nào trên wheel (0-based)
├── icon_url              VARCHAR(500)
└── label                 VARCHAR(100)
```

### 2.3 Spin Token Ledger

```sql
user_token_ledger
├── id                    BIGINT PK
├── user_id               BIGINT
├── campaign_id           BIGINT FK
├── delta                 INT                    -- dương: cộng, âm: trừ
├── source                ENUM(TASK, PURCHASE, GIFT, SPIN)
├── ref_id                VARCHAR(100) NULL      -- task_id hoặc purchase_id
└── created_at            TIMESTAMP

-- View / query: SUM(delta) WHERE user_id AND campaign_id = số token hiện tại
```

### 2.4 Spin History

```sql
spin_history
├── id                    BIGINT PK
├── user_id               BIGINT
├── campaign_id           BIGINT FK
├── reward_item_id        BIGINT FK
├── spin_count_at_time    INT                    -- user đã quay bao nhiêu lần trước spin này
├── reward_issued         BOOLEAN
├── idempotency_key       VARCHAR(100) UNIQUE    -- tránh double spin
└── created_at            TIMESTAMP
```

### 2.5 Task

```sql
campaign_tasks
├── id                    BIGINT PK
├── campaign_id           BIGINT FK
├── title                 VARCHAR(255)
├── description           TEXT
├── icon_url              VARCHAR(500)
├── action_deeplink       VARCHAR(500)           -- deeplink khi user bấm vào task
├── token_reward          INT                    -- số token nhận khi hoàn thành
├── completion_condition  JSON                   -- điều kiện check (gọi Task Service)
├── reset_type            ENUM(ONE_TIME, DAILY)
└── sort_order            INT
```

---

## 3. UI Config JSON Schema

Toàn bộ `ui_config` trong bảng `campaigns` theo cấu trúc:

```json
{
  "background": {
    "image_url": "https://cdn.example.com/bg.png",
    "color": "#3A0050",
    "overlay_opacity": 0.4
  },
  "title": {
    "text": "Easter Lucky Wheel",
    "font_size": 28,
    "color": "#FFD700",
    "bold": true
  },
  "countdown_timer": {
    "enabled": true,
    "label": "Ends in:",
    "color": "#FFFFFF"
  },
  "wheel": {
    "background_image_url": "https://cdn.example.com/wheel.png",
    "pointer_image_url": "https://cdn.example.com/pointer.png",
    "spin_duration_ms": 4000,
    "min_rotations": 5
  },
  "token_display": {
    "icon_url": "https://cdn.example.com/egg.png",
    "color": "#FF8800"
  },
  "buttons": {
    "spin_one": {
      "label": "Spin",
      "cost": 1,
      "background_color": "#4CAF50",
      "text_color": "#FFFFFF"
    },
    "spin_ten": {
      "label": "Spin 10",
      "cost": 10,
      "background_color": "#FFC107",
      "text_color": "#000000"
    },
    "shop": {
      "label": "Shop",
      "icon_url": "https://cdn.example.com/shop.png",
      "action_type": "DEEPLINK",
      "action_value": "zalopay://shop/token"
    },
    "task": {
      "label": "Tasks",
      "action_type": "DEEPLINK",
      "action_value": "zalopay://lucky-wheel/tasks"
    }
  },
  "popups": {
    "reward": {
      "background_image_url": "https://cdn.example.com/reward-popup-bg.png",
      "title": "Chúc mừng!",
      "claim_button_label": "Nhận thưởng",
      "claim_action_type": "CLOSE"
    },
    "out_of_token": {
      "title": "Hết lượt rồi!",
      "description": "Làm nhiệm vụ để có thêm lượt quay nhé.",
      "cta_label": "Làm nhiệm vụ",
      "cta_action_type": "DEEPLINK",
      "cta_action_value": "zalopay://lucky-wheel/tasks"
    },
    "error": {
      "title": "Có lỗi xảy ra",
      "description": "Vui lòng thử lại.",
      "cta_label": "Thử lại",
      "cta_action_type": "RETRY"
    }
  },
  "tnc": {
    "content": "<p>Điều khoản áp dụng...</p>",
    "display_type": "BOTTOM_SHEET",
    "trigger_label": "Điều khoản & Điều kiện"
  }
}
```

---

## 4. API Endpoints

### 4.1 Phía End User App

```
GET  /api/v1/lucky-wheel/active
     → Trả về campaign active mà user thuộc segment
     → Response: campaign_id, ui_config, spin_config, task_list (summary), token_balance

GET  /api/v1/lucky-wheel/{campaign_id}/config
     → Chi tiết config để render UI (dùng khi app cần reload)

GET  /api/v1/lucky-wheel/{campaign_id}/token-balance
     → Số token hiện tại của user trong campaign

POST /api/v1/lucky-wheel/{campaign_id}/spin
     Body: { "count": 1 | 10, "idempotency_key": "uuid" }
     → Trả về: reward_item, animation_stop_slot, remaining_token

GET  /api/v1/lucky-wheel/{campaign_id}/tasks
     → Danh sách task, trạng thái hoàn thành của user

POST /api/v1/lucky-wheel/{campaign_id}/tasks/{task_id}/claim
     → User claim token sau khi hoàn thành task
```

### 4.2 Phía Config Tool (Internal)

```
GET    /internal/v1/campaigns               -- danh sách tất cả campaign
POST   /internal/v1/campaigns               -- tạo campaign mới
GET    /internal/v1/campaigns/{id}          -- lấy full config
PUT    /internal/v1/campaigns/{id}          -- cập nhật config
PATCH  /internal/v1/campaigns/{id}/status   -- đổi trạng thái (DRAFT → SCHEDULED...)
DELETE /internal/v1/campaigns/{id}          -- xóa (chỉ DRAFT)
POST   /internal/v1/campaigns/{id}/clone    -- nhân bản campaign

GET    /internal/v1/campaigns/{id}/reward-pools
POST   /internal/v1/campaigns/{id}/reward-pools
PUT    /internal/v1/campaigns/{id}/reward-pools/{pool_id}

GET    /internal/v1/campaigns/{id}/spin-history   -- log lịch sử quay
GET    /internal/v1/campaigns/{id}/stats          -- thống kê: spin count, reward distribution
```

---

## 5. Spin Logic (Random Engine)

```java
// Pseudo-code
public RewardItem spin(Long campaignId, Long userId) {
    // 1. Kiểm tra token
    int balance = tokenLedger.getBalance(userId, campaignId);
    if (balance < 1) throw new InsufficientTokenException();

    // 2. Lấy pool, lọc item còn stock
    List<RewardItem> availableItems = rewardPool.getAvailableItems(campaignId);

    // 3. Kiểm tra guaranteed reward
    int spinCount = spinHistory.countByUser(userId, campaignId);
    Campaign campaign = campaignRepo.findById(campaignId);
    if (campaign.getGuaranteedAfterN() != null
        && spinCount % campaign.getGuaranteedAfterN() == 0) {
        return pickGuaranteedReward(availableItems);
    }

    // 4. Weight-based random
    RewardItem selected = weightedRandom(availableItems);

    // 5. Trừ stock nếu non-unlimited (Redis atomic decrement)
    if (selected.getStock() != null) {
        boolean decremented = stockService.decrement(selected.getId());
        if (!decremented) {
            // Fallback: pick lại không có item này
            return spin(campaignId, userId); // hoặc pick fallback item
        }
    }

    // 6. Ghi ledger + history
    tokenLedger.debit(userId, campaignId, 1, Source.SPIN);
    spinHistory.save(userId, campaignId, selected.getId(), spinCount + 1);

    // 7. Phát thưởng async
    rewardService.issueAsync(userId, selected);

    return selected;
}
```

**Lưu ý quan trọng:**
- Dùng `idempotency_key` để tránh double spin do retry
- `stockService.decrement` dùng Redis `DECR` với check `>= 0` để tránh race condition
- Phát thưởng async qua queue, không block response spin

---

## 6. Caching Strategy

| Data | Cache | TTL |
|---|---|---|
| Campaign UI config | Redis | 5 phút (invalidate khi Ops save) |
| User token balance | Redis | 30 giây (eventual consistency ok) |
| Reward item remaining stock | Redis | Realtime (DECR atomic) |
| Task completion status | Redis | 1 phút |
| Active campaign per user | Redis | 2 phút |

---

## 7. Source Code Structure (đề xuất)

```
lucky-wheel-service/
├── api/
│   ├── user/          -- controller cho end user app
│   └── internal/      -- controller cho config tool
├── domain/
│   ├── campaign/      -- Campaign entity, repo, service
│   ├── reward/        -- RewardPool, RewardItem, RandomEngine
│   ├── spin/          -- SpinService, SpinHistory
│   ├── token/         -- TokenLedger
│   └── task/          -- Task entity, completion check
├── infra/
│   ├── persistence/   -- JPA repositories
│   ├── cache/         -- Redis adapter
│   └── messaging/     -- async reward queue
└── config/
    └── UIConfigParser -- deserialize/validate JSON config
```

---

## 8. Các điểm cần lưu ý khi phát triển

- **UI config validation**: khi Ops save config, BE phải validate JSON schema đầy đủ trước khi cho phép ACTIVE
- **Stock race condition**: luôn dùng Redis atomic operation, không dùng SQL `UPDATE stock = stock - 1`
- **Idempotency**: mọi API spin đều phải check `idempotency_key` để tránh tính phí 2 lần khi app retry
- **Timezone**: `start_time` và `end_time` lưu UTC, hiển thị convert theo timezone user
- **Config tool vs app API**: tách riêng, internal API không qua API Gateway public
- **Preview**: config tool gọi internal API để render preview, không ảnh hưởng data live
