# TC35 — Feature: Proactive Intelligence — End-to-End Summary

| Field | Value |
|-------|-------|
| **Test ID** | TC35 |
| **Mode** | Code review + UI verification |
| **Type** | Feature completeness — full stack |
| **Verdict** | ✅ PASS |

---

## Feature: Proactive Intelligence

This is the top feature added to the Zalopay Wiki Agent AI Agent. It makes the agent proactively helpful — instead of passively answering questions, it anticipates what the user might want to know next, and surfaces documentation gaps to admins.

### Why this matters (requirement alignment)

From `2-requirements/`: the agent must be a **knowledge companion** for Zalopay internal staff, not just a search tool. Proactive follow-up questions:
- Reduce the number of turns needed to get full understanding
- Surface related policies the user didn't know to ask about
- Keep users within the citation-grounded system instead of searching elsewhere

Knowledge Gap Tracker:
- Closes the loop for admins: know exactly which questions fail
- Enables targeted Confluence/Drive documentation to fill gaps
- Turns "not in docs" from a dead-end into an actionable signal

---

## ✅ Full Stack Verification

| Layer | Component | Status |
|-------|-----------|--------|
| LLM Prompt | `suggest.v1.yaml` — bilingual, strict JSON | ✅ |
| Graph Node | `suggest.py` — fault-tolerant, skips on refused | ✅ |
| State | `GraphState.suggested_questions: list[str]` | ✅ |
| API Schema | `ChatResponse.suggested_questions: Optional[list[str]]` | ✅ |
| Graph Wiring | `respond → suggest → END` | ✅ |
| Service | `state_to_response()` passes through field | ✅ |
| Store Methods | `refused_questions()`, `feedback_gaps()` | ✅ |
| REST Endpoint | `GET /api/knowledge-gaps` | ✅ |
| UI Component | `SuggestedQuestions.tsx` with GSAP stagger | ✅ |
| UI Component | `KnowledgeGapPanel.tsx` with CSV export | ✅ |
| Chat Wiring | `AssistantMessage` renders chips on last message | ✅ |
| Click Handler | `handleSuggestedSelect` → auto-submits question | ✅ |
| Admin Wiring | `AdminPage` mounts `KnowledgeGapPanel` | ✅ |
| Styles | `.suggestion-chip`, `.gap-item`, animations | ✅ |
| i18n | 9 new EN/VI keys | ✅ |
| TypeScript | `tsc --noEmit` — 0 errors | ✅ |
| Build | `npm run build` — 953 modules, 0 errors | ✅ |
| Tests | 544 unit tests pass | ✅ |
| Git | Committed `dacec0c` on `main` | ✅ |

---

## 📸 Screenshots Verified

1. **Chat — Suggested Questions chips** (TC31): "YOU MIGHT ALSO ASK:" label with 3 chips below answer
2. **Admin — Knowledge Gaps panel** (TC33): "Knowledge Gaps" card with empty state ✅

---

## 🏗️ Architecture Diagram

```
User question
     │
     ▼
[retrieve] → [grade] → [synthesize] → [verify]
                                          │
                                     [reconcile]
                                          │
                                      [respond]
                                          │
                                      [suggest]  ← NEW
                                          │
                                    suggested_questions[]
                                          │
                                    SSE → frontend
                                          │
                                  SuggestedQuestions chips
```

```
Admin page
     │
     ▼
KnowledgeGapPanel → GET /api/knowledge-gaps
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
    AuditStore                  FeedbackStore
    .refused_questions()        .feedback_gaps()
              │                       │
         [refused Q]           [low-rated docs]
```
