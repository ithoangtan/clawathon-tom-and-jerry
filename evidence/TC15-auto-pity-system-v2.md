# TC15 — Auto-route: Pity System trong Lucky Wheel v2

| Field | Value |
|-------|-------|
| **Test ID** | TC15 |
| **Mode** | Auto-route |
| **Type** | Happy case — technical feature query |
| **Verdict** | ✅ PASS |

---

## 📤 Request

```
POST http://localhost:8080/chat
X-GreenNode-AgentBase-User-Id: qc-tester
X-GreenNode-AgentBase-Session-Id: tc15-<timestamp>
Content-Type: application/json
```

```json
{
  "question": "Pity System trong Lucky Wheel v2 hoạt động như thế nào?"
}
```

---

## 📥 Response

| Field | Value |
|-------|-------|
| **status** | ✅ answered |
| **lang** | `vi` |
| **source_departments** | `['grow_enablement']` |
| **citations** | 3 |
| **confidence** | `0.64` |
| **feedback_id** | `40156020-0fe7-4be0-b5fd-7f883ec35b25` |

### Answer (excerpt)

```
## Pity System trong Lucky Wheel v2

### Tổng quan
Pity System là tính năng giúp tăng cảm nhận công bằng cho người dùng —
đảm bảo sau nhiều lần không trúng thưởng (trượt), xác suất nhận phần thưởng tốt
sẽ tăng dần hoặc được cam kết [1][3].

### Cách bật và cấu hình
**Bước 1:** Bật tính năng bằng toggle ON trong phần "Advanced Settings" của campaign [1].
**Bước 2:** Chọn một trong hai mode hoạt động [1]:

| Mode   | Hành vi                                     |
|--------|---------------------------------------------|
| BOOST  | Sau N lần trượt, xác suất tăng dần theo %  |
| GUARANTEED | Sau N lần trượt, lần thứ N+1 chắc chắn trúng |
```

---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| `status` | `answered` | `answered` | ✅ |
| Định nghĩa Pity System | Tăng xác suất sau N lần trượt | ✅ match | ✅ |
| 2 modes: BOOST & GUARANTEED | ✅ trong v2 docs | ✅ cả 2 modes | ✅ |
| Hướng dẫn cấu hình bật toggle | ✅ trong ops guide v2 | ✅ có | ✅ |
| confidence > 0.3 | ✅ | 0.64 | ✅ |

---

## 📝 Ghi chú

- confidence = 0.64 — cao nhất trong các TC grow_enablement, phản ánh câu hỏi targeted
- 3 citations từ cả PRD v2, Ops Guide v2, Tech Doc v2 — cross-doc synthesis tốt
- Pity counter reset mechanism: TC này không test sâu (xem BUG-02 trong README)
