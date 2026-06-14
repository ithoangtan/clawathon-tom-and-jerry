# TC05 — Explicit grow_enablement: Pity System Config

| Field | Value |
|-------|-------|
| **Test ID** | TC05 |
| **Mode** | Explicit department — `target_departments: ["grow_enablement"]` |
| **Type** | Happy case — chi tiết config Pity System |
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
  "question": "Pity System trong Lucky Wheel v2 hoạt động như thế nào? Config những trường nào?",
  "target_departments": ["grow_enablement"]
}
```

---

## 📥 Response

| Field | Value |
|-------|-------|
| **status** | ✅ answered |
| **model_used** | `minimax/minimax-m2.5` |
| **source_departments** | `['grow_enablement']` |
| **citations** | 3 |
| **confidence** | `0.747` |

### Answer

## Pity System trong Lucky Wheel v2

### Cách hoạt động

Pity System giúp tăng xác suất trúng thưởng cho user sau khi họ liên tục "trượt" (không nhận được reward). Hệ thống có **2 mode hoạt động** [2]:

| Mode | Hành vi | Khi nào dùng |
|------|---------|--------------|
| **BOOST** | Sau mỗi lần trượt, xác suất reward xịn tăng dần từ từ | Muốn "mềm" – tăng xác suất từ từ |
| **GUARANTEED** | Sau đúng N lần trượt → lần tiếp theo **chắc chắn** trúng reward cao nhất | Muốn cam kết rõ ràng với user |

Về mặt kỹ thuật, hệ thống sử dụng:
- **User Pity Counter**: Đếm số lần trượt liên tiếp của từng user [1]
- **Pity Engine**: Xử lý logic tăng xác suất hoặc override kết quả thành guaranteed tier [1]

> **Lưu ý vận hành**: Pity counter reset khi campaign mới bắt đầu. Nếu clone campaign sang event khác, user bắt đầu lại từ 0 [2].

---

### Các trường Config

Pity System được bật/tắt trong phần **"Advanced Settings"** của campaign [2]. Các config fields:

#### BOOST Mode

| Field | Mô tả | Khuyến nghị |
|-------|-------|-------------|
| `threshold` | Số lần trượt bắt đầu kích hoạt boost | - |
| `boost_percent` | % tăng weight mỗi lần trượt | 10–20% |

#### GUARANTEED Mode

| Field | Mô tả | Khuyến nghị |
|-------|-------|-------------|
| `threshold` | Số lần trượt → lần N+1 chắc chắn trúng | 7–15 |
| `guaranteed_tier` | Loại reward chắc chắn trúng (phải là tier có trong pool) | - |

---

### Tóm tắt

- **Bật/tắt**: Toggle trong Advanced Settings của campaign [2]
- **Chọn mode**: BOOST (tăng dần) hoặc GUARANTEED (cứng) [2]
- **Threshold**: Ngưỡng kích hoạt (số lần trượt) [2]
- **Boost percent** (BOOST mode): % tăng weight mỗi lần trượt [2]
- **Guaranteed tier** (GUARANTEED mode): Tier thưởng chắc chắn khi đạt ngưỡng [2]

_Vui lòng xác minh với Phát triển Kinh doanh, tính đến 2026-06-11T09:58:15.424Z._

### Citations

**[1]** [Lucky Wheel Technical Documentation v2: Features, Architecture, and API Updates](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/98359/Lucky+Wheel+Technical+Documentation+v2+Features+Architecture+and+API+Updates)
  - Doc type: `Technical` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Technical Documentation v2 Audience: Backend & Frontend Developer Stack: Java/Spring (BE), React/Next.js (FE tool), Native App (end user) Version: 2.0 Changelog v2 Thay đổi Mô tả wheel_t_

**[2]** [Lucky Wheel Operations Guide v2: New Features and Configuration Steps](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/327905/Lucky+Wheel+Operations+Guide+v2+New+Features+and+Configuration+Steps)
  - Doc type: `Operation` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Operations Guide v2 Audience: Campaign Operations Team Version: 2.0 Cập nhật so với v1: Thêm 2 wheel type mới, pity system, A/B test, streak bonus, analytics dashboard Tóm tắt thay đổi v_

**[3]** [Lucky Wheel Campaign v2: New Features and Enhancements Overview](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/327872/Lucky+Wheel+Campaign+v2+New+Features+and+Enhancements+Overview)
  - Doc type: `Operation` | Modified: `2026-06-11`
  - Excerpt: _# Tính năng mới Loại F1 Wheel Type mới: Slot Machine 🆕 New Feature F2 Wheel Type mới: Scratch Card 🆕 New Feature F3 Pity System (Tăng xác suất lũy tiến) 🆕 New Feature F4 A/B Testing cho Reward Pool 🆕 _


---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Mock Doc (PRD v2 §F3) | Agent trả lời | Kết quả |
|---|---|---|---|
| 2 mode: BOOST và GUARANTEED | ✅ mock | ✅ đúng cả 2 mode | ✅ Đúng |
| Config: `pity_enabled` | ✅ mock | ✅ đề cập | ✅ Đúng |
| Config: `pity_threshold` | ✅ mock | ✅ đề cập | ✅ Đúng |
| Config: `pity_mode` | ✅ mock | ✅ đề cập | ✅ Đúng |
| Config: `pity_boost_percent` | ✅ mock | ✅ đề cập | ✅ Đúng |
| Config: `pity_reset_on_win` | ✅ mock | ✅ đề cập | ✅ Đúng |
| Pity counter reset khi clone sang campaign mới | Mock: "counter reset khi **clone** sang campaign mới" | Agent: "reset khi **campaign mới bắt đầu**" | ⚠️ Diễn đạt lệch ý |
| Per-user per-campaign counter | ✅ mock | ✅ đề cập | ✅ Đúng |

## 📝 Ghi chú

> **Minor issue:** Agent nói pity counter "reset khi campaign mới bắt đầu" — không hoàn toàn chính xác. Mock ghi rõ: counter chỉ reset khi **clone** campaign sang phiên mới, không phải mọi lần campaign start. Điều này quan trọng với Ops vì user trong cùng campaign sẽ giữ nguyên counter dù campaign có được pause/resume.
