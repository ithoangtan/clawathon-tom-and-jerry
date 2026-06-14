# TC25 — UI: New session — empty state & suggested prompts

| Field | Value |
|-------|-------|
| **Test ID** | TC25 |
| **Mode** | UI — Browser interaction |
| **Type** | Happy case — new session empty state |
| **Verdict** | ✅ PASS |

---

## 🖱️ UI Interaction

| Step | Action | Selector / Method |
|------|--------|-------------------|
| 1 | Navigate to app root | `http://localhost:5173/` |
| 2 | Click "New session" button | `button: "New session"` (in sidebar) |
| 3 | Observe empty state | Chat area resets to welcome screen |

---

## 📸 Observed UI State

**Chat area (new session):**
- Large centered heading: **"How can I help?"**
- Subtext: "Ask a question to get started. Every answer includes citations from Confluence or Drive."
- Empty text input with placeholder: "Ask about Zalopay policies, runbooks, or procedures…"
- Send button (disabled until text entered)
- Bottom bar: `Auto-route (Agent Center)` chip + `+` button

**Suggested prompts (3 chips):**
1. "What is the escalation process when a fraud alert triggers on a high-value merchant transaction?"
2. "Walk me through the settlement reconciliation steps with a partner bank after a failed batch."
3. "What KYC re-verification is required when a merchant's transaction volume doubles?"

**Session sidebar:**
- Previous sessions still visible in history
- New session does NOT appear in list until first message sent

---

## 🔍 Đối chiếu UI

| UI Element | Kỳ vọng | Thực tế | Kết quả |
|---|---|---|---|
| "How can I help?" heading | ✅ | ✅ | ✅ |
| Suggested prompts visible | ✅ 3 chips | ✅ 3 chips | ✅ |
| Auto-route chip present | ✅ | ✅ | ✅ |
| Empty input (no stale text) | ✅ | ✅ | ✅ |
| Previous sessions preserved | ✅ | ✅ in sidebar | ✅ |
| New session not in list until msg sent | ✅ | ✅ | ✅ |

---

## 📝 Ghi chú

- New session button creates a fresh UUID session locally, not persisted until first chat
- Suggested prompts cover multi-dept scenarios: risk escalation, bank reconciliation, KYC
- Auto-route is default mode — user can override by clicking `+` to pick dept
