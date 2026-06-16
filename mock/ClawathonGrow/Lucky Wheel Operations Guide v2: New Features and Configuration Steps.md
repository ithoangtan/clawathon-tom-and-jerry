# Lucky Wheel – Operations Guide v2

> **Audience:** Campaign Operations Team  
> **Version:** 2.0  
> **Cập nhật so với v1:** Thêm 2 wheel type mới, pity system, A/B test, streak bonus, analytics dashboard

---

## Tóm tắt thay đổi v2 dành cho Ops

| Tính năng | Ops cần làm gì thêm? |
|---|---|
| Wheel Type mới (Slot Machine, Scratch Card) | Chọn type khi tạo campaign, config thêm symbols/cells |
| Pity System | Bật/tắt, chọn mode, đặt ngưỡng |
| A/B Testing | Config 2 pool, đặt traffic split (chỉ khi DRAFT) |
| Streak Bonus | Bật/tắt, config mốc ngày và số token tương ứng |
| Analytics Dashboard | Xem số liệu, export CSV – không cần hỏi Dev |

---

## 1. Chọn Wheel Type khi tạo Campaign

Bước đầu tiên khi tạo campaign mới, Ops chọn 1 trong 3 loại:

| Type | Trải nghiệm user | Phù hợp khi |
|---|---|---|
| **Lucky Wheel** | Vòng quay tròn truyền thống | Campaign thông thường, mọi dịp |
| **Slot Machine** | 3 cuộn trượt, match combo | Muốn cảm giác casino, nhiều mức thưởng |
| **Scratch Card** | Tấm thẻ cào ảo | Campaign ngắn ngày, casual, "bóc thẻ" |

> ⚠️ **Không thể đổi wheel type sau khi campaign đã ACTIVE.** Chọn đúng ngay từ đầu.

---

## 2. Config theo từng Wheel Type

### 2a. Lucky Wheel (giống v1, bổ sung slot count)

- Hỗ trợ: **6 / 8 / 10 / 12 slot** (v1 chỉ có 8 và 12)
- Các bước config giống v1 (xem Ops Guide v1 §2–§6)

---

### 2b. Slot Machine – Config bổ sung

**Bước 1 – Config symbols (biểu tượng trên cuộn)**

Mỗi symbol cần:

| Field | Mô tả | Ví dụ |
|---|---|---|
| Symbol ID | Tên định danh (không dấu, không khoảng trắng) | `cherry`, `seven` |
| Icon URL | Ảnh biểu tượng (PNG, ~100×100px) | |
| Weight | Xác suất xuất hiện trên cuộn | Cherry=30, Seven=5 |

**Bước 2 – Config combo rewards**

Mỗi combo là một tổ hợp 3 symbol → reward tương ứng:

| Pattern | Ví dụ | Reward |
|---|---|---|
| 3 giống nhau chính xác | `[cherry, cherry, cherry]` | Jackpot |
| 3 giống nhau | `[lemon, lemon, lemon]` | 500 coin |
| 2 giống + bất kỳ | `[cherry, cherry, *]` | 50 coin |
| Bất kỳ (fallback) | `[*, *, *]` | Miss |

> ⚠️ **Bắt buộc phải có 1 combo fallback `[*, *, *]` ở cuối.** Nếu không có, spin sẽ lỗi.

**Bước 3 – Config số cuộn và số line**
- Reel count: thường để 3
- Line count: 1 (đơn giản) hoặc 3/5 (phức tạp hơn, trao đổi với Dev trước)

---

### 2c. Scratch Card – Config bổ sung

| Field | Mô tả |
|---|---|
| Cell count | Số ô trên thẻ: 3, 6, hoặc 9 |
| Card background | Ảnh nền thẻ (750×400px, PNG) |
| Scratch overlay color | Màu lớp phủ cào (mặc định xám #AAAAAA) |
| Match bonus | Bật/tắt – nếu bật: user match 3 ô giống nhau → thưởng thêm |
| Match bonus reward | Reward thưởng thêm khi match (coin, token…) |

> **Lưu ý:** Reward pool cho Scratch Card config giống hệt Lucky Wheel thông thường — vẫn là weight-based random, tương tự v1.

---

## 3. Pity System – Config & Vận hành

**Bật pity:** Toggle ON trong phần "Advanced Settings" của campaign.

**Chọn mode:**

| Mode | Hành vi | Khi nào dùng |
|---|---|---|
| **BOOST** | Sau mỗi lần trượt, xác suất reward xịn tăng dần | Muốn "mềm" – xác suất tăng từ từ |
| **GUARANTEED** | Sau đúng N lần trượt → lần tiếp theo chắc chắn trúng reward cao nhất | Muốn cam kết rõ ràng với user |

**Config BOOST mode:**
- Threshold: số lần trượt bắt đầu kích hoạt boost
- Boost percent: % tăng weight mỗi lần trượt (khuyến nghị 10–20%)

**Config GUARANTEED mode:**
- Threshold: số lần trượt → lần N+1 chắc chắn trúng (khuyến nghị 7–15)
- Guaranteed tier: loại reward chắc chắn trúng (phải là tier có trong pool)

> ⚠️ **Lưu ý vận hành:** Pity counter reset khi campaign mới bắt đầu. Nếu clone campaign từ event này sang event khác, user bắt đầu lại từ 0.

---

## 4. A/B Testing – Config & Vận hành

> ⚠️ **Chỉ config A/B khi campaign còn DRAFT. Không thể thay đổi traffic split sau khi ACTIVE.**

**Bước 1:** Tạo 2 reward pool riêng biệt (tạo pool trước, sau đó gán vào A/B).

**Bước 2:** Bật A/B Testing trong campaign settings.

**Bước 3:** Gán pool A, pool B và đặt traffic split (ví dụ: 50% A / 50% B).

**Bước 4:** Sau khi campaign chạy ít nhất 2–3 ngày → vào Analytics tab → xem bảng so sánh A vs B.

**Đọc kết quả A/B:**

| Metric | Ý nghĩa |
|---|---|
| Spin count A vs B | Số lần quay của 2 nhóm (nên tương đương nếu traffic 50/50) |
| Reward distribution | Reward nào rơi nhiều hơn – check xem có lệch so với weight không |
| Conversion rate | % user thực hiện giao dịch trong/sau khi chơi |

> **Quy tắc:** Không kết luận winner trước 500 spin/variant. Dưới ngưỡng đó kết quả chưa có ý nghĩa thống kê.

---

## 5. Streak Bonus – Config & Vận hành

**Bật streak:** Toggle ON trong phần "Engagement Settings".

**Config milestones:** Thêm từng mốc streak:

| Mốc (ngày) | Token bonus | Ghi chú |
|---|---|---|
| 1 | 1 | Mốc đầu tiên, thấp để dễ đạt |
| 3 | 3 | |
| 7 | 10 | Mốc tuần |
| 14 | 25 | Mốc 2 tuần |

**Strict mode vs Grace period:**
- `Reset on miss = ON`: user bỏ 1 ngày → streak về 0 (nghiêm ngặt)
- `Grace period = 30 giờ`: thay vì reset đúng 24h, cho user 30h để giữ streak (khuyến nghị để tránh phàn nàn về múi giờ)

> **Lưu ý:** User chỉ cần spin ít nhất 1 lần/ngày để giữ streak. Task completion không tính, chỉ tính spin thật.

---

## 6. Analytics Dashboard – Cách đọc số liệu

Vào tab **Analytics** trong campaign detail. Không cần hỏi Dev.

### Các tab chính:

**Overview**
- Spin count theo ngày (line chart) → xem trend tăng/giảm
- Token flow: phát ra vs tiêu thụ → nếu phát >> tiêu thụ, user đang tích lũy nhiều, cần push notify

**Reward Distribution**
- % mỗi reward được trúng thực tế vs weight config
- Nếu lệch lớn (>5%) → báo Dev kiểm tra random engine hoặc stock

**Task Performance**
- % user hoàn thành từng task
- Task completion rate thấp → mô tả task khó hiểu, cần edit

**Streak**
- Bar chart: bao nhiêu user đang ở streak ngày 1, 3, 7, 14+
- Nếu phần lớn user stuck ở ngày 1 → milestone ngày 3 có thể quá cao, cần điều chỉnh

**A/B Comparison** (chỉ hiện nếu bật A/B)
- Side-by-side: spin count, reward rate, conversion

**Export:** Nút "Export CSV" → chọn khoảng ngày → tải về.

---

## 7. Giới hạn mới cần biết (v2)

| Giới hạn | Lưu ý |
|---|---|
| A/B chỉ 2 variant | Không thể A/B/C trong v2 |
| Wheel type không đổi được sau ACTIVE | Chọn kỹ ngay từ đầu |
| Traffic split A/B chỉ set khi DRAFT | Không chỉnh được sau khi có user đã vào campaign |
| Scratch card expire sau 10 phút | User cào xong phải claim ngay, không để lâu |
| Analytics delay ~5 phút | Số liệu không realtime tuyệt đối, refresh sau 5 phút |
| Combo fallback bắt buộc | Slot Machine phải có `[*,*,*]` → MISS ở cuối |

---

## 8. Checklist trước khi Publish (v2 bổ sung)

**Checklist gốc v1 (giữ nguyên) +**

- [ ] Đã chọn đúng wheel type chưa?
- [ ] Nếu Slot Machine: có combo fallback `[*,*,*]` ở cuối danh sách chưa?
- [ ] Nếu Scratch Card: ảnh thẻ đúng kích thước 750×400px chưa?
- [ ] Nếu bật Pity: threshold có hợp lý với độ dài campaign không? (campaign 3 ngày mà threshold = 20 thì user khó đạt)
- [ ] Nếu bật A/B: 2 pool đã được tạo và gán đúng chưa? Traffic split đã confirm với Biz chưa?
- [ ] Nếu bật Streak: grace period đã set chưa (khuyến nghị 30h)?
- [ ] Đã xem Analytics tab trống (0 data) để confirm dashboard load được không?
