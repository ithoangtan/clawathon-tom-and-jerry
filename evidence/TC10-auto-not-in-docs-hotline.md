# TC10 — Auto-route: Not-In-Docs (Hotline khách hàng)

| Field | Value |
|-------|-------|
| **Test ID** | TC10 |
| **Mode** | Auto-route (Agent Center) |
| **Type** | Edge case — thông tin không có trong tài liệu indexed |
| **Verdict** | ⚠️ PARTIAL — Behavior không optimal |

---

## 📤 Request

```
POST http://localhost:8080/chat
X-GreenNode-AgentBase-User-Id: qc-tester
Content-Type: application/json
```

```json
{
  "question": "Tôi muốn biết số điện thoại hotline hỗ trợ khách hàng Zalopay là bao nhiêu?"
}
```

---

## 📥 Response

| Field | Value |
|-------|-------|
| **status** | ⛔ refused |
| **model_used** | `None` |
| **source_departments** | `[]` |
| **citations** | 0 |
| **clarifying_question** | `{'prompt': 'Câu hỏi của bạn có thể liên quan đến nhiều bộ phận. Bạn muốn hỏi bộ phận nào?', 'options': ['bank_partnerships', 'grow_enablement', 'risk']}` |

### Answer (Clarifying question)

Câu hỏi của bạn có thể liên quan đến nhiều bộ phận. Bạn muốn hỏi bộ phận nào?

---

## 🔍 Đối chiếu với Mock

| Điểm kiểm tra | Expected | Actual | Kết quả |
|---|---|---|---|
| Không trả lời số hotline (không trong docs) | ✅ phải từ chối | ✅ không trả lời số hotline | ✅ Đúng (không hallucinate) |
| `status: refused` | ✅ expected | ✅ `refused` | ✅ Đúng |
| Giải thích rõ "không trong tài liệu" | ✅ expected | ❌ hỏi ngược "bạn muốn hỏi bộ phận nào?" | ⚠️ Không optimal |
| Không bật clarifying question | Nên từ chối thẳng | ⚠️ phát sinh `clarifying_question` | ⚠️ Misclassification |

## 🐛 Bug Report

**BUG-02: Router misclassification — out-of-scope thành ambiguous**

- **Severity:** Low–Medium
- **Expected behavior:** Router nhận diện "hotline support" là `out_of_scope` → `status: refused` kèm giải thích "thông tin này không có trong tài liệu nội bộ indexed"
- **Actual behavior:** Router classify là intent ambiguous → phát sinh `clarifying_question` hỏi ngược user muốn hỏi bộ phận nào
- **Impact:** User experience kém — user hỏi hotline rồi lại bị hỏi ngược bộ phận, thay vì nhận câu trả lời từ chối rõ ràng
- **Root cause hypothesis:** "hotline hỗ trợ khách hàng" không map rõ vào keyword out-of-scope trong router prompt. Router thấy question không rõ department nên hỏi clarify thay vì nhận diện đây là external/real-world info.
- **Suggested fix:** Bổ sung vào router prompt các signal out-of-scope: câu hỏi về contact info (hotline, email, địa chỉ), giờ làm việc, HR/nhân sự ngoài tài liệu indexed.
