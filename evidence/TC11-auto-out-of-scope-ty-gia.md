# TC11 — Auto-route: Out-of-scope — tỷ giá USD/VND

| Field | Value |
|-------|-------|
| **Test ID** | TC11 |
| **Mode** | Auto-route — `target_departments: null` |
| **Type** | Edge — out-of-scope real-time data |
| **Verdict** | ✅ PASS |

---

## 📤 Request

```
POST http://localhost:8080/chat
X-GreenNode-AgentBase-User-Id: qc-tester
X-GreenNode-AgentBase-Session-Id: tc11-<timestamp>
Content-Type: application/json
```

```json
{
  "question": "Tỷ giá USD/VND hôm nay là bao nhiêu?"
}
```

---

## 📥 Response

| Field | Value |
|-------|-------|
| **status** | ❌ refused |
| **refusal_reason** | `out_of_scope` |
| **lang** | `vi` |
| **source_departments** | `[]` |
| **citations** | 0 |
| **confidence** | `0.0` |

### Answer

> Câu hỏi này nằm ngoài phạm vi tài liệu đã lập chỉ mục (ví dụ: số liệu thời gian thực).
>
> **Liên hệ tiếp:**
> - **Quản lý Rủi ro**: Teams **Quản lý Rủi ro** hoặc Nguyễn Thị Lan (trưởng bộ phận)
> - **Phát triển Kinh doanh**: Liên hệ Trần Minh (quản lý kênh) …

---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| `status` | `refused` | `refused` | ✅ |
| `refusal_reason` | `out_of_scope` | `out_of_scope` | ✅ |
| `lang` | `vi` | `vi` | ✅ |
| `citations` | 0 | 0 | ✅ |
| Không hallucinate tỷ giá | ✅ không trả tỷ giá | ✅ từ chối đúng | ✅ |

---

## 📝 Ghi chú

- Router nhận diện đúng câu hỏi về dữ liệu thời gian thực (tỷ giá) là out-of-scope
- `refusal_reason: out_of_scope` là giá trị chính xác theo spec — phân biệt với `not_in_docs`
- Response kèm gợi ý liên hệ bộ phận phù hợp (graceful degradation)
