# PRD – Lucky Wheel Campaign v2

> **Audience:** Product Owner  
> **Version:** 2.0  
> **Prev version:** 1.0  
> **Status:** Living document

---

## Changelog v2

| # | Tính năng mới | Loại |
|---|---|---|
| F1 | **Wheel Type mới: Slot Machine** | 🆕 New Feature |
| F2 | **Wheel Type mới: Scratch Card** | 🆕 New Feature |
| F3 | **Pity System (Tăng xác suất lũy tiến)** | 🆕 New Feature |
| F4 | **A/B Testing cho Reward Pool** | 🆕 New Feature |
| F5 | **Streak Bonus (Chuỗi ngày đăng nhập quay)** | 🆕 New Feature |
| F6 | **Campaign Analytics Dashboard** | 🆕 New Feature |
| U1 | Slot count: mở rộng hỗ trợ 6 / 8 / 10 / 12 | ✏️ Updated |
| U2 | Task condition: hỗ trợ combo & dependent task | ✏️ Updated |

---

## 1. Tổng quan

Lucky Wheel v2 mở rộng từ "vòng quay đơn thuần" thành **Mini-Game Platform** hỗ trợ nhiều loại game mechanic. Ops team có thể chọn wheel type khi tạo campaign, mỗi type có UI và reward logic riêng nhưng dùng chung infrastructure (token, task, pool, segment).

### Mục tiêu v2

- Tránh nhàm chán: 2 game type mới thay đổi trải nghiệm mỗi campaign
- Tăng fairness cảm nhận: pity system giúp user không bao giờ cảm thấy "đen mãi"
- Tăng insight cho Biz: analytics dashboard + A/B test để tối ưu reward
- Tăng daily retention: streak bonus gắn với thói quen hàng ngày

---

## 2. Khái niệm cốt lõi (bổ sung v2)

| Khái niệm | Mô tả |
|---|---|
| **Wheel Type** | Loại game mechanic: `LUCKY_WHEEL`, `SLOT_MACHINE`, `SCRATCH_CARD` |
| **Pity Counter** | Đếm số lần trượt liên tiếp của user, dùng để tăng xác suất |
| **Pity Threshold** | Ngưỡng kích hoạt tăng xác suất hoặc guaranteed reward |
| **A/B Variant** | Phiên bản reward pool khác nhau, phân luồng ngẫu nhiên |
| **Streak** | Số ngày liên tiếp user có hoạt động trong campaign |
| **Streak Bonus** | Token thưởng thêm khi user duy trì streak đủ số ngày |

---

## 3. Tính năng v1 (giữ nguyên, tóm tắt)

- Campaign CRUD, status flow `DRAFT → SCHEDULED → ACTIVE → ENDED`
- Reward Pool: replaceable / non-replaceable, stock giới hạn
- Weight-based random, guaranteed after N
- Task list (one-time / daily), spin token ledger
- Full UI config: background, title, button, popup, TnC
- Deeplink / webview / close action cho mọi button

---

## 4. Tính năng mới v2

### F1 – Wheel Type: Slot Machine `NEW`

**Mô tả:** Thay vì vòng quay tròn, campaign hiển thị 3 cuộn (reel) trượt ngang. User bấm Spin → 3 cuộn quay độc lập → kết quả là tổ hợp 3 biểu tượng.

**Reward logic:**
- Config combo mapping: `[🍒🍒🍒] → Jackpot`, `[🍋🍋🍋] → 500 coin`, `[🍒🍒?] → 50 coin`, ...
- Slot machine có thể có nhiều line (1 line, 3 line, 5 line – config được)
- Mỗi reel có weight riêng cho từng symbol

**UI config thêm:**
- `reel_count`: số cuộn (mặc định 3)
- `line_count`: số line tính thưởng (1 / 3 / 5)
- `symbols[]`: danh sách biểu tượng, mỗi cái có `icon_url`, `weight`
- `combo_rewards[]`: mapping tổ hợp → reward

**Phù hợp với:** Campaign muốn cảm giác "casino", nhiều mức thưởng phức tạp

---

### F2 – Wheel Type: Scratch Card `NEW`

**Mô tả:** User nhận 1 tấm thẻ cào ảo. Vuốt ngón tay để cào lớp phủ → lộ ra phần thưởng bên dưới. Mỗi lần spin = 1 tấm thẻ mới.

**Reward logic:**
- Mỗi thẻ có N ô (config 3, 6, hoặc 9 ô)
- Reward được chọn trước khi hiển thị (random từ pool như thường), sau đó layout lên thẻ
- Có thể config kiểu "match 3": nếu 3 ô cùng biểu tượng → bonus reward thêm

**UI config thêm:**
- `card_background_url`: ảnh nền thẻ cào
- `scratch_overlay_color`: màu lớp cào (mặc định xám)
- `cell_count`: số ô (3 / 6 / 9)
- `match_bonus_enabled`: bật/tắt cơ chế match 3
- `match_bonus_reward`: reward thưởng thêm khi match

**Phù hợp với:** Campaign casual, ngắn ngày, cảm giác "bóc thẻ" trực quan

---

### F3 – Pity System `NEW`

**Mô tả:** Sau mỗi lần user không trúng reward xịn (trúng MISS hoặc reward nhỏ dưới ngưỡng), hệ thống tăng dần xác suất trúng reward cao hơn. Đảm bảo user không bao giờ cảm thấy "đen vô tận".

**Config:**
- `pity_enabled`: bật/tắt
- `pity_threshold`: số lần trượt liên tiếp trước khi kích hoạt
- `pity_mode`:
  - `BOOST`: tăng weight của reward xịn thêm X% sau mỗi lần trượt
  - `GUARANTEED`: sau đúng N lần trượt, lần tiếp theo chắc chắn trúng reward tier cao nhất
- `pity_boost_percent`: % tăng weight mỗi lần (dùng với BOOST mode)
- `pity_reset_on_win`: pity counter reset về 0 sau khi trúng reward xịn

**Ví dụ:** Pity threshold = 10, GUARANTEED mode → user trượt 10 lần liên tiếp → lần 11 chắc chắn trúng reward "EPIC" tier.

**Lưu ý PO:** Pity counter lưu per-user per-campaign. Khi campaign clone sang campaign mới, counter reset.

---

### F4 – A/B Testing Reward Pool `NEW`

**Mô tả:** Một campaign có thể có 2 phiên bản reward pool (Variant A và Variant B). User được phân luồng ngẫu nhiên khi lần đầu vào campaign, gắn cố định với variant đó trong suốt campaign.

**Config:**
- `ab_enabled`: bật/tắt
- `variant_a_pool_id`: reward pool cho nhóm A
- `variant_b_pool_id`: reward pool cho nhóm B
- `variant_a_traffic_percent`: % traffic vào A (phần còn lại vào B)

**Analytics tách biệt:**
- Spin count, reward distribution, conversion rate theo từng variant
- Ops/Biz thấy được bảng so sánh A vs B trực tiếp trên dashboard

**Giới hạn v2:** Chỉ hỗ trợ 2 variant (A/B), chưa hỗ trợ A/B/C.

---

### F5 – Streak Bonus `NEW`

**Mô tả:** User duy trì hoạt động liên tục trong campaign (spin ít nhất 1 lần/ngày) sẽ nhận thêm token theo chuỗi ngày.

**Config:**
- `streak_enabled`: bật/tắt
- `streak_rewards[]`: danh sách mốc streak và token bonus tương ứng
  ```
  Ngày 1: +1 token
  Ngày 3: +3 token
  Ngày 7: +10 token
  Ngày 14: +25 token
  ```
- `streak_reset_on_miss`: streak về 0 nếu user bỏ 1 ngày (strict mode)
- `streak_grace_period_hours`: số giờ gia hạn trước khi coi là miss (ví dụ: 30 giờ để tránh lệch giờ ngủ)

**UI:** Hiển thị thanh streak progress trên màn hình campaign, highlight mốc tiếp theo user sắp đạt.

---

### F6 – Campaign Analytics Dashboard `NEW`

**Mô tả:** Dashboard realtime trực tiếp trên Config Tool, Ops/Biz xem được số liệu mà không cần hỏi Dev.

**Metrics hiển thị:**
- Tổng spin count theo ngày (biểu đồ line)
- Reward distribution: % mỗi reward được trúng (so với weight config)
- Token flow: token phát ra vs token tiêu thụ
- Task completion rate: % user hoàn thành từng task
- Streak distribution: bao nhiêu user đang ở streak ngày mấy
- A/B comparison (nếu bật): side-by-side spin count + conversion

**Export:** CSV cho khoảng thời gian tùy chọn.

---

## 5. Cập nhật tính năng cũ

### U1 – Slot count linh hoạt (6 / 8 / 10 / 12)

v1 chỉ hỗ trợ 8 hoặc 12. v2 mở rộng: 6, 8, 10, 12 slot — áp dụng cho wheel type `LUCKY_WHEEL`.

### U2 – Task condition nâng cao

- **Combo task:** hoàn thành task A + task B → nhận bonus thêm
- **Dependent task:** task B chỉ mở sau khi hoàn thành task A
- **Tiered task:** cùng 1 task nhưng có nhiều mức (giao dịch 100K → 1 token, 500K → 5 token)

---

## 6. Giới hạn còn lại (sau v2)

| Hạn chế | Ghi chú |
|---|---|
| A/B chỉ 2 variant | A/B/C để roadmap v3 |
| Pity counter reset khi clone campaign | Behavior by design, xem lại nếu cần cross-campaign pity |
| Slot Machine chưa hỗ trợ free spin | Để v3 |
| Scratch Card chưa có hiệu ứng cào realtime trên web tool preview | Chỉ preview result, không simulate scratch gesture |
| Streak không tính ngày trước khi campaign active | User join muộn không có lợi thế streak |

---

## 7. Metrics bổ sung v2

- **Pity trigger rate**: % lần spin trúng nhờ pity (kỳ vọng < 15%)
- **A/B lift**: conversion rate chênh lệch giữa variant A và B
- **Streak retention**: % user đạt streak 7+ ngày / tổng user tham gia
- **Slot Machine vs Scratch Card vs Wheel**: spin count và conversion theo wheel type

---

## 8. Phụ thuộc bổ sung v2

- **Analytics Service / Data Warehouse**: feed data cho dashboard F6
- **Notification Service**: push notify nhắc user duy trì streak trước khi miss
