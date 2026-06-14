# TC31 — Feature: Proactive Intelligence — Suggested Follow-up Questions (UI)

| Field | Value |
|-------|-------|
| **Test ID** | TC31 |
| **Mode** | UI — Browser interaction |
| **Type** | New feature — suggested questions chip row |
| **Verdict** | ✅ PASS |

---

## Feature Overview

After each answered response, the agent proactively generates 3 contextually-relevant follow-up questions derived from the retrieved source documents. These appear as clickable chips below the last assistant message, animating in with a GSAP stagger effect.

---

## 🖱️ UI Interaction

| Step | Action | Details |
|------|--------|---------|
| 1 | Open existing answered chat session | "Lucky Wheel v2 có những tính năng mới gì so với v1?" |
| 2 | Scroll to bottom of message | `chatScroll.scrollTop = scrollHeight` |
| 3 | Verify "YOU MIGHT ALSO ASK:" section | Appears below sources + feedback row |
| 4 | Verify 3 suggestion chips rendered | Each with text + `→` arrow |

---

## 📸 Observed UI State

**Suggestion chips visible:**
1. "What are the prize pool configuration limits for Lucky Wheel v2?"
2. "How does the Slot Machine mechanic differ from the classic spin wheel?"
3. "What analytics events are tracked for each Lucky Wheel v2 game type?"

**UI Details:**
- `💡 YOU MIGHT ALSO ASK:` label in uppercase with accent color
- Each chip: full-width button, dark glass background, `→` arrow right-aligned
- Hover: chip slides right 2px, brand-color border, glow shadow
- GSAP animation: opacity 0→1, y 8→0, scale 0.96→1, stagger 0.07s per chip

---

## 🔧 Implementation

| Component | File |
|-----------|------|
| Graph node | `app/graph/nodes/suggest.py` |
| Prompt template | `app/prompts/suggest.v1.yaml` |
| State field | `app/graph/state.py` → `suggested_questions: list[str]` |
| API schema | `app/api/schemas.py` → `ChatResponse.suggested_questions` |
| Graph wiring | `app/graph/build.py` → `respond → suggest → END` |
| UI component | `frontend/src/components/chat/SuggestedQuestions.tsx` |
| Message wiring | `frontend/src/components/chat/AssistantMessage.tsx` |
| Click handler | `frontend/src/components/chat/ChatInterface.tsx` → `handleSuggestedSelect` |
| CSS styles | `frontend/src/index.css` → `.suggested-questions-wrap`, `.suggestion-chip` |

---

## ✅ Assertions

- [x] Section only appears on the **last** assistant message (`isLast` prop)
- [x] Section does **not** appear while streaming (`!streaming` guard)
- [x] Clicking a chip calls `setInput(question)` then `sendMessage(question)`
- [x] Returns `[]` (skipped) when response status is `refused` or `not_covered`
- [x] Gracefully handles LLM errors — never propagates exception to the user request
- [x] Bilingual: EN "You might also ask:" / VI "Bạn có thể hỏi tiếp:"
- [x] TypeScript strict — no errors
- [x] Vite build clean — 953 modules, 0 errors
