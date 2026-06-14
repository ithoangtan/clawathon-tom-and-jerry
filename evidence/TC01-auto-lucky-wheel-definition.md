# TC01 — Auto-route: Lucky Wheel là gì?

| Field | Value |
|-------|-------|
| **Test ID** | TC01 |
| **Mode** | Auto-route (Agent Center) — `target_departments: null` |
| **Type** | Happy case — định nghĩa cơ bản |
| **Verdict** | ✅ PASS |

---

## 📤 Request

```
POST http://localhost:8080/chat
X-GreenNode-AgentBase-User-Id: qc-tester
X-GreenNode-AgentBase-Session-Id: tc01-<timestamp>
Content-Type: application/json
```

```json
{
  "question": "Lucky Wheel là gì? Mục tiêu sản phẩm là gì?"
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
| **confidence** | `0.453` |
| **lang** | `vi` |
| **feedback_id** | `43913e6d-619c-44d6-bdeb-b4573fbe15e0` |

### Answer

## Lucky Wheel là gì?

Lucky Wheel là một **mini-game dạng vòng quay may mắn** được nhúng trực tiếp vào trong ứng dụng (app). [1]

Mỗi "Campaign" là một phiên bản vòng quay độc lập, có thể tùy chỉnh toàn bộ:
- Giao diện (background, button, popup)
- Phần thưởng (reward pool)
- Luật quay (số slot, tỉ lệ rơi)
- Thời gian chạy

Nhiều campaign có thể tồn tại đồng thời, nhưng mỗi user chỉ thấy campaign mà mình được phân loại vào. [1]

---

## Mục tiêu sản phẩm

### Mục tiêu (Version 1)
| Mục tiêu | Mô tả |
|----------|-------|
| **Tăng engagement** | Kéo user quay lại app thường xuyên để tích lũy lượt quay |
| **Tăng conversion** | Thưởng voucher, coin, item kích thích user giao dịch |
| **Hỗ trợ marketing** | Mỗi campaign có thể gắn với một sự kiện (Tết, Valentine, Easter…) |
| **Linh hoạt vận hành** | Ops team tự config mà không cần deploy code |

[1]

### Mục tiêu mở rộng (Version 2)
V2 mở rộng từ "vòng quay đơn thuần" thành **Mini-Game Platform** hỗ trợ nhiều loại game mechanic (Slot Machine, Scratch Card). [2]

| Mục tiêu v2 | Mô tả |
|-------------|-------|
| **Tránh nhàm chán** | 2 game type mới thay đổi trải nghiệm mỗi campaign |
| **Tăng fairness cảm nhận** | Pity system giúp user không bao giờ cảm thấy "đen mãi" |
| **Tăng insight cho Biz** | Analytics dashboard + A/B test để tối ưu reward |
| **Tăng daily retention** | Streak bonus gắn với thói quen hàng ngày |

[2]

### Citations

**[1]** [Lucky Wheel Campaign: Features, Goals, and Management Overview](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/327880/Lucky+Wheel+Campaign+Features+Goals+and+Management+Overview)
  - Doc type: `Operation` | Lifecycle: `active` | Modified: `2026-06-11`
  - Excerpt: _PRD – Lucky Wheel Campaign Audience: Product Owner Version: 1.0 Status: Living document 1. Tổng quan tính năng Lucky Wheel là một mini-game dạng vòng quay may mắn được nhúng vào trong app. Mỗi "Campai_

**[2]** [Lucky Wheel Campaign v2: New Features and Enhancements Overview](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/327872/Lucky+Wheel+Campaign+v2+New+Features+and+Enhancements+Overview)
  - Doc type: `Operation` | Lifecycle: `active` | Modified: `2026-06-11`
  - Excerpt: _# Tính năng mới Loại F1 Wheel Type mới: Slot Machine 🆕 New Feature F2 Wheel Type mới: Scratch Card 🆕 New Feature F3 Pity System (Tăng xác suất lũy tiến) 🆕 New Feature F4 A/B Testing cho Reward Pool 🆕 _

**[3]** [Lucky Wheel Technical Documentation v2: Features, Architecture, and API Updates](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/98359/Lucky+Wheel+Technical+Documentation+v2+Features+Architecture+and+API+Updates)
  - Doc type: `Technical` | Lifecycle: `active` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Technical Documentation v2 Audience: Backend & Frontend Developer Stack: Java/Spring (BE), React/Next.js (FE tool), Native App (end user) Version: 2.0 Changelog v2 Thay đổi Mô tả wheel_t_

**[4]** [Lucky Wheel Operations Guide v2: New Features and Configuration Steps](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/327905/Lucky+Wheel+Operations+Guide+v2+New+Features+and+Configuration+Steps)
  - Doc type: `Operation` | Lifecycle: `active` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Operations Guide v2 Audience: Campaign Operations Team Version: 2.0 Cập nhật so với v1: Thêm 2 wheel type mới, pity system, A/B test, streak bonus, analytics dashboard Tóm tắt thay đổi v_

**[5]** [Lucky Wheel Campaign Operations Guide: Creation, Configuration, and Monitoring Steps](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/360467/Lucky+Wheel+Campaign+Operations+Guide+Creation+Configuration+and+Monitoring+Steps)
  - Doc type: `Operation` | Lifecycle: `active` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Operations Guide Audience: Campaign Operations Team Mục đích: Hướng dẫn tạo & vận hành campaign Lucky Wheel trên Config Tool Version: 1.0 1. Quy trình tạo Campaign wide 760 2. Các bước c_

**[6]** [Lucky Wheel Technical Documentation for Developers](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/98343/Lucky+Wheel+Technical+Documentation+for+Developers)
  - Doc type: `Technical` | Lifecycle: `active` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Technical Documentation Audience: Backend & Frontend Developer Stack: Java/Spring (BE), React/Next.js (FE tool), Native App (end user) Version: 1.0 1. Kiến trúc tổng quan wide 760 2. Dat_


---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Mock Doc | Agent trả lời | Kết quả |
|---|---|---|---|
| Định nghĩa Lucky Wheel | "mini-game dạng vòng quay may mắn nhúng vào app" | "mini-game dạng vòng quay may mắn được nhúng trực tiếp vào trong ứng dụng" | ✅ Đúng |
| Mỗi Campaign là 1 phiên độc lập | ✅ có trong mock | ✅ đề cập | ✅ Đúng |
| Nhiều campaign cùng lúc / phân luồng user | ✅ có trong mock | ✅ đề cập | ✅ Đúng |
| 4 mục tiêu v1 (engagement, conversion, marketing, vận hành) | ✅ đầy đủ trong mock | ✅ liệt kê đủ 4 | ✅ Đúng |
| Mục tiêu v2 (pity, analytics, streak) | ✅ có trong mock v2 | ✅ bổ sung thêm | ✅ Đúng |

## 📝 Ghi chú

- Router tự động nhận diện intent và route đúng `grow_enablement` — không cần chỉ định department
- Answer tổng hợp từ cả v1 lẫn v2 docs, phân biệt rõ ràng từng version
- Model: `minimax/minimax-m2.5` (auto-fallback từ `qwen/qwen3.7-plus` do daily quota exhausted)
