# TC12 — Bilingual VI: Risk dept — quy trình leo thang gian lận

| Field | Value |
|-------|-------|
| **Test ID** | TC12 |
| **Mode** | Explicit — `target_departments: ["risk"]` |
| **Type** | Happy case — VI bilingual + risk dept routing |
| **Verdict** | ✅ PASS |

---

## 📤 Request

```
POST http://localhost:8080/chat
X-GreenNode-AgentBase-User-Id: qc-tester
X-GreenNode-AgentBase-Session-Id: tc12-<timestamp>
Content-Type: application/json
```

```json
{
  "question": "Quy trình leo thang khi phát hiện cảnh báo gian lận?",
  "target_departments": ["risk"]
}
```

---

## 📥 Response

| Field | Value |
|-------|-------|
| **status** | ✅ answered |
| **lang** | `vi` |
| **source_departments** | `['risk']` |
| **citations** | 6 |
| **confidence** | (retrieved from risk dept) |

### Answer (excerpt)

```
# Quy Trình Leo Thang Khi Phát Hiện Cảnh Báo Gian Lận

## 1. Cấp Độ Phát Hiện & Cảnh Báo

### Giám sát thời gian thực
- **Rules Engine**: Tự động gắn cờ cho các mô hình rõ ràng như định hình (structuring), vận tốc cao [1]
- ...
```

---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| `status` | `answered` | `answered` | ✅ |
| `lang` | `vi` | `vi` | ✅ |
| `source_departments` | `['risk']` | `['risk']` | ✅ |
| `citations` > 0 | ✅ | 6 citations | ✅ |
| Nội dung về quy trình leo thang | ✅ có trong risk docs | ✅ trả về đúng | ✅ |

---

## 📝 Ghi chú

- Explicit routing `target_departments: ["risk"]` → hệ thống route đúng đến Risk Management
- Risk Confluence space (`ClawathonRisk`) đã được index: 13 pages / 37 chunks
- Câu hỏi tiếng Việt → câu trả lời tiếng Việt (`lang: vi`) — bilingual detection hoạt động đúng
- 6 citations từ risk docs xác nhận retrieval chất lượng cao
