# TC02 — Auto-route: Campaign Status Flow

| Field | Value |
|-------|-------|
| **Test ID** | TC02 |
| **Mode** | Auto-route (Agent Center) — `target_departments: null` |
| **Type** | Happy case — trạng thái và flow campaign |
| **Verdict** | ✅ PASS |

---

## 📤 Request

```
POST http://localhost:8080/chat
X-GreenNode-AgentBase-User-Id: qc-tester
X-GreenNode-AgentBase-Session-Id: tc02-<timestamp>
Content-Type: application/json
```

```json
{
  "question": "Các trạng thái của một Campaign Lucky Wheel là gì? Flow chuyển đổi trạng thái như thế nào?"
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
| **confidence** | `0.480` |
| **lang** | `vi` |

### Answer

## Các trạng thái của Campaign Lucky Wheel

Dựa trên tài liệu, một Campaign Lucky Wheel có **4 trạng thái** chính:

| Trạng thái | Mô tả |
|------------|-------|
| **DRAFT** | Bản nháp - campaign đang được tạo/chỉnh sửa, chưa được kích hoạt |
| **SCHEDULED** | Đã lên lịch - campaign đã được thiết lập thời gian chạy, sẵn sàng hoạt động |
| **ACTIVE** | Đang chạy - campaign đang diễn ra, user có thể tham gia |
| **ENDED** | Đã kết thúc - campaign đã kết thúc, không còn hoạt động |

---

## Flow chuyển đổi trạng thái

```
DRAFT → SCHEDULED → ACTIVE → ENDED
```

**Luồng chuyển đổi:**

1. **DRAFT → SCHEDULED**: Sau khi Ops lưu campaign và đặt thời gian bắt đầu – kết thúc [1]
2. **SCHEDULED → ACTIVE**: Khi đến thời gian bắt đầu (start_time), hệ thống tự động chuyển sang ACTIVE [1]
3. **ACTIVE → ENDED**: Khi đến thời gian kết thúc (end_time), hệ thống tự động chuyển sang ENDED [1]

---

## Lưu ý bổ sung từ v2

- Hệ thống hỗ trợ **nhiều campaign ACTIVE cùng lúc**, phân luồng user theo segment [1]
- Từ v2, khi tạo campaign cần chọn **Wheel Type** (Lucky Wheel / Slot Machine / Scratch Card) ngay từ đầu - **không thể đổi wheel type sau khi campaign đã ACTIVE** [3]

---

_Tham khảo: PRD – Lucky Wheel Campaign (v1.0) và Lucky Wheel v2 Overview._

### Citations

**[1]** [Lucky Wheel Campaign: Features, Goals, and Management Overview](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/327880/Lucky+Wheel+Campaign+Features+Goals+and+Management+Overview)
  - Doc type: `Operation` | Modified: `2026-06-11`
  - Excerpt: _PRD – Lucky Wheel Campaign Audience: Product Owner Version: 1.0 Status: Living document 1. Tổng quan tính năng Lucky Wheel là một mini-game dạng vòng quay may mắn được nhúng vào trong app. Mỗi "Campai_

**[2]** [Lucky Wheel Campaign v2: New Features and Enhancements Overview](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/327872/Lucky+Wheel+Campaign+v2+New+Features+and+Enhancements+Overview)
  - Doc type: `Operation` | Modified: `2026-06-11`
  - Excerpt: _# Tính năng mới Loại F1 Wheel Type mới: Slot Machine 🆕 New Feature F2 Wheel Type mới: Scratch Card 🆕 New Feature F3 Pity System (Tăng xác suất lũy tiến) 🆕 New Feature F4 A/B Testing cho Reward Pool 🆕 _

**[3]** [Lucky Wheel Operations Guide v2: New Features and Configuration Steps](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/327905/Lucky+Wheel+Operations+Guide+v2+New+Features+and+Configuration+Steps)
  - Doc type: `Operation` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Operations Guide v2 Audience: Campaign Operations Team Version: 2.0 Cập nhật so với v1: Thêm 2 wheel type mới, pity system, A/B test, streak bonus, analytics dashboard Tóm tắt thay đổi v_

**[4]** [Lucky Wheel Campaign Operations Guide: Creation, Configuration, and Monitoring Steps](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/360467/Lucky+Wheel+Campaign+Operations+Guide+Creation+Configuration+and+Monitoring+Steps)
  - Doc type: `Operation` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Operations Guide Audience: Campaign Operations Team Mục đích: Hướng dẫn tạo & vận hành campaign Lucky Wheel trên Config Tool Version: 1.0 1. Quy trình tạo Campaign wide 760 2. Các bước c_

**[5]** [Lucky Wheel Technical Documentation v2: Features, Architecture, and API Updates](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/98359/Lucky+Wheel+Technical+Documentation+v2+Features+Architecture+and+API+Updates)
  - Doc type: `Technical` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Technical Documentation v2 Audience: Backend & Frontend Developer Stack: Java/Spring (BE), React/Next.js (FE tool), Native App (end user) Version: 2.0 Changelog v2 Thay đổi Mô tả wheel_t_

**[6]** [Lucky Wheel Technical Documentation for Developers](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/98343/Lucky+Wheel+Technical+Documentation+for+Developers)
  - Doc type: `Technical` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Technical Documentation Audience: Backend & Frontend Developer Stack: Java/Spring (BE), React/Next.js (FE tool), Native App (end user) Version: 1.0 1. Kiến trúc tổng quan wide 760 2. Dat_


---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Mock Doc | Agent trả lời | Kết quả |
|---|---|---|---|
| 4 trạng thái: DRAFT, SCHEDULED, ACTIVE, ENDED | ✅ mock v1 | ✅ đầy đủ | ✅ Đúng |
| Flow: DRAFT → SCHEDULED → ACTIVE → ENDED | ✅ mock v1 | ✅ đúng thứ tự | ✅ Đúng |
| SCHEDULED → ACTIVE khi đến start_time tự động | ✅ mock ops guide | ✅ đề cập | ✅ Đúng |
| Nhiều campaign ACTIVE đồng thời | ✅ mock v1 | ✅ đề cập | ✅ Đúng |
| Không thể đổi wheel_type sau khi ACTIVE (v2) | ✅ mock ops guide v2 | ✅ bổ sung note | ✅ Tốt (bonus) |

## 📝 Ghi chú

- Answer phân biệt rõ v1 và v2, không lẫn lộn
- Thêm note từ v2 (không thể đổi wheel_type) là thông tin bổ sung hữu ích, không sai
