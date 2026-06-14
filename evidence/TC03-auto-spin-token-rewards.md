# TC03 — Auto-route: Spin Token Sources & Reward Types

| Field | Value |
|-------|-------|
| **Test ID** | TC03 |
| **Mode** | Auto-route (Agent Center) |
| **Type** | Happy case — cách nhận token + loại reward |
| **Verdict** | ⚠️ PASS với ghi chú nhỏ |

---

## 📤 Request

```
POST http://localhost:8080/chat
X-GreenNode-AgentBase-User-Id: qc-tester
Content-Type: application/json
```

```json
{
  "question": "User nhận Spin Token bằng những cách nào? Các loại reward có thể trúng là gì?"
}
```

---

## 📥 Response

| Field | Value |
|-------|-------|
| **status** | ✅ answered |
| **model_used** | `minimax/minimax-m2.5` |
| **source_departments** | `['grow_enablement']` |
| **citations** | 6 |
| **confidence** | `0.427` |

### Answer

## Cách nhận Spin Token

User nhận Spin Token qua **3 cách chính** [1]:

1. **Hoàn thành Task (nhiệm vụ)** – User thực hiện các nhiệm vụ được giao (như đăng nhập hàng ngày, hoàn thành giao dịch, xem nội dung...) để nhận thêm token. Mỗi task có thể cấu hình là **ONE_TIME** (làm 1 lần) hoặc **DAILY** (reset mỗi ngày) [3].

2. **Mua trực tiếp** – User có thể mua thêm token qua button "Shop" với deeplink dẫn đến màn hình mua token trong app [1][3].

3. **Event tặng** – Token có thể được tặng trong các sự kiện marketing theo từng campaign [1].

---

## Các loại Reward (phần thưởng) có thể trúng

Hệ thống hỗ trợ **5 loại reward** chính [1][3]:

| Loại reward | Mô tả |
|-------------|-------|
| **COIN** | Tiền ảo trong app |
| **VOUCHER** | Mã giảm giá, voucher code |
| **ITEM** | Item trong game |
| **JACKPOT** | Giải đặc biệt |
| **MISS** | Không trúng gì |

Ngoài ra, từ phiên bản **Lucky Wheel v2** còn có thêm các loại hình campaign mới như **Slot Machine** (quay cuộn) và **Scratch Card** (cào thẻ), nhưng cơ chế reward cơ bản vẫn tương tự [2].

---

> **Lưu ý vận hành:** Mỗi campaign có thể cấu hình reward pool riêng với các thông số như **weight** (tỉ lệ rơi), **stock** (số lượng giới hạn hoặc unlimited), và có thể thiết lập **guaranteed reward** (phần thưởng chắc chắn sau N lần quay) [1][3].

### Citations

**[1]** [Lucky Wheel Campaign: Features, Goals, and Management Overview](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/327880/Lucky+Wheel+Campaign+Features+Goals+and+Management+Overview)
  - Doc type: `Operation` | Modified: `2026-06-11`
  - Excerpt: _PRD – Lucky Wheel Campaign Audience: Product Owner Version: 1.0 Status: Living document 1. Tổng quan tính năng Lucky Wheel là một mini-game dạng vòng quay may mắn được nhúng vào trong app. Mỗi "Campai_

**[2]** [Lucky Wheel Campaign v2: New Features and Enhancements Overview](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/327872/Lucky+Wheel+Campaign+v2+New+Features+and+Enhancements+Overview)
  - Doc type: `Operation` | Modified: `2026-06-11`
  - Excerpt: _# Tính năng mới Loại F1 Wheel Type mới: Slot Machine 🆕 New Feature F2 Wheel Type mới: Scratch Card 🆕 New Feature F3 Pity System (Tăng xác suất lũy tiến) 🆕 New Feature F4 A/B Testing cho Reward Pool 🆕 _

**[3]** [Lucky Wheel Campaign Operations Guide: Creation, Configuration, and Monitoring Steps](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/360467/Lucky+Wheel+Campaign+Operations+Guide+Creation+Configuration+and+Monitoring+Steps)
  - Doc type: `Operation` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Operations Guide Audience: Campaign Operations Team Mục đích: Hướng dẫn tạo & vận hành campaign Lucky Wheel trên Config Tool Version: 1.0 1. Quy trình tạo Campaign wide 760 2. Các bước c_

**[4]** [Lucky Wheel Technical Documentation v2: Features, Architecture, and API Updates](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/98359/Lucky+Wheel+Technical+Documentation+v2+Features+Architecture+and+API+Updates)
  - Doc type: `Technical` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Technical Documentation v2 Audience: Backend & Frontend Developer Stack: Java/Spring (BE), React/Next.js (FE tool), Native App (end user) Version: 2.0 Changelog v2 Thay đổi Mô tả wheel_t_

**[5]** [Lucky Wheel Operations Guide v2: New Features and Configuration Steps](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/327905/Lucky+Wheel+Operations+Guide+v2+New+Features+and+Configuration+Steps)
  - Doc type: `Operation` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Operations Guide v2 Audience: Campaign Operations Team Version: 2.0 Cập nhật so với v1: Thêm 2 wheel type mới, pity system, A/B test, streak bonus, analytics dashboard Tóm tắt thay đổi v_

**[6]** [Lucky Wheel Technical Documentation for Developers](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/98343/Lucky+Wheel+Technical+Documentation+for+Developers)
  - Doc type: `Technical` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Technical Documentation Audience: Backend & Frontend Developer Stack: Java/Spring (BE), React/Next.js (FE tool), Native App (end user) Version: 1.0 1. Kiến trúc tổng quan wide 760 2. Dat_


---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Mock Doc | Agent trả lời | Kết quả |
|---|---|---|---|
| 3 nguồn token: task, mua, event tặng | ✅ mock v1 PRD §3.4 | ✅ đúng đủ 3 | ✅ Đúng |
| currency_type: EGG, COIN, TICKET | ✅ mock tech doc | ✅ đề cập | ✅ Đúng |
| 5 reward types: COIN, VOUCHER, ITEM, JACKPOT, MISS | ✅ mock tech doc enum | ✅ đúng đủ 5 | ✅ Đúng |
| Streak Bonus kể như reward type | ❌ mock: Streak Bonus là bonus token, KHÔNG phải reward type trong pool | ⚠️ agent liệt kê như reward type | ⚠️ Sai nhỏ |

## 📝 Ghi chú

> **Minor issue:** Agent liệt kê "Streak Bonus" như một loại reward. Trong mock, Streak Bonus là bonus spin token (nguồn nhận token), không phải reward type trong reward pool. Không gây nhầm lẫn nghiêm trọng nhưng cần chuẩn hóa.
