# TC04 — Explicit grow_enablement: Lucky Wheel v2 New Features

| Field | Value |
|-------|-------|
| **Test ID** | TC04 |
| **Mode** | Explicit department — `target_departments: ["grow_enablement"]` |
| **Type** | Happy case — danh sách tính năng mới v2 |
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
  "question": "Lucky Wheel v2 có những tính năng mới gì so với v1?",
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
| **citations** | 4 |
| **confidence** | `0.680` |

### Answer

## Tính năng mới của Lucky Wheel v2 so với v1

Lucky Wheel v2 được nâng cấp từ "vòng quay đơn thuần" thành **Mini-Game Platform** với nhiều cơ chế game mới [1].

### Các tính năng hoàn toàn mới (New Features)

| Mã | Tính năng | Mô tả |
|----|-----------|-------|
| **F1** | Wheel Type: **Slot Machine** | Thay vì vòng quay tròn, campaign hiển thị 3 cuộn (reel) trượt ngang. User bấm Spin → 3 cuộn quay độc lập → kết quả là tổ hợp 3 biểu tượng. Hỗ trợ nhiều line (1/3/5 line) và combo mapping phức tạp [1][2]. |
| **F2** | Wheel Type: **Scratch Card** | User nhận 1 tấm thẻ cào ảo, vuốt ngón tay để cào lớp phủ → lộ ra phần thưởng. Hỗ trợ 3/6/9 ô và cơ chế "match 3" thưởng thêm [1][2]. |
| **F3** | **Pity System** | Tăng xác suất lũy tiến sau mỗi lần trượt. Có 2 mode: **BOOST** (tăng dần) và **GUARANTEED** (chắc chắn trúng sau N lần trượt) [1][2]. |
| **F4** | **A/B Testing** cho Reward Pool | Cho phép config 2 pool khác nhau, phân luồng ngẫu nhiên theo traffic split để tối ưu reward [1][2]. |
| **F5** | **Streak Bonus** | Token thưởng thêm khi user duy trì streak (chuỗi ngày đăng nhập liên tiếp) đủ số ngày [1][2]. |
| **F6** | **Campaign Analytics Dashboard** | Ops team có thể tự xem số liệu và export CSV mà không cần hỏi Dev [1][2]. |

### Các tính năng được cập nhật (Updated)

| Mã | Tính năng | Thay đổi |
|----|-----------|----------|
| **U1** | **Slot count** | Mở rộng hỗ trợ 6 / 8 / 10 / 12 slot (v1 chỉ có 8 và 12) [1][3]. |
| **U2** | **Task condition** | Hỗ trợ combo & dependent task (nhiệm vụ phụ thuộc lẫn nhau) [1]. |

### Tóm tắt mục tiêu v2

- **Tránh nhàm chán**: 2 game type mới thay đổi trải nghiệm mỗi campaign [1].
- **Tăng fairness cảm nhận**: Pity system giúp user không bao giờ cảm thấy "đen mãi" [1].
- **Tăng insight cho Biz**: Analytics dashboard + A/B test để tối ưu reward [1].
- **Tăng daily retention**: Streak bonus gắn với thói quen hàng ngày [1].

---

_Lưu ý: Tất cả tính năng v1 (Campaign CRUD, Reward Pool, Task list, Full UI config...) vẫn được giữ nguyên trong v2_ [1][4].

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


---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Mock Doc (v2 changelog) | Agent trả lời | Kết quả |
|---|---|---|---|
| F1 — Wheel Type: Slot Machine | ✅ F1 trong changelog | ✅ đề cập | ✅ Đúng |
| F2 — Wheel Type: Scratch Card | ✅ F2 trong changelog | ✅ đề cập | ✅ Đúng |
| F3 — Pity System | ✅ F3 trong changelog | ✅ đề cập, 2 mode BOOST/GUARANTEED | ✅ Đúng |
| F4 — A/B Testing Reward Pool | ✅ F4 trong changelog | ✅ đề cập | ✅ Đúng |
| F5 — Streak Bonus | ✅ F5 trong changelog | ✅ đề cập | ✅ Đúng |
| F6 — Campaign Analytics Dashboard | ✅ F6 trong changelog | ✅ đề cập | ✅ Đúng |
| U1 — Slot count 6/8/10/12 | ✅ U1 Updated | ✅ đề cập | ✅ Đúng |
| U2 — Task combo & dependent | ✅ U2 Updated | ✅ đề cập | ✅ Đúng |

## 📝 Ghi chú

- Liệt kê đầy đủ tất cả 6 New Feature + 2 Update từ changelog v2
- Explicit routing hoạt động đúng — không cần router suy luận
