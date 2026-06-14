# TC21 — UI: Chat page — answered response with citations panel

| Field | Value |
|-------|-------|
| **Test ID** | TC21 |
| **Mode** | UI — Browser interaction |
| **Type** | Happy case — chat answered response rendering |
| **Verdict** | ✅ PASS |

---

## 🖱️ UI Interaction

| Step | Action | Selector / Method |
|------|--------|-------------------|
| 1 | Navigate to app | `http://localhost:5173/` |
| 2 | Type question | `textarea[placeholder*="Ask about"]` |
| 3 | Submit | Press Enter or click Send |
| 4 | Wait for response | Pipeline loading visible then answer rendered |
| 5 | Scroll to bottom | `[role="log"].scrollTop = scrollHeight` |

**Question asked:** "Lucky Wheel v2 có những tính năng mới gì so với v1?"

---

## 📸 Observed UI State

**Top of response:**
- `Growth Enablement` dept chip (teal badge)
- `Answered` status chip (green)
- `Medium · 68%` confidence badge (orange)
- `minimax/minimax-m2.5` model chip

**Answer body:**
- Markdown rendered: headings, bold text, table with F1–F6 features
- Citation superscripts `[1]` `[2]` inline in text — clickable

**Bottom of response:**
- `SOURCES (4)` section with expandable citation list
- Each citation: title, URL (ithoangtan-clawathon.atlassian.net), source type `CONFLUENCE`, date
- `Was this helpful?` with 👍 👎 buttons
- `Model: minimax/minimax-m2.5` badge

---

## 🔍 Đối chiếu UI

| UI Element | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| Dept chip render | `Growth Enablement` | ✅ teal badge | ✅ |
| Status chip | `Answered` (green) | ✅ | ✅ |
| Confidence badge | present | `Medium · 68%` | ✅ |
| Model badge | present | `minimax/minimax-m2.5` | ✅ |
| Markdown tables rendered | ✅ | ✅ feature table F1–F6 | ✅ |
| Inline citation superscripts | ✅ `[1]` clickable | ✅ | ✅ |
| SOURCES panel | ✅ | 4 sources with links | ✅ |
| Feedback buttons | ✅ 👍 👎 | ✅ visible | ✅ |

---

## 📝 Ghi chú

- Markdown rendering đầy đủ: headers H2/H3, bold, table, bullet list
- Citations superscript `[1]` là số trong ô vuông màu xanh lam — clickable scroll to source
- SOURCES panel hiện domain `ithoangtan-clawathon.atlassian.net` (Confluence)
- Copy response button (`⧉`) ở top-right của answer card
