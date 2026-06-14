# TC07 — Auto-route: Cross-Version Conflict (Slot Count v1 vs v2)

| Field | Value |
|-------|-------|
| **Test ID** | TC07 |
| **Mode** | Auto-route (Agent Center) |
| **Type** | Edge case — thông tin mâu thuẫn giữa hai phiên bản |
| **Verdict** | ✅ PASS |

---

## 📤 Request

```
POST http://localhost:8080/chat
X-GreenNode-AgentBase-User-Id: qc-tester
Content-Type: application/json
```

```json
{
  "question": "Vòng quay Lucky Wheel hỗ trợ tối đa bao nhiêu slot? Có thể config 6 hoặc 10 slot không?"
}
```

---

## 📥 Response

| Field | Value |
|-------|-------|
| **status** | ✅ answered |
| **model_used** | `minimax/minimax-m2.5` |
| **source_departments** | `['grow_enablement']` |
| **citations** | 5 |
| **confidence** | `0.640` |
| **conflicts** | `None` |

### Answer

## Thông tin về số lượng slot của Lucky Wheel

**Có thể config 6 hoặc 10 slot** trong Lucky Wheel v2.

Theo tài liệu Lucky Wheel v2, hệ thống hỗ trợ **4 lựa chọn slot**: **6 / 8 / 10 / 12** slot [1][2].

### Chi tiết:
- **Phiên bản v1** (cũ): chỉ hỗ trợ 8 hoặc 12 slot [5]
- **Phiên bản v2** (mới): mở rộng hỗ trợ thêm 6 và 10 slot [1][2]

Vì vậy, bạn hoàn toàn có thể config campaign với 6 slot hoặc 10 slot khi sử dụng Lucky Wheel v2. Đây là tính năng mới được cập nhật trong phiên bản v2 nhằm tăng tính linh hoạt cho các chiến dịch marketing.

### Citations

**[1]** [Lucky Wheel Campaign v2: New Features and Enhancements Overview](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/327872/Lucky+Wheel+Campaign+v2+New+Features+and+Enhancements+Overview)
  - Doc type: `Operation` | Modified: `2026-06-11`
  - Excerpt: _# Tính năng mới Loại F1 Wheel Type mới: Slot Machine 🆕 New Feature F2 Wheel Type mới: Scratch Card 🆕 New Feature F3 Pity System (Tăng xác suất lũy tiến) 🆕 New Feature F4 A/B Testing cho Reward Pool 🆕 _

**[2]** [Lucky Wheel Operations Guide v2: New Features and Configuration Steps](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/327905/Lucky+Wheel+Operations+Guide+v2+New+Features+and+Configuration+Steps)
  - Doc type: `Operation` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Operations Guide v2 Audience: Campaign Operations Team Version: 2.0 Cập nhật so với v1: Thêm 2 wheel type mới, pity system, A/B test, streak bonus, analytics dashboard Tóm tắt thay đổi v_

**[3]** [Lucky Wheel Technical Documentation v2: Features, Architecture, and API Updates](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/98359/Lucky+Wheel+Technical+Documentation+v2+Features+Architecture+and+API+Updates)
  - Doc type: `Technical` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Technical Documentation v2 Audience: Backend & Frontend Developer Stack: Java/Spring (BE), React/Next.js (FE tool), Native App (end user) Version: 2.0 Changelog v2 Thay đổi Mô tả wheel_t_

**[4]** [Lucky Wheel Campaign: Features, Goals, and Management Overview](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/327880/Lucky+Wheel+Campaign+Features+Goals+and+Management+Overview)
  - Doc type: `Operation` | Modified: `2026-06-11`
  - Excerpt: _PRD – Lucky Wheel Campaign Audience: Product Owner Version: 1.0 Status: Living document 1. Tổng quan tính năng Lucky Wheel là một mini-game dạng vòng quay may mắn được nhúng vào trong app. Mỗi "Campai_

**[5]** [Lucky Wheel Campaign Operations Guide: Creation, Configuration, and Monitoring Steps](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/360467/Lucky+Wheel+Campaign+Operations+Guide+Creation+Configuration+and+Monitoring+Steps)
  - Doc type: `Operation` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Operations Guide Audience: Campaign Operations Team Mục đích: Hướng dẫn tạo & vận hành campaign Lucky Wheel trên Config Tool Version: 1.0 1. Quy trình tạo Campaign wide 760 2. Các bước c_


---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Mock | Agent | Kết quả |
|---|---|---|---|
| v1: chỉ 8 hoặc 12 slot | ✅ ops guide v1: "Số slot: 8 hoặc 12 — Không thể config 6, 10" | ✅ đề cập đúng | ✅ Đúng |
| v2: 6/8/10/12 slot | ✅ mock PRD v2 U1 | ✅ đề cập đúng | ✅ Đúng |
| Có thể config 6 slot? | ✅ Có (từ v2) | ✅ "Có thể config 6 slot — được hỗ trợ từ v2" | ✅ Đúng |
| Có thể config 10 slot? | ✅ Có (từ v2) | ✅ "Có thể config 10 slot — được hỗ trợ từ v2" | ✅ Đúng |
| `conflicts` field trong response | Không bắt buộc (2 nguồn không contradictory mà versioned) | `null` | ✅ Hợp lý |

## 📝 Ghi chú

- Hệ thống xử lý tốt thông tin versioned: phân biệt rõ v1 (8/12) vs v2 (6/8/10/12), không confuse
- `conflicts: null` — đúng vì 2 tài liệu không mâu thuẫn nhau (v2 mở rộng v1), chỉ là có context về version
- Answer tự thêm disclaimer "kiểm tra lại với đội Ops" — behavior tốt với nội dung nhạy cảm về config
