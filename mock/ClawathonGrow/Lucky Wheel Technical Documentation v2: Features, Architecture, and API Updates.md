# Lucky Wheel – Technical Documentation v2

> **Audience:** Backend & Frontend Developer  
> **Stack:** Java/Spring (BE), React/Next.js (FE tool), Native App (end user)  
> **Version:** 2.0  

---

## Changelog v2

| Thay đổi | Mô tả |
|---|---|
| `wheel_type` field | Campaign có thêm trường phân loại mechanic |
| Slot Machine engine | Random engine riêng: reel × symbol × combo mapping |
| Scratch Card engine | Pre-determined result, cell layout, match bonus |
| Pity system | Per-user counter, BOOST / GUARANTEED mode |
| A/B variant routing | User-campaign variant assignment, tách pool |
| Streak tracking | Daily activity check, grace period, milestone reward |
| Analytics API | Aggregated metrics endpoint cho dashboard |
| Slot count: 6/10 thêm | Wheel renderer hỗ trợ thêm 2 kích cỡ |

---

## 1. Kiến trúc v2

```
┌────────────────────┐     ┌──────────────────────┐
│   Config Tool (Web)│     │   End User App        │
│   + Analytics Tab  │     │   (Native iOS/Android)│
└────────┬───────────┘     └──────────┬────────────┘
         │                            │
         ▼                            ▼
┌─────────────────────────────────────────────────────┐
│              Lucky Wheel Service v2 (Java/Spring)   │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Spin Engine │  │ Pity Engine  │  │ A/B Router │ │
│  │ - Wheel     │  │ - Counter    │  │ - Assign   │ │
│  │ - SlotMach  │  │ - Boost calc │  │ - Sticky   │ │
│  │ - Scratch   │  └──────────────┘  └────────────┘ │
│  └─────────────┘                                    │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │ Streak Svc   │  │ Analytics    │                 │
│  │ - Daily check│  │ - Aggregator │                 │
│  │ - Grace period│ └──────────────┘                 │
│  └──────────────┘                                   │
└──────┬──────────────────────────┬───────────────────┘
       │                          │
       ▼                          ▼
┌─────────────┐         ┌──────────────────┐
│  Reward Svc │         │  Task / Segment  │
│             │         │  / Notif Service │
└─────────────┘         └──────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  MySQL + Redis + (Data WH)   │
└──────────────────────────────┘
```

---

## 2. Data Model bổ sung v2

### 2.1 Campaign – thêm fields

```sql
campaigns (bổ sung v2)
├── wheel_type          ENUM(LUCKY_WHEEL, SLOT_MACHINE, SCRATCH_CARD)  DEFAULT LUCKY_WHEEL
├── ab_enabled          BOOLEAN DEFAULT FALSE
├── ab_variant_a_pool   BIGINT FK → reward_pools NULL
├── ab_variant_b_pool   BIGINT FK → reward_pools NULL
├── ab_traffic_a_pct    INT DEFAULT 50            -- % traffic vào variant A
├── pity_enabled        BOOLEAN DEFAULT FALSE
├── pity_config         JSON NULL                 -- xem §2.4
├── streak_enabled      BOOLEAN DEFAULT FALSE
└── streak_config       JSON NULL                 -- xem §2.5
```

### 2.2 Slot Machine Config (trong ui_config JSON)

```json
"slot_machine": {
  "reel_count": 3,
  "line_count": 1,
  "symbols": [
    { "id": "cherry", "icon_url": "...", "weight": 30 },
    { "id": "lemon",  "icon_url": "...", "weight": 25 },
    { "id": "seven",  "icon_url": "...", "weight": 5  }
  ],
  "combo_rewards": [
    { "pattern": ["cherry","cherry","cherry"], "reward_type": "JACKPOT", "reward_value": {} },
    { "pattern": ["lemon","lemon","lemon"],    "reward_type": "COIN",    "reward_value": {"amount": 500} },
    { "pattern": ["cherry","cherry","*"],      "reward_type": "COIN",    "reward_value": {"amount": 50} },
    { "pattern": ["*","*","*"],               "reward_type": "MISS",    "reward_value": {} }
  ]
}
```

> `"*"` = wildcard (bất kỳ symbol nào). Pattern match theo thứ tự từ trên xuống, first-match wins.

### 2.3 Scratch Card Config (trong ui_config JSON)

```json
"scratch_card": {
  "cell_count": 6,
  "card_background_url": "...",
  "scratch_overlay_color": "#AAAAAA",
  "match_bonus_enabled": true,
  "match_bonus_threshold": 3,
  "match_bonus_reward": { "reward_type": "COIN", "reward_value": {"amount": 200} }
}
```

### 2.4 Pity Config (JSON column)

```json
{
  "threshold": 10,
  "mode": "GUARANTEED",
  "boost_percent": 20,
  "reset_on_win": true,
  "guaranteed_tier": "EPIC"
}
```

### 2.5 Streak Config (JSON column)

```json
{
  "reset_on_miss": true,
  "grace_period_hours": 30,
  "milestones": [
    { "day": 1,  "token_bonus": 1 },
    { "day": 3,  "token_bonus": 3 },
    { "day": 7,  "token_bonus": 10 },
    { "day": 14, "token_bonus": 25 }
  ]
}
```

### 2.6 Bảng mới: User Variant Assignment

```sql
user_campaign_variants
├── user_id         BIGINT
├── campaign_id     BIGINT FK
├── variant         ENUM(A, B)
├── assigned_at     TIMESTAMP
PRIMARY KEY (user_id, campaign_id)
```

### 2.7 Bảng mới: User Pity Counter

```sql
user_pity_counters
├── user_id             BIGINT
├── campaign_id         BIGINT FK
├── miss_streak         INT DEFAULT 0       -- số lần trượt liên tiếp
├── total_pity_triggers INT DEFAULT 0       -- số lần pity đã kích hoạt
├── last_updated        TIMESTAMP
PRIMARY KEY (user_id, campaign_id)
```

### 2.8 Bảng mới: User Streak

```sql
user_streaks
├── user_id             BIGINT
├── campaign_id         BIGINT FK
├── current_streak      INT DEFAULT 0
├── longest_streak      INT DEFAULT 0
├── last_activity_date  DATE
├── next_deadline       TIMESTAMP           -- deadline để giữ streak (có grace period)
PRIMARY KEY (user_id, campaign_id)
```

---

## 3. Spin Engine v2 – Logic theo wheel_type

### 3.1 LUCKY_WHEEL (giữ nguyên v1 + pity)

```java
RewardItem result = weightedRandom(availableItems, pityBoostIfEnabled);
// Nếu pity BOOST mode: tăng weight của tier cao sau mỗi miss
// Nếu pity GUARANTEED mode: override result sau N lần miss liên tiếp
pityEngine.update(userId, campaignId, result);
```

### 3.2 SLOT_MACHINE

```java
public SlotResult spinSlotMachine(Long campaignId, Long userId) {
    SlotMachineConfig cfg = campaign.getSlotMachineConfig();
    
    // 1. Spin từng reel độc lập
    List<String> reelResults = new ArrayList<>();
    for (int i = 0; i < cfg.getReelCount(); i++) {
        reelResults.add(weightedRandomSymbol(cfg.getSymbols()));
    }
    
    // 2. Match combo (first-match wins)
    ComboReward matched = matchCombo(reelResults, cfg.getComboRewards());
    
    // 3. Apply pity nếu result là MISS
    if (matched.getRewardType() == MISS) {
        pityEngine.recordMiss(userId, campaignId);
        matched = pityEngine.maybeOverride(userId, campaignId, matched);
    } else {
        pityEngine.recordWin(userId, campaignId);
    }
    
    return new SlotResult(reelResults, matched);
}
```

### 3.3 SCRATCH_CARD

```java
public ScratchCard generateCard(Long campaignId, Long userId) {
    ScratchCardConfig cfg = campaign.getScratchCardConfig();
    
    // 1. Chọn reward trước (pre-determined)
    RewardItem mainReward = weightedRandom(pool.getItems());
    
    // 2. Tạo layout cell
    // Cell count - 1 ô chứa reward thật, còn lại filler
    List<CellContent> cells = layoutCells(cfg.getCellCount(), mainReward);
    
    // 3. Nếu match bonus enabled: kiểm tra xem có match 3 không
    // (layout engine có thể tạo match hoặc không tùy RNG)
    boolean hasMatch = tryCreateMatch(cells, cfg);
    
    // Lưu card vào DB trước khi trả về (user phải cào đúng card này)
    return scratchCardRepo.save(new ScratchCard(userId, campaignId, cells, mainReward, hasMatch));
}
```

> **Lưu ý:** Card được generate và lưu DB trước khi user cào. Khi user reveal xong → gọi API claim. Tránh case user cancel giữa chừng rồi retry để "chọn kết quả tốt hơn".

---

## 4. A/B Router

```java
public RewardPool resolvePool(Long userId, Long campaignId) {
    Campaign campaign = campaignRepo.findById(campaignId);
    if (!campaign.isAbEnabled()) return campaign.getDefaultPool();
    
    // Sticky assignment: lấy variant đã assign, hoặc assign mới
    UserVariant variant = variantRepo.findOrAssign(userId, campaignId, () -> {
        // Random theo traffic split
        return Math.random() * 100 < campaign.getAbTrafficAPct() ? Variant.A : Variant.B;
    });
    
    return variant == Variant.A
        ? campaign.getVariantAPool()
        : campaign.getVariantBPool();
}
```

---

## 5. Pity Engine

```java
public class PityEngine {

    public RewardItem maybeOverride(Long userId, Long campaignId, RewardItem current) {
        PityConfig cfg = campaign.getPityConfig();
        UserPityCounter counter = pityRepo.get(userId, campaignId);
        
        if (cfg.getMode() == GUARANTEED && counter.getMissStreak() >= cfg.getThreshold()) {
            return pickGuaranteedTier(cfg.getGuaranteedTier(), pool);
        }
        return current;
    }
    
    public List<RewardItem> applyBoost(List<RewardItem> items, UserPityCounter counter, PityConfig cfg) {
        if (cfg.getMode() != BOOST || counter.getMissStreak() == 0) return items;
        double boostMultiplier = 1 + (cfg.getBoostPercent() / 100.0 * counter.getMissStreak());
        // Tăng weight các item tier cao, giữ nguyên MISS
        return items.stream().map(item ->
            item.getTier() == Tier.HIGH
                ? item.withWeight((int)(item.getWeight() * boostMultiplier))
                : item
        ).toList();
    }
    
    public void recordResult(Long userId, Long campaignId, RewardItem result) {
        if (result.getRewardType() == MISS || result.getTier() == Tier.LOW) {
            pityRepo.incrementMissStreak(userId, campaignId);
        } else {
            pityRepo.resetMissStreak(userId, campaignId);
        }
    }
}
```

---

## 6. Streak Service

```java
public void recordActivity(Long userId, Long campaignId) {
    UserStreak streak = streakRepo.findOrCreate(userId, campaignId);
    StreakConfig cfg = campaign.getStreakConfig();
    LocalDate today = LocalDate.now(ZoneId.of("Asia/Ho_Chi_Minh"));
    
    if (streak.getLastActivityDate() == null) {
        // Ngày đầu tiên
        streak.setCurrentStreak(1);
    } else if (today.equals(streak.getLastActivityDate())) {
        // Đã activity hôm nay rồi → không tính thêm
        return;
    } else if (isWithinGracePeriod(streak.getNextDeadline())) {
        streak.setCurrentStreak(streak.getCurrentStreak() + 1);
    } else {
        // Miss streak
        streak.setCurrentStreak(cfg.isResetOnMiss() ? 1 : streak.getCurrentStreak());
    }
    
    streak.setLastActivityDate(today);
    streak.setNextDeadline(computeDeadline(today, cfg.getGracePeriodHours()));
    streakRepo.save(streak);
    
    // Check milestone và phát token
    checkAndIssueMilestoneBonus(userId, campaignId, streak.getCurrentStreak(), cfg);
}
```

---

## 7. API bổ sung v2

### End User App

```
GET  /api/v1/lucky-wheel/{campaign_id}/streak
     → { current_streak, next_milestone_day, next_milestone_bonus, next_deadline }

GET  /api/v1/lucky-wheel/{campaign_id}/card/{card_id}
     → Lấy scratch card đã generate (dùng khi user cần resume)

POST /api/v1/lucky-wheel/{campaign_id}/card/{card_id}/claim
     → Sau khi user cào xong, claim reward
```

### Internal Config Tool

```
GET  /internal/v1/campaigns/{id}/analytics
     Query params: from, to, granularity (DAY/HOUR)
     → { spin_counts[], reward_distribution{}, token_flow{}, task_completion{}, ab_comparison{} }

GET  /internal/v1/campaigns/{id}/analytics/export
     → CSV file

GET  /internal/v1/campaigns/{id}/streak-stats
     → Distribution user theo streak day

POST /internal/v1/campaigns/{id}/ab-config
     → Cập nhật traffic split (chỉ cho phép khi campaign DRAFT)
```

---

## 8. Caching bổ sung v2

| Data | Cache | TTL |
|---|---|---|
| User variant assignment | Redis | Permanent trong campaign (không expire) |
| User pity counter | Redis | 10 phút (write-through) |
| User streak | Redis | 1 giờ |
| Analytics aggregated (hourly) | Redis | 10 phút |
| Scratch card pending | Redis | 10 phút (user phải claim hoặc expire) |

---

## 9. Lưu ý triển khai

- **Variant assignment là immutable:** Một khi user được assign A hoặc B, không đổi lại dù campaign bị edit. Nếu Ops muốn thay đổi traffic split, chỉ áp dụng cho user chưa được assign.
- **Scratch card expire:** Card chưa được claim sau 10 phút bị mark EXPIRED. User không thể claim card cũ. Spin tiếp theo generate card mới (token đã bị trừ từ lúc generate).
- **Streak timezone:** Luôn tính theo `Asia/Ho_Chi_Minh`. Day boundary = 00:00 VN.
- **Analytics là eventual consistent:** Aggregation chạy theo batch mỗi 5 phút, không realtime theo từng spin.
- **Pity không áp dụng cross-campaign:** Counter reset về 0 khi campaign mới bắt đầu, dù user clone sang campaign khác.
- **Slot machine combo matching:** Test kỹ wildcard pattern — đảm bảo pattern `["*","*","*"]` (fallback MISS) luôn là cuối cùng trong danh sách combo_rewards.
