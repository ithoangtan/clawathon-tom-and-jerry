# TC18 — Feedback round-trip: chat → submit thumbs up

| Field | Value |
|-------|-------|
| **Test ID** | TC18 |
| **Mode** | API — `POST /chat` → `POST /feedback` |
| **Type** | Happy case — end-to-end feedback flow |
| **Verdict** | ✅ PASS |

---

## 📤 Request

### Step 1 — Chat

```
POST http://localhost:8080/chat
X-GreenNode-AgentBase-User-Id: qc-tester
X-GreenNode-AgentBase-Session-Id: tc18-<timestamp>
Content-Type: application/json
```

```json
{
  "question": "Lucky Wheel v2 có Pity System không?"
}
```

### Step 2 — Submit Feedback

```
POST http://localhost:8080/feedback
X-GreenNode-AgentBase-User-Id: qc-tester
Content-Type: application/json
```

```json
{
  "feedback_id": "6f1bf53f-9e1b-4740-9e6c-327327ea305d",
  "rating": "up",
  "comment": "Accurate"
}
```

---

## 📥 Response

### Step 1 — Chat Response

| Field | Value |
|-------|-------|
| **status** | `answered` |
| **feedback_id** | `6f1bf53f-9e1b-4740-9e6c-327327ea305d` |

### Step 2 — Feedback Response

| Field | Value |
|-------|-------|
| **status_code** | `204 No Content` |
| **body** | _(empty)_ |

---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| Chat trả về `feedback_id` là UUID | ✅ | valid UUID | ✅ |
| `POST /feedback` với UUID hợp lệ → 204 | ✅ | 204 | ✅ |
| Body rỗng khi 204 | ✅ | empty | ✅ |
| `rating: "up"` accepted | ✅ | accepted | ✅ |
| `comment` optional field accepted | ✅ | accepted | ✅ |

---

## 📝 Ghi chú

- feedback_id được generate tự động bởi backend và trả trong chat response
- Workflow: user nhận answer → copy feedback_id → POST /feedback với rating (up/down)
- 204 No Content là HTTP semantics đúng cho "received but no content to return"
- Comment field optional — API chấp nhận cả khi có lẫn không có
