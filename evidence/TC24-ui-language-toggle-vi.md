# TC24 — UI: Language toggle EN → VI

| Field | Value |
|-------|-------|
| **Test ID** | TC24 |
| **Mode** | UI — Browser interaction |
| **Type** | Happy case — bilingual UI toggle |
| **Verdict** | ✅ PASS |

---

## 🖱️ UI Interaction

| Step | Action | Selector / Method |
|------|--------|-------------------|
| 1 | Observe EN is active | `button "Switch to English"` highlighted |
| 2 | Click "VI" toggle | `button: "Switch to Vietnamese"` (text "VI") |
| 3 | Observe full UI language change | All text translates immediately |

---

## 📸 Observed UI State

**Before (EN active):**

| UI Text | EN |
|---------|----|
| App title | "Zalopay Knowledge" |
| Nav: Chat | "Chat" |
| Nav: Dashboard | "Dashboard" |
| Nav: Settings | "Settings" |
| Sidebar header | "Session history" |
| Sidebar subtext | "Recent conversations saved on this device." |
| New session button | "New session" |
| Empty state heading | "How can I help?" |
| Empty state subtext | "Ask a question to get started…" |
| System status | "System healthy" |
| Session label | "Answered" |

**After clicking VI:**

| UI Text | VI |
|---------|----|
| App title | "Tri thức Zalopay" |
| Nav: Chat | "Hỏi đáp" |
| Nav: Dashboard | "Bảng điều khiển" |
| Nav: Settings | "Cài đặt" |
| Sidebar header | "Lịch sử phiên hỏi đáp" |
| Sidebar subtext | "Các cuộc hội thoại gần đây được lưu trên thiết bị này." |
| New session button | "Phiên mới" |
| Empty state heading | "Tôi có thể giúp gì?" |
| System status | "Hệ thống hoạt động" |
| Session label | "Đã trả lời" |
| Dept chip | "Phát triển Kinh doanh" (Growth Enablement) |
| "Not covered" label | "Không có thông tin trong tài liệu" |

---

## 🔍 Đối chiếu UI

| UI Element | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| All navigation items translated | ✅ | ✅ đầy đủ | ✅ |
| Session sidebar labels translated | ✅ | ✅ | ✅ |
| Empty state heading translated | ✅ | "Tôi có thể giúp gì?" | ✅ |
| Department chips translated | ✅ | "Phát triển Kinh doanh" | ✅ |
| No page reload (instant toggle) | ✅ | ✅ instant | ✅ |
| "VI" button highlighted after click | ✅ | ✅ | ✅ |

---

## 📝 Ghi chú

- Language toggle is instant — full i18n without page reload (React state)
- Session history labels, dept chips, status chips all translated
- Placeholder in chat input also changes: "Hỏi về chính sách, quy trình hoặc runbook của Zalopay…"
- Setting persists to localStorage — re-opening app stays in VI
