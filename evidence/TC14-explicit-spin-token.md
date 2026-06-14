# TC14 — Explicit dept: Spin Token là gì?

| Field | Value |
|-------|-------|
| **Test ID** | TC14 |
| **Mode** | Explicit — `target_departments: ["grow_enablement"]` |
| **Type** | Happy case — explicit department pinning |
| **Verdict** | ✅ PASS |

---

## 📤 Request

```
POST http://localhost:8080/chat
X-GreenNode-AgentBase-User-Id: qc-tester
X-GreenNode-AgentBase-Session-Id: tc14-<timestamp>
Content-Type: application/json
```

```json
{
  "question": "Spin Token là gì? Cách kiếm Spin Token?",
  "target_departments": ["grow_enablement"]
}
```

---

## 📥 Response

| Field | Value |
|-------|-------|
| **status** | ✅ answered |
| **lang** | `vi` |
| **source_departments** | `['grow_enablement']` |
| **citations** | 6 |
| **confidence** | `0.427` |

### Answer (excerpt)

```
## Spin Token là gì?

**Spin Token** là đơn vị (token) dùng để quay vòng quay may mắn trong Lucky Wheel.
Mỗi campaign có thể cấu hình loại token riêng như: coin, egg, ticket hoặc các đơn vị tùy chỉnh khác [1].

Spin Token tương tự như "tiền tệ" để user sử dụng tính năng quay.
Mỗi lần quay sẽ tiêu tốn một số lượng token nhất định (thường là 1 token cho quay 1 lần,
hoặc N token cho quay 10 lần).
```

---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| `status` | `answered` | `answered` | ✅ |
| `lang` | `vi` | `vi` | ✅ |
| Explicit dept honoured | `grow_enablement` | `['grow_enablement']` | ✅ |
| Định nghĩa Spin Token chính xác | "đơn vị dùng để quay" | ✅ match | ✅ |
| Cách kiếm token | ✅ trong docs | ✅ có trong answer | ✅ |
| `citations` ≥ 3 | ✅ | 6 | ✅ |

---

## 📝 Ghi chú

- `target_departments: ["grow_enablement"]` được hệ thống tôn trọng — source_departments trả đúng
- confidence = 0.427 — đủ cao trên threshold 0.3
- 6 citations từ grow docs xác nhận retrieval phong phú
