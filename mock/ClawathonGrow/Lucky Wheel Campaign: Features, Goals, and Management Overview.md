# PRD – Lucky Wheel Campaign

> **Audience:** Product Owner  
> **Version:** 1.0  
> **Status:** Living document

---

## 1. Tổng quan tính năng

Lucky Wheel là một mini-game dạng vòng quay may mắn được nhúng vào trong app. Mỗi "Campaign" là một phiên bản vòng quay độc lập, có thể tùy chỉnh toàn bộ giao diện, phần thưởng, luật quay và thời gian chạy. Nhiều campaign có thể tồn tại đồng thời nhưng mỗi user chỉ thấy campaign mà mình được phân loại vào.

### Mục tiêu sản phẩm

- Tăng engagement: kéo user quay lại app thường xuyên để tích lũy lượt quay
- Tăng conversion: thưởng voucher, coin, item kích thích user giao dịch
- Hỗ trợ marketing: mỗi campaign có thể gắn với một sự kiện (Tết, Valentine, Easter…)
- Linh hoạt vận hành: Ops team tự config mà không cần deploy code

---

## 2. Các khái niệm cốt lõi

| Khái niệm | Mô tả |
|---|---|
| **Campaign** | Một phiên Lucky Wheel có thời gian chạy xác định |
| **Spin Token** | Đơn vị để quay (coin, egg, ticket… – config riêng mỗi campaign) |
| **Reward Pool** | Tập hợp phần thưởng có thể rơi ra từ vòng quay |
| **Slot** | Một ô trên vòng quay, gắn với một reward |
| **Task** | Hành động user thực hiện để nhận thêm spin token |
| **TnC** | Điều khoản & điều kiện hiển thị kèm campaign |

---

## 3. Tính năng chính

### 3.1 Quản lý Campaign

- Tạo / sửa / xóa / clone campaign
- Đặt thời gian bắt đầu – kết thúc (timestamp)
- Trạng thái: `DRAFT` → `SCHEDULED` → `ACTIVE` → `ENDED`
- Hỗ trợ nhiều campaign active cùng lúc (phân luồng user theo segment)
- Preview campaign trước khi publish

### 3.2 Cấu hình vòng quay

- Số lượng slot: cố định (thường 8 hoặc 12)
- Mỗi slot config: icon/image, label, reward gắn kèm, tỉ lệ rơi (weight)
- Background vòng quay: upload ảnh hoặc chọn màu
- Kim chỉ (pointer): config vị trí, icon
- Animation: tốc độ quay, vòng quay tối thiểu trước khi dừng

### 3.3 Reward Pool & Random Logic

- Mỗi campaign có một hoặc nhiều reward pool
- Pool có thể là: **có hoàn lại** (replaceable) hoặc **không hoàn lại** (non-replaceable – hết là hết)
- Reward có `stock` (số lượng giới hạn) hoặc `unlimited`
- Weight-based random: mỗi reward có `weight` để tính xác suất
- Guaranteed reward: config phần thưởng rơi chắc chắn sau N lần quay
- Reward types hỗ trợ: coin, voucher code, item in-game, jackpot, "miss" (không trúng gì)

### 3.4 Spin Token & Nhiệm vụ (Tasks)

- Mỗi campaign config loại token riêng (currency_type)
- User nhận token qua: task hoàn thành, mua trực tiếp, event tặng
- Task list: danh sách nhiệm vụ user cần làm để nhận thêm token
  - Mỗi task có: mô tả, icon, action deeplink, reward token amount, điều kiện hoàn thành
  - Task có thể daily reset hoặc one-time
- Button "Spin 1" (tốn 1 token) và "Spin 10" (tốn N token) – đều config được

### 3.5 UI & Branding

Toàn bộ UI được config qua tool, không hardcode:

- **Campaign banner/background**: ảnh nền toàn màn hình
- **Title text**: nội dung, font size, màu
- **Countdown timer**: hiển thị thời gian còn lại, bật/tắt được
- **Token counter**: hiển thị số token user đang có
- **Button Spin**: label, màu, icon
- **Button Shop** (mua thêm token): label, deeplink
- **Popup trúng thưởng**: ảnh, text, animation, nút claim
- **Popup hết lượt**: text, nút đi mua thêm, deeplink
- **Popup lỗi**: text, nút retry
- **TnC**: nội dung text/HTML, vị trí hiển thị (bottom sheet hoặc popup), nút đóng

### 3.6 Navigation & Deeplink

- Mỗi button trong campaign có thể config `action_type`:
  - `DEEPLINK`: mở màn hình trong app
  - `WEBVIEW`: mở URL
  - `CLOSE`: đóng campaign
  - `NONE`: không làm gì
- Button Shop → thường link đến màn hình mua token
- Button Task → link đến task tương ứng
- Button Claim (sau khi trúng) → tùy theo loại reward

---

## 4. Giới hạn hiện tại

| Hạn chế | Mô tả |
|---|---|
| Số slot cố định | Hiện chỉ hỗ trợ 8 hoặc 12 slot, không tùy biến số lượng |
| Animation chưa tách biệt | Tốc độ quay global, chưa config per-campaign |
| Task condition đơn giản | Chưa hỗ trợ điều kiện phức tạp (combo task, dependent task) |
| Segment user | Phân luồng theo rule đơn giản, chưa A/B test tự động |
| Pool chưa có cơ chế "pity" mạnh | Guaranteed reward chỉ config sau N lần, chưa gradual increase probability |
| Preview chưa realtime | Preview phải reload sau mỗi lần thay đổi config |

---

## 5. Roadmap đề xuất (ưu tiên)

### Short-term
- [ ] A/B testing cho reward pool (split traffic tự động)
- [ ] Realtime preview trong config tool
- [ ] Thêm loại task: watch video, share, invite friend

### Mid-term
- [ ] Hỗ trợ số slot tùy biến (6, 8, 10, 12)
- [ ] Pity system: tăng dần xác suất reward xịn sau mỗi lần trượt
- [ ] Multi-language support cho campaign UI

### Long-term
- [ ] Jackpot mechanic (progressive jackpot pool)
- [ ] Social element: leaderboard token, compare với bạn bè
- [ ] AI-suggested reward weight dựa trên conversion history

---

## 6. Metrics theo dõi

- **Spin rate**: số lần quay / DAU
- **Token acquisition rate**: user hoàn thành bao nhiêu task để lấy token
- **Reward claim rate**: % user nhận thưởng thành công sau khi quay trúng
- **Conversion uplift**: giao dịch tăng trong thời gian campaign active
- **Churn reduction**: user quay lại app nhiều hơn trong campaign period

---

## 7. Phụ thuộc

- **Reward Service**: phát thưởng thực tế (coin, voucher…)
- **Task Service**: quản lý trạng thái hoàn thành task của user
- **Notification Service**: push notify khi sắp hết hạn campaign, task reminder
- **Segment Service**: phân loại user vào đúng campaign
- **CMS / Config Tool**: giao diện Ops dùng để tạo & quản lý campaign
