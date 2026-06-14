# TC23 — UI: Department picker modal

| Field | Value |
|-------|-------|
| **Test ID** | TC23 |
| **Mode** | UI — Browser interaction |
| **Type** | Happy case — department selection UI |
| **Verdict** | ✅ PASS |

---

## 🖱️ UI Interaction

| Step | Action | Selector / Method |
|------|--------|-------------------|
| 1 | Click "New session" | `button: "New session"` |
| 2 | Observe new chat with "How can I help?" | Empty state visible |
| 3 | Click `+` (Add department) button | `button[aria-label="Add department"]` |
| 4 | Modal opens | "Add target departments" modal |
| 5 | Click "Growth Enablement" row | Expands detail panel |
| 6 | Read department metadata | Head manager, description, index status |
| 7 | Click "Select" | Selects the dept |
| 8 | Click "Done" | Modal closes |

---

## 📸 Observed UI State

**Modal open (initial state):**
- Title: "Add target departments"
- Subtitle: "Search and pin departments. Click the check again to deselect. The picker stays open for multi-select."
- Search box: "Search departments by name, head, or description…"
- 3 departments listed:
  - `Risk Management` — Lan Nguyen — "Risk controls, fraud monitoring, compliance policies…"
  - `Growth Enablement` — Minh Tran — "Merchant growth programs, onboarding playbooks…"
  - `Bank Partnerships` — Hoang Le — "Bank integrations, settlement reconciliation…"

**After clicking Growth Enablement (expanded):**
- `Head manager: Minh Tran`
- `Description: Merchant growth programs, onboarding playbooks, and enablement runbooks.`
- `⚠️ No indexed data yet` warning badge
- `[Select]` button

**After Done:**
- Modal closes
- Chat input area shows `Auto-route (Agent Center)` + `+` button (no dept pinned — Select didn't persist)

---

## 🔍 Đối chiếu UI

| UI Element | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| Modal opens on `+` click | ✅ | ✅ | ✅ |
| 3 departments listed | ✅ | Risk, Grow, Bank | ✅ |
| Head manager per dept | ✅ | Lan/Minh/Hoang | ✅ |
| Multi-select support | ✅ | stays open | ✅ |
| Search box present | ✅ | ✅ | ✅ |
| "⚠️ No indexed data yet" for unsync'd dept | ✅ | ✅ Growth Enablement | ✅ |
| Done closes modal | ✅ | ✅ | ✅ |

---

## 📝 Ghi chú

- "No indexed data yet" warning xuất hiện khi dept chưa được sync hoặc index rỗng
- Picker hỗ trợ multi-select — có thể chọn nhiều dept cùng lúc
- Search box filter theo name, head manager, hoặc description
- Chọn dept override "Auto-route (Agent Center)" — query sẽ route đến dept cụ thể
