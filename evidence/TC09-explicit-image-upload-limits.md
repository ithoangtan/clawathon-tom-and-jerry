# TC09 — Explicit grow_enablement: Image Upload Limits

| Field | Value |
|-------|-------|
| **Test ID** | TC09 |
| **Mode** | Explicit department — `target_departments: ["grow_enablement"]` |
| **Type** | Happy case — thông tin config cụ thể |
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
  "question": "Khi upload ảnh cho campaign Lucky Wheel, có giới hạn dung lượng không? Kích thước recommended là bao nhiêu?",
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
| **citations** | 2 |
| **confidence** | `0.560` |

### Answer

## Giới hạn & kích thước khi upload ảnh cho Lucky Wheel

Có, có giới hạn dung lượng và kích thước recommended cho từng loại ảnh:

### Ảnh nền campaign (Background)
- **Kích thước khuyến nghị:** 750×1334px
- **Định dạng:** PNG hoặc JPG
- **Dung lượng tối đa:** < 500KB [1]

### Ảnh vòng quay (Wheel)
- **Kích thước:** Vuông, tối thiểu ≥ 600×600px
- **Định dạng:** PNG với nền trong suốt [1]

### Ảnh kim chỉ (Pointer)
- Chỉ cần upload ảnh kim chỉ, không có thông số kích thước cụ thể được đề cập [1]

### Icon hiển thị trên ô (Slot)
- **Kích thước:** ~100×100px
- **Định dạng:** PNG [1]

---

**Lưu ý:** Nếu không có ảnh, bạn có thể chọn màu hex thay thế cho ảnh nền campaign. [1]

### Citations

**[1]** [Lucky Wheel Campaign Operations Guide: Creation, Configuration, and Monitoring Steps](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/360467/Lucky+Wheel+Campaign+Operations+Guide+Creation+Configuration+and+Monitoring+Steps)
  - Doc type: `Operation` | Modified: `2026-06-11`
  - Excerpt: _Lucky Wheel – Operations Guide Audience: Campaign Operations Team Mục đích: Hướng dẫn tạo & vận hành campaign Lucky Wheel trên Config Tool Version: 1.0 1. Quy trình tạo Campaign wide 760 2. Các bước c_

**[2]** [Lucky Wheel Campaign: Features, Goals, and Management Overview](https://ithoangtan-clawathon.atlassian.net/wiki/spaces/ClawathonGrow/pages/327880/Lucky+Wheel+Campaign+Features+Goals+and+Management+Overview)
  - Doc type: `Operation` | Modified: `2026-06-11`
  - Excerpt: _PRD – Lucky Wheel Campaign Audience: Product Owner Version: 1.0 Status: Living document 1. Tổng quan tính năng Lucky Wheel là một mini-game dạng vòng quay may mắn được nhúng vào trong app. Mỗi "Campai_


---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Mock Doc (Ops Guide v1 §2 Bước 2) | Agent trả lời | Kết quả |
|---|---|---|---|
| Background: 750×1334px | ✅ "khuyến nghị: 750×1334px" | ✅ đúng | ✅ Đúng |
| Background: PNG/JPG | ✅ "PNG/JPG" | ✅ đúng | ✅ Đúng |
| Background: < 500KB | ✅ "< 500KB" | ✅ đúng | ✅ Đúng |
| Wheel image: PNG transparent, ≥ 600×600px | ✅ "PNG với nền trong suốt, kích thước vuông ≥ 600×600px" | ✅ đúng | ✅ Đúng |
| Slot icon: ~100×100px PNG | ✅ "PNG, ~100×100px" | ✅ đúng | ✅ Đúng |
| Fallback: chọn màu hex nếu không có ảnh | ✅ ops guide | ✅ đề cập | ✅ Đúng |

## 📝 Ghi chú

- Câu hỏi rất cụ thể (image specs) — agent retrieve đúng chunk từ Ops Guide và trả lời chính xác 100%
- Confidence thấp (`0.560`) nhưng answer vẫn chính xác — GRADE_THRESHOLD=0.3 hoạt động tốt cho câu hỏi factual cụ thể
