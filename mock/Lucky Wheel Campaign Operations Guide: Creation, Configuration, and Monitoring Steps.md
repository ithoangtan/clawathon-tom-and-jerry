# Lucky Wheel – Operations Guide

> **Audience:** Campaign Operations Team  
> **Mục đích:** Hướng dẫn tạo & vận hành campaign Lucky Wheel trên Config Tool  
> **Version:** 1.0

---

## 1. Quy trình tạo Campaign

```
Nhận yêu cầu từ Biz
        ↓
Tạo Campaign (DRAFT)
        ↓
Config UI + Reward Pool
        ↓
Config Task List
        ↓
Review nội dung TnC
        ↓
Gửi Dev/PO review (nếu cần)
        ↓
Đặt lịch → SCHEDULED
        ↓
Tự động ACTIVE khi đến giờ
        ↓
Monitor trong thời gian chạy
        ↓
Campaign tự ENDED khi hết giờ
```

---

## 2. Các bước config chi tiết

### Bước 1 – Thông tin cơ bản

| Field | Mô tả | Ví dụ |
|---|---|---|
| Campaign Name | Tên nội bộ (Ops thấy, user không thấy) | `easter_2024_q2` |
| Start Time | Thời điểm bắt đầu (UTC+7) | `2024-04-01 00:00` |
| End Time | Thời điểm kết thúc (UTC+7) | `2024-04-07 23:59` |
| Currency Type | Loại token để quay | `EGG` / `COIN` / `TICKET` |
| Segment Rule | Ai nhìn thấy campaign này | `ALL` / `NEW_USER` / `VIP` |

> ⚠️ **Lưu ý:** Đặt end_time trước 23:59 để tránh lệch múi giờ. Luôn dùng giờ VN (UTC+7).

---

### Bước 2 – UI & Branding

**Background campaign:**
- Upload ảnh nền toàn màn hình (khuyến nghị: 750×1334px, PNG/JPG, < 500KB)
- Hoặc chọn màu hex nếu không có ảnh

**Wheel:**
- Upload ảnh vòng quay (PNG với nền trong suốt, kích thước vuông ≥ 600×600px)
- Upload ảnh kim chỉ (pointer)

**Title:**
- Text hiển thị, màu chữ, cỡ chữ

**Countdown:** Bật/tắt đồng hồ đếm ngược. Nếu bật, hiển thị thời gian còn lại đến end_time.

---

### Bước 3 – Cấu hình Slots & Reward Pool

**Bước 3a – Tạo Reward Pool**

- Chọn loại pool:
  - `REPLACEABLE`: phần thưởng trong pool có thể tái sử dụng (phù hợp coin, miss)
  - `NON_REPLACEABLE`: phần thưởng hết là hết (phù hợp voucher code giới hạn)
- Config guaranteed_after_N nếu muốn đảm bảo user chắc chắn trúng sau N lần quay

**Bước 3b – Thêm Reward Items (gắn vào từng Slot)**

Mỗi slot cần config:

| Field | Mô tả |
|---|---|
| Slot index | Vị trí trên vòng quay (0 → 7 cho wheel 8 slot) |
| Icon URL | Ảnh hiển thị trên ô (PNG, ~100×100px) |
| Label | Text hiển thị trên ô (ngắn gọn, < 10 ký tự) |
| Reward Type | COIN / VOUCHER / ITEM / JACKPOT / MISS |
| Reward Value | Số tiền, mã voucher pool, hoặc item ID |
| Weight | Số nguyên dương – càng cao càng dễ rơi. VD: MISS=100, COIN_1K=50, VOUCHER=5 |
| Stock | Số lượng tối đa. Để trống = không giới hạn |

> ⚠️ **Giới hạn:** Tổng số slot hiện chỉ hỗ trợ **8 hoặc 12**. Không thể config số lẻ.

> ⚠️ **Stock:** Khi stock reward về 0, system sẽ tự động fallback sang reward khác. Nên luôn có ít nhất 1 reward MISS hoặc reward unlimited trong pool.

---

### Bước 4 – Config Nút Spin

| Field | Mô tả |
|---|---|
| Spin 1 cost | Số token tốn cho 1 lần quay (mặc định: 1) |
| Spin 10 cost | Số token tốn cho quay x10 (thường = 10, có thể giảm để khuyến khích) |
| Button label | Text hiển thị trên nút |
| Button màu | Màu nền, màu chữ |

---

### Bước 5 – Task List

Mỗi task là một nhiệm vụ để user nhận thêm token:

| Field | Mô tả |
|---|---|
| Title | Tên nhiệm vụ ngắn gọn |
| Description | Mô tả cách làm |
| Icon | Ảnh đại diện task |
| Token reward | Số token nhận khi hoàn thành |
| Action deeplink | Link mở khi user bấm vào task |
| Reset type | `ONE_TIME` (chỉ làm 1 lần) hoặc `DAILY` (reset mỗi ngày) |
| Completion condition | Trao đổi với Dev để gắn đúng condition ID |

---

### Bước 6 – Popup & Buttons

**Popup trúng thưởng:** Upload ảnh background, đặt title, label nút claim.

**Popup hết lượt:** Text thông báo + nút CTA dẫn user đi làm task hoặc mua token.

**Popup lỗi:** Text lỗi generic, nút retry.

**Button Shop:** Deeplink đến màn hình mua thêm token (lấy link từ Dev).

---

### Bước 7 – TnC

- Paste nội dung TnC (plain text hoặc HTML đơn giản)
- Chọn kiểu hiển thị: `POPUP` hoặc `BOTTOM_SHEET`
- TnC sẽ hiện khi user bấm vào link "Điều khoản & Điều kiện"

---

### Bước 8 – Publish

1. Nhấn **Save** → campaign lưu dạng DRAFT
2. Nhấn **Preview** → xem thử trên simulator (không ảnh hưởng data thật)
3. Nhấn **Schedule** → campaign chờ đến start_time rồi tự ACTIVE
4. Hoặc nhấn **Publish Now** nếu muốn active ngay

---

## 3. Monitor khi Campaign đang chạy

### Chỉ số cần theo dõi hàng ngày

- **Spin count**: tổng số lần quay, so với ngày hôm trước
- **Token balance trung bình**: user còn nhiều token chưa dùng → cần push notify
- **Remaining stock** của các reward giới hạn: nếu gần hết cần tăng stock hoặc thêm reward mới
- **Error rate**: nếu tăng đột biến → báo Dev ngay

### Xử lý sự cố

| Tình huống | Hành động |
|---|---|
| Stock reward về 0 sớm hơn dự kiến | Vào edit pool → tăng stock hoặc thêm reward mới |
| Campaign hiển thị sai UI | Chỉnh config → Save → cache tự clear sau 5 phút |
| User báo không quay được | Kiểm tra token balance, sau đó báo Dev check log |
| Cần dừng campaign gấp | PATCH status → `ENDED` (không thể undo) |

---

## 4. Giới hạn & Lưu ý quan trọng

| Giới hạn | Lưu ý |
|---|---|
| Số slot: 8 hoặc 12 | Không thể config 6, 10, hay số khác |
| Ảnh upload | PNG/JPG, tối đa 500KB mỗi file |
| Không thể xóa campaign ACTIVE | Chỉ có thể ENDED sớm hoặc edit config |
| Không thể hoàn tác ENDED | Muốn chạy lại phải clone campaign mới |
| Một user một lúc một campaign | Nếu user thuộc 2 segment khác nhau → hệ thống ưu tiên campaign có priority cao hơn |
| Task completion check | Ops không tự config được condition phức tạp – cần Dev hỗ trợ |

---

## 5. Checklist trước khi Publish

- [ ] Start time và end time đã đúng múi giờ VN chưa?
- [ ] Tất cả slot đã có reward gắn kèm chưa?
- [ ] Có ít nhất 1 reward MISS hoặc unlimited trong pool chưa?
- [ ] Deeplink Shop và Task đã test chưa?
- [ ] TnC đã được Legal review chưa?
- [ ] Preview đã xem thử trên mobile chưa?
- [ ] Segment rule đúng target user chưa?
- [ ] Thông báo Dev về campaign sắp live (để monitor log)?
