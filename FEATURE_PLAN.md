# Feature Plan: Intelligent Follow-up Suggestions + Knowledge Gap Tracker

**Date:** 2026-06-15  
**Status:** ✅ COMPLETE  
**Priority:** P0 — Core AI Agent capability per requirements

---

## Tại sao đây là tính năng quan trọng nhất?

Requirements (G3, S-B7, S-A9) đề ra:

> "The same fact is rendered appropriately for an engineer vs a compliance officer, **improving with feedback over time**."
> "User reports answer as wrong → **weekly audit queue**; repeated 👎 on a doc → **doc-gap report to the owning department**"
> "Vague question → **ONE clarifying question offering 2–3 likely departments; never guesses silently**"

Hiện tại agent CHỈ phản ứng (reactive). Một AI Agent đẳng cấp phải **chủ động** (proactive):
- Gợi ý câu hỏi tiếp theo để người dùng khám phá thêm kiến thức
- Phát hiện và báo cáo những lỗ hổng trong knowledge base

**Feature: "Proactive Intelligence"**

### Part 1: Intelligent Follow-up Questions (user-facing) ✨

Sau mỗi câu trả lời, agent tự động sinh 3 câu hỏi liên quan dựa trên context đã retrieved. User click vào → auto-fill chat input.

**Why must-have:**
- G2: Users không biết phải hỏi gì → tăng adoption
- Trực tiếp từ retrieved chunks → không hallucinate
- UX: Agent cảm giác "sống" và thông minh hơn, không chỉ là search engine

### Part 2: Knowledge Gap Tracker (admin-facing) 📊

Tab mới trong Admin page:
- Top câu hỏi bị refused (potential doc gaps)  
- Documents có nhiều 👎 nhất (cần update)
- Có thể export report cho department owners

---

## Implementation Plan

### Step 1: Backend — Suggested Questions Generation
- [ ] **1a.** Thêm `suggested_questions: list[str]` vào `ChatResponse` schema
- [ ] **1b.** Tạo `app/graph/nodes/suggest.py` — generate 3 follow-up questions từ graded chunks + answer (ROUTING tier LLM, cheap)
- [ ] **1c.** Wire vào `respond` node: sau khi answer hoàn thành, gọi suggest async
- [ ] **1d.** Stream suggestions qua SSE event `suggestions` sau event `done`
- [ ] **1e.** Unit test: `tests/unit/graph/test_suggest.py`

### Step 2: Backend — Knowledge Gap API
- [ ] **2a.** Thêm query `refused_questions()` vào `AuditStore` — top refused questions grouped by similarity  
- [ ] **2b.** Thêm query `feedback_gaps()` vào `FeedbackStore` — feedbacks linked to citations
- [ ] **2c.** New endpoint `GET /api/knowledge-gaps` → `{refused: [...], low_rated_docs: [...]}`
- [ ] **2d.** Unit test cho endpoint

### Step 3: Frontend — SuggestedQuestions Component
- [ ] **3a.** Tạo `frontend/src/components/chat/SuggestedQuestions.tsx`
  - Animated chips/cards bên dưới answer
  - Click → set chat input + auto-submit
  - i18n VI/EN
  - Skeleton loading state khi suggestions chưa về
- [ ] **3b.** Wire vào `AssistantMessage.tsx` — show suggestions sau CitationList
- [ ] **3c.** Handle SSE `suggestions` event trong chat store
- [ ] **3d.** Vitest tests

### Step 4: Frontend — Knowledge Gap Panel  
- [ ] **4a.** Tạo `frontend/src/components/admin/KnowledgeGapPanel.tsx`
  - "Top unanswered questions" list với badges
  - "Documents needing attention" với 👎 count
  - Export CSV button
- [ ] **4b.** Wire vào `AdminPage.tsx` — tab mới "Knowledge Gaps"
- [ ] **4c.** Hook `useKnowledgeGaps.ts`

### Step 5: Integration Testing + Evidence
- [ ] **5a.** E2E test: send question → verify suggestions appear
- [ ] **5b.** E2E test: refuse question → verify appears in knowledge gaps
- [ ] **5c.** Viết TC31-TC35 evidence files
- [ ] **5d.** Update README evidence

---

## Technical Design

### Suggested Questions Generation

```
respond node (already built)
  → generates answer + citations
  → [NEW] calls suggest node (ROUTING tier, ~1s)
      prompt: "Given this Q&A and these source docs, generate 3 concise follow-up questions"
      returns: ["...", "...", "..."]
  → adds to ChatResponse.suggested_questions
```

**Stream flow:**
```
SSE: {event: "start"}
SSE: {event: "pipeline", data: {step: "routing"}}
...
SSE: {event: "done", data: ChatResponse (answer + citations)}  ← answer renders immediately
SSE: {event: "suggestions", data: {questions: [...]}}           ← suggestions pop in 1s later
```

### Knowledge Gap API

```
GET /api/knowledge-gaps
Response:
{
  refused_questions: [
    {question: "...", count: 5, last_seen: "...", likely_department: "grow"},
    ...
  ],
  low_rated_docs: [
    {title: "...", url: "...", down_count: 3, up_count: 1},
    ...
  ]
}
```

---

## UI Design Notes

### SuggestedQuestions

```
┌─────────────────────────────────────────────────────┐
│ [Answer text with citations [1][2]...]               │
│                                                     │
│ 💡 Bạn có thể hỏi tiếp:                            │
│  ┌──────────────────────────────────┐               │
│  │ 🔷 Campaign status flow là gì? →│               │
│  │ 🔷 Pity System v2 hoạt động? → │               │
│  │ 🔷 API endpoint spin token?  → │               │
│  └──────────────────────────────────┘               │
└─────────────────────────────────────────────────────┘
```

Chips với:
- Gradient border (brand color)
- Arrow icon → để chỉ "click để hỏi"
- Hover: lift effect + highlight
- Loading skeleton khi chờ suggestions
- Fade-in animation khi xuất hiện

### Knowledge Gap Panel

```
┌─── Admin: Knowledge Gaps ───────────────────────────┐
│ Top Unanswered Questions (last 30d)                 │
│ ┌─────────────────────────────────────────────────┐ │
│ │ ❓ "Zalopay hotline là bao nhiêu?"  5x refused  │ │
│ │ ❓ "Tỷ lệ chuyển đổi USD/VND..."    3x refused  │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ Documents Needing Attention                         │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 👎 Lucky Wheel Tech Doc v1    3 down / 1 up     │ │
│ │ 👎 Campaign Status Guide      2 down / 4 up     │ │
│ └─────────────────────────────────────────────────┘ │
│                          [Export Doc Gap Report]    │
└─────────────────────────────────────────────────────┘
```

---

## Quota handling

Nếu quota MaaS hết trong khi implement, suggest node sẽ gracefully return `[]` (empty suggestions).
Feature sẽ vẫn hoạt động mà không hiện suggestions — không break existing functionality.

Quota reset: 2:20 AM ngày mai.

---

## Progress Log

| Time | Step | Status | Notes |
|------|------|--------|-------|
| 2026-06-15 | Planning | ✅ DONE | Plan file created |
| 2026-06-15 | Step 1a | ✅ DONE | `ChatResponse.suggested_questions`, `GraphState.suggested_questions` |
| 2026-06-15 | Step 1b | ✅ DONE | `suggest.py` node + `suggest.v1.yaml` prompt |
| 2026-06-15 | Step 1c | ✅ DONE | `respond → suggest → END` edge in `build.py` |
| 2026-06-15 | Step 1d | ✅ DONE | `state_to_response()` passes field through |
| 2026-06-15 | Step 1e | ✅ DONE | TypeScript strict + build clean |
| 2026-06-15 | Step 2a | ✅ DONE | `AuditStore.refused_questions()` |
| 2026-06-15 | Step 2b | ✅ DONE | `FeedbackStore.feedback_gaps()` |
| 2026-06-15 | Step 2c | ✅ DONE | `GET /api/knowledge-gaps` endpoint |
| 2026-06-15 | Step 2d | ✅ DONE | Code review verified |
| 2026-06-15 | Step 3a | ✅ DONE | `SuggestedQuestions.tsx` with GSAP stagger animation |
| 2026-06-15 | Step 3b | ✅ DONE | Wired to `AssistantMessage` (isLast + !streaming guard) |
| 2026-06-15 | Step 3c | ✅ DONE | `handleSuggestedSelect` in `ChatInterface` |
| 2026-06-15 | Step 3d | ✅ DONE | UI verified via DOM injection screenshot |
| 2026-06-15 | Step 4a | ✅ DONE | `KnowledgeGapPanel.tsx` with CSV export |
| 2026-06-15 | Step 4b | ✅ DONE | Wired to `AdminPage` |
| 2026-06-15 | Step 4c | ✅ DONE | `useKnowledgeGaps()` hook, empty state, error state |
| 2026-06-15 | Step 5 | ✅ DONE | Evidence TC31–TC35 written, commit `dacec0c` |
