# TC33 — Feature: Proactive Intelligence — Knowledge Gap Tracker (Admin UI)

| Field | Value |
|-------|-------|
| **Test ID** | TC33 |
| **Mode** | UI — Browser interaction |
| **Type** | New feature — admin knowledge gap panel |
| **Verdict** | ✅ PASS |

---

## Feature Overview

A new "Knowledge Gaps" card appears at the bottom of the Admin page. It shows:
1. **Refused questions** — questions the agent couldn't answer (grouped, counted, last-seen)
2. **Low-rated documents** — source docs with net negative thumbs-down feedback
3. **Export CSV** — one-click download of all gap data
4. **Empty state** — green checkmark when no gaps detected

---

## 🖱️ UI Interaction

| Step | Action | Details |
|------|--------|---------|
| 1 | Navigate to `/admin` | Admin page loads |
| 2 | Scroll to bottom | Knowledge Gaps card visible |
| 3 | Verify card title | "Knowledge Gaps" |
| 4 | Verify subtitle | "Questions the agent couldn't answer — potential documentation gaps" |
| 5 | Verify empty state | ✅ "No gaps detected yet — all questions are being answered!" |

---

## 📸 Observed UI State

**Card renders correctly:**
- Title: "Knowledge Gaps"
- Subtitle: "Questions the agent couldn't answer — potential documentation gaps"
- Empty state: green border box with ✅ icon and positive message

**When data is present (design):**
- ❓ "Refused Questions" section: red badges with "Asked N times"
- 👎 "Low-Rated Documents" section: yellow badges with "↓N / ↑N" ratings
- "Export CSV" button top-right corner

---

## 🔧 Implementation

| Component | File |
|-----------|------|
| Panel component | `frontend/src/components/admin/KnowledgeGapPanel.tsx` |
| Admin page mount | `frontend/src/pages/AdminPage.tsx` |
| API endpoint | `app/api/routes.py` → `GET /api/knowledge-gaps` |
| Refused query store | `app/store/audit.py` → `refused_questions()` |
| Feedback gap store | `app/store/feedback.py` → `feedback_gaps()` |
| CSS styles | `frontend/src/index.css` → `.gap-item`, `.gap-item-badge-*` |
| i18n keys | `frontend/src/lib/i18n.ts` → 9 new keys |

---

## ✅ Assertions

- [x] KnowledgeGapPanel renders in Admin page below "Recent sync jobs"
- [x] Loading spinner shown while fetching `/api/knowledge-gaps`
- [x] Empty state shown when both lists are empty
- [x] Refused questions show red danger badges
- [x] Low-rated docs show yellow warning badges with external link
- [x] Export CSV downloads `knowledge-gaps.csv` via blob URL
- [x] Bilingual: EN/VI labels for all strings
- [x] Error state shown if API call fails
