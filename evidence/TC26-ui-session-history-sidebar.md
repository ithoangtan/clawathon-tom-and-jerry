# TC26 — UI: Session history sidebar

| Field | Value |
|-------|-------|
| **Test ID** | TC26 |
| **Mode** | UI — Browser interaction |
| **Type** | Happy case — session persistence & navigation |
| **Verdict** | ✅ PASS |

---

## 🖱️ UI Interaction

| Step | Action | Selector / Method |
|------|--------|-------------------|
| 1 | Open app | `http://localhost:5173/` |
| 2 | Observe session history in left sidebar | `[aria-label="Session history"]` |
| 3 | Click on "Lucky Wheel là gì?" (Not covered) session | `li.textContent.includes("Not covered")` → click |
| 4 | Observe session loaded in main area | Previous Q&A replayed |

---

## 📸 Observed UI State

**Session history sidebar shows:**

| Session | Timestamp | Status chip | Dept chip |
|---------|-----------|-------------|-----------|
| "Lucky Wheel v2 có những tính năng mới gì so với v1?" | Jun 15, 2026, 12:43 AM | `Answered` (green) | `Growth Enablement` (teal) |
| "Lucky Wheel là gì?" | Jun 15, 2026, 12:33 AM | `Answered` (green) | `Growth Enablement` (teal) |
| "Lucky Wheel là gì?" | Jun 15, 2026, 12:28 AM | `Not covered in the docs` (red/dark) | — |

**Search box:**
- Placeholder: "Search sessions"
- Filters sessions by title in real-time

---

## 🔍 Đối chiếu UI

| UI Element | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| Sessions listed in reverse chronological order | ✅ | ✅ newest first | ✅ |
| Status chips per session | `Answered`/`Not covered` | ✅ correct per session | ✅ |
| Dept chips on answered sessions | ✅ | `Growth Enablement` | ✅ |
| Session title truncated correctly | ✅ | ✅ | ✅ |
| Search box present | ✅ | ✅ | ✅ |
| Click session loads history | ✅ | ✅ navigates to session | ✅ |

---

## 📝 Ghi chú

- Sessions stored in localStorage / IndexedDB on device — persist across page reloads
- Status chip reflects final outcome of the session (answered vs refused)
- Dept chip shows which department answered the question
- "Not covered in the docs" session shows no dept chip (no dept processed it)
- Sessions can be searched by title text
