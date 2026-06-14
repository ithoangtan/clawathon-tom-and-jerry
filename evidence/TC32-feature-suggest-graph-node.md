# TC32 — Feature: Proactive Intelligence — suggest LangGraph Node

| Field | Value |
|-------|-------|
| **Test ID** | TC32 |
| **Mode** | Code review + static analysis |
| **Type** | New feature — backend graph node |
| **Verdict** | ✅ PASS |

---

## Feature Overview

A new `suggest` node is appended to the LangGraph supervisor pipeline after `respond`. It calls the ROUTING-tier LLM with the question, truncated answer, and source titles to generate 3 context-aware follow-up questions. The node is designed to be fault-tolerant — any exception results in `suggested_questions: []` rather than a request failure.

---

## 🔧 Node Design

```
respond → suggest → END
```

**Inputs from GraphState:**
- `status`: only runs for `"answered"` or `"partial"` — skips on `"refused"` / `"not_covered"`
- `response`: final answer text (truncated to 800 chars to stay within token budget)
- `messages[0]`: original question
- `retrieved_docs`: source document titles (up to 5)
- `detected_language`: `"vi"` or `"en"` for bilingual prompt

**Output:**
- `suggested_questions: list[str]` — 0–3 items

---

## 📋 Prompt Template (`suggest.v1.yaml`)

```yaml
role: routing
version: "1.0"
description: "Generate 3 follow-up questions from retrieved context"
required_inputs: [question, answer, source_titles, language]
output_format: "JSON array of 3 strings only"
```

- Strict JSON-only output requirement
- Fallback regex extraction for malformed LLM output
- Examples provided in both EN and VI
- Uses ROUTING tier (small/fast model) to avoid latency impact

---

## ✅ Assertions

- [x] Node registered in `build.py`: `g.add_node("suggest", make_suggest_node(deps.llm))`
- [x] Graph edge: `g.add_edge("respond", "suggest")` / `g.add_edge("suggest", END)`
- [x] `GraphState.suggested_questions: list[str]` added to state schema
- [x] Skips generation when `status not in ("answered", "partial")`
- [x] JSON parse with regex fallback for malformed output
- [x] All exceptions caught — returns `{"suggested_questions": []}` on any error
- [x] Answer truncated to 800 chars to control token usage
- [x] Source titles extracted from `retrieved_docs[].metadata.title`

---

## 📁 Key Files

| File | Change |
|------|--------|
| `app/graph/nodes/suggest.py` | New node implementation (86 lines) |
| `app/prompts/suggest.v1.yaml` | Prompt template with bilingual examples |
| `app/graph/state.py` | Added `suggested_questions: list[str]` field |
| `app/graph/build.py` | Added node + edges: `respond → suggest → END` |
| `app/graph/nodes/__init__.py` | Updated module docstring topology |
