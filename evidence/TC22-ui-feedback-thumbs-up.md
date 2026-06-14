# TC22 — UI: Feedback thumbs up → confirmation toast

| Field | Value |
|-------|-------|
| **Test ID** | TC22 |
| **Mode** | UI — Browser interaction |
| **Type** | Happy case — feedback submission flow |
| **Verdict** | ✅ PASS |

---

## 🖱️ UI Interaction

| Step | Action | Selector / Method |
|------|--------|-------------------|
| 1 | Navigate to chat session with answered response | `http://localhost:5173/` |
| 2 | Scroll to bottom of answer | `[role="log"].scrollTop = scrollHeight` |
| 3 | Find "Was this helpful?" section | Visible at bottom of response card |
| 4 | Click 👍 (thumbs up) | First button in helpful section |
| 5 | Observe confirmation | Inline text appears |

---

## 📸 Observed UI State

**Before click:**
- `Was this helpful?` label
- 👍 button (unfilled outline)
- 👎 button (unfilled outline)

**After clicking 👍:**
- 👍 button highlighted (filled blue/active state)
- `Thanks for your feedback!` text appears inline next to 👎 button
- Buttons remain visible (can change vote)

---

## 🔍 Đối chiếu UI

| UI Element | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| Thumbs up button clickable | ✅ | ✅ | ✅ |
| POST /feedback called with `rating: "up"` | 204 | 204 No Content | ✅ |
| Confirmation text displayed | "Thanks for your feedback!" | ✅ exact match | ✅ |
| 👍 button visual change (active) | ✅ highlighted | ✅ filled blue | ✅ |
| No page reload | ✅ | ✅ inline update | ✅ |

---

## 📝 Ghi chú

- Feedback submission là optimistic UI update — text xuất hiện ngay sau click, không cần reload
- Backend xác nhận: `POST /feedback` → `204 No Content`
- 👍 button highlighted sau khi selected — clear visual state
- API confirmed (TC18): feedback_id từ chat response được dùng để submit feedback
