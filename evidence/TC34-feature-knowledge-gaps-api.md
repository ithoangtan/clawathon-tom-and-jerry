# TC34 — Feature: Proactive Intelligence — /api/knowledge-gaps Endpoint

| Field | Value |
|-------|-------|
| **Test ID** | TC34 |
| **Mode** | Code review + static analysis |
| **Type** | New feature — REST API endpoint |
| **Verdict** | ✅ PASS |

---

## Feature Overview

New `GET /api/knowledge-gaps` endpoint aggregates two data streams:
1. **Refused questions** from the audit store (last 30 days, top 20 by frequency)
2. **Low-rated documents** from the feedback store (docs with net negative ratings)

---

## 🔧 API Contract

```
GET /api/knowledge-gaps
Authorization: Bearer <token>

Response 200:
{
  "refused_questions": [
    {
      "question": "string",
      "count": 3,
      "last_seen": "2026-06-14T10:30:00",
      "departments": ["risk", "grow_enablement"]
    }
  ],
  "low_rated_docs": [
    {
      "title": "string",
      "url": "https://...",
      "up": 2,
      "down": 5
    }
  ]
}
```

---

## 📋 Store Methods

### `AuditStore.refused_questions(limit=20, days=30)`
```sql
SELECT question, departments, COUNT(*) AS cnt, MAX(ts) AS last_seen
FROM queries
WHERE status = 'refused' AND ts >= NOW() - INTERVAL 30 DAYS
GROUP BY question, departments
ORDER BY cnt DESC
LIMIT 20
```

### `FeedbackStore.feedback_gaps(limit=20)`
- Joins `feedback` table with `queries` on `feedback_id`
- Parses `citations_json` to aggregate per-document up/down counts
- Returns documents where `down > 0`, sorted by down count descending

---

## ✅ Assertions

- [x] Route registered: `router.get("/api/knowledge-gaps")`
- [x] Returns `JSONResponse` with `refused_questions` + `low_rated_docs` keys
- [x] `AuditStore.refused_questions()` queries only `status = 'refused'`
- [x] 30-day rolling window filters stale unanswered questions
- [x] `FeedbackStore.feedback_gaps()` aggregates per source document
- [x] Both stores handle empty tables gracefully (return `[]`)
- [x] Frontend `useKnowledgeGaps()` hook fetches on mount, provides `exportCsv()`

---

## 📁 Key Files

| File | Change |
|------|--------|
| `app/api/routes.py` | Added `GET /api/knowledge-gaps` route |
| `app/store/audit.py` | Added `refused_questions()` method |
| `app/store/feedback.py` | Added `feedback_gaps()` method |
