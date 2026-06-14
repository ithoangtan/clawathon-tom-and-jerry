# TC19 — Auth & validation error cases

| Field | Value |
|-------|-------|
| **Test ID** | TC19 |
| **Mode** | API — `POST /chat` với invalid/missing headers |
| **Type** | Edge — input validation & auth guards |
| **Verdict** | ✅ PASS |

---

## 📤 Requests

| Sub-case | Request | Expected |
|----------|---------|----------|
| TC19a | Missing `X-GreenNode-AgentBase-User-Id` | 400 |
| TC19b | Missing `X-GreenNode-AgentBase-Session-Id` | 400 |
| TC19c | Empty question `""` | 422 |
| TC19d | Question > 4000 chars | 422 |
| TC19e | Extra unknown field | 422 |
| TC19f | Malformed JSON body | 422 |

---

## 📥 Response

| Sub-case | status_code | detail |
|----------|-------------|--------|
| TC19a — missing User-Id | `400` | `"Missing required header: X-GreenNode-AgentBase-User-Id"` |
| TC19b — missing Session-Id | `400` | `"Missing required header: X-GreenNode-AgentBase-Session-Id"` |
| TC19c — empty question | `422` | Pydantic validation error |
| TC19d — question too long (4001 chars) | `422` | Pydantic validation error |
| TC19e — extra field | `422` | Pydantic `extra=forbid` error |
| TC19f — malformed JSON | `422` | JSON parse error |

---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| Missing User-Id → 400 | ✅ | 400 | ✅ |
| Missing Session-Id → 400 | ✅ | 400 | ✅ |
| Error message mentions exact missing header | ✅ | ✅ exact match | ✅ |
| Empty question → 422 | ✅ | 422 | ✅ |
| Question >4000 chars → 422 | ✅ | 422 | ✅ |
| Extra field → 422 (`extra=forbid`) | ✅ | 422 | ✅ |
| Malformed JSON → 422 | ✅ | 422 | ✅ |

---

## 📝 Ghi chú

- 400 dành cho auth headers missing (gateway-level validation)
- 422 dành cho body schema validation (Pydantic FastAPI)
- `extra=forbid` trên `ChatRequest` — API từ chối bất kỳ field không khai báo, tránh injection
- Question max length = 4000 chars (per spec)
- Error detail messages thân thiện — mention tên header thiếu, giúp client debug dễ
