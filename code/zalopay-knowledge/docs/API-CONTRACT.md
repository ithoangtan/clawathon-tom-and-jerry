# API Contract — Zalopay Knowledge Agent

**Version:** 0.1.0  
**Single source of truth for the FE↔BE handshake.**  
Changes to any endpoint, header, field name, type, or optionality **must** be reflected in:
1. `app/api/schemas.py` (Pydantic models — the canonical definition)
2. `frontend/src/lib/types.ts` (TypeScript mirror)
3. This document

---

## Global Headers

Every request to a protected endpoint **must** include all four
`X-GreenNode-AgentBase-*` headers.  Missing `User-Id` or `Session-Id` returns
`400 Bad Request` immediately (before any LangGraph execution begins).

| Header | Required | Example | Description |
|---|---|---|---|
| `X-GreenNode-AgentBase-User-Id` | **Yes** | `user-abc123` | Stable user identifier |
| `X-GreenNode-AgentBase-Session-Id` | **Yes** | `sess-xyz789` | Session UUID (rotate via "New session" in UI) |
| `X-GreenNode-AgentBase-Role` | No (defaults to `"business"`) | `engineer` | User role: `engineer` \| `pm` \| `ops` \| `risk` \| `business` |
| `X-GreenNode-AgentBase-Home-Department` | No (defaults to `"risk"`) | `risk` | User's primary dept: `risk` \| `grow_enablement` \| `bank_partnerships` |

**Header-validation rule:** If either `X-GreenNode-AgentBase-User-Id` or
`X-GreenNode-AgentBase-Session-Id` is absent or empty, the server returns:

```json
{
  "detail": "Missing required header: X-GreenNode-AgentBase-User-Id"
}
```

with HTTP status `400`.

The frontend `apiClient.ts` injects all four headers from the persisted
`UserContext` on every request.

---

## Endpoints

### `GET /health`

Liveness and readiness probe.  No auth headers required.

**Request:** no body.

**Response `200 OK`:**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "index_ready": false,
  "config": {
    "small_model": "qwen2.5-7b-instruct",
    "main_model": "qwen2.5-72b-instruct",
    "embedding_model": "intfloat/multilingual-e5-small",
    "grade_threshold": 0.5,
    "topk": 8,
    "route_confidence_min": 0.55
  }
}
```

| Field | Type | Description |
|---|---|---|
| `status` | `"healthy"` | Always `"healthy"` while the process is up |
| `version` | `string \| null` | Semantic version from config |
| `index_ready` | `boolean` | `true` when at least one FAISS partition has been synced |
| `config` | `object \| null` | Non-sensitive config snapshot for the Settings ConfigPanel |

---

### `POST /invocations`

AgentBase-compatible entrypoint (mirrors `/chat`).  Accepts the same body and
headers as `/chat`.  Used by the GreenNode platform — the frontend uses
`/chat` directly.

---

### `POST /chat`

**Primary chat endpoint.** Runs the full LangGraph pipeline and returns a
grounded answer with citations.

**Required headers:** all four `X-GreenNode-AgentBase-*` headers (see above).

**Request body:**

```json
{
  "question": "What is the escalation process for risk alerts?",
  "target_departments": ["risk"]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `question` | `string` (1–4000 chars) | **Yes** | Natural-language question |
| `target_departments` | `Department[] \| null` | No | Explicit dept pins; bypasses router confidence gate |

**Response `200 OK`:**

```json
{
  "answer": "The escalation process begins when… [1]\n\nFor urgent cases… [2]",
  "citations": [
    {
      "title": "Risk Alert Escalation Policy",
      "url": "https://yoursite.atlassian.net/wiki/spaces/RISK/pages/123456",
      "section": "Escalation Levels > Level 1",
      "last_modified": "2024-11-15T09:30:00Z",
      "lifecycle_state": "active",
      "deprecated": false,
      "successor_url": null,
      "source_type": "confluence",
      "page": null,
      "excerpt": "Escalation Level 1 requires manager approval within 24 hours when…",
      "chunk_id": "risk-abc12345-deadbeef"
    },
    {
      "title": "Incident Response Runbook.pdf",
      "url": "https://drive.google.com/file/d/abc123",
      "section": null,
      "last_modified": "2024-10-01T00:00:00Z",
      "lifecycle_state": "active",
      "deprecated": false,
      "successor_url": null,
      "source_type": "pdf",
      "page": 3
    }
  ],
  "source_departments": ["risk"],
  "confidence": 0.87,
  "feedback_id": "fb-550e8400-e29b-41d4-a716-446655440000",
  "status": "answered",
  "conflicts": null,
  "clarifying_question": null,
  "lang": "en"
}
```

| Field | Type | Description |
|---|---|---|
| `answer` | `string` | Markdown answer with inline `[n]` citation markers |
| `citations` | `Citation[]` | Ordered citations; `[1]` maps to index 0, etc. |
| `source_departments` | `Department[]` | Departments that contributed |
| `confidence` | `float` 0–1 | Aggregate confidence |
| `feedback_id` | `string` | UUID for `POST /feedback` correlation |
| `status` | `"answered" \| "refused" \| "partial"` | Overall status |
| `conflicts` | `Conflict[] \| null` | Factual conflicts to render in ConflictPanel |
| `clarifying_question` | `ClarifyingQuestion \| null` | Emitted when router confidence < threshold |
| `lang` | `"en" \| "vi" \| null` | Language of the response |

**`status` semantics:**

| Value | Meaning |
|---|---|
| `"answered"` | At least one department returned a verified, grounded answer |
| `"refused"` | No department had relevant documents (grade gate failed for all) |
| `"partial"` | Some departments answered; others refused or timed out |

**`Citation` shape:**

| Field | Type | Description |
|---|---|---|
| `title` | `string` | Document title |
| `url` | `string` | Canonical URL |
| `section` | `string \| null` | Section heading path |
| `last_modified` | `string \| null` | ISO-8601 datetime |
| `lifecycle_state` | `string \| null` | `"active"` \| `"deprecated"` \| `"sunset"` |
| `deprecated` | `boolean` | `true` triggers StalenessBadge in UI |
| `successor_url` | `string \| null` | Link to replacement doc (deprecated only) |
| `source_type` | `string \| null` | `"confluence"` \| `"pdf"` |
| `page` | `int \| null` | PDF page number (1-indexed) |
| `excerpt` | `string \| null` | Optional chunk text snippet (~400 chars) for evidence inspection |
| `chunk_id` | `string \| null` | Optional stable chunk id from retrieval |

**`Conflict` shape:**

```json
{
  "topic": "Escalation SLA for Level 2 incidents",
  "sides": [
    {
      "department": "risk",
      "statement": "Level 2 must be resolved within 4 hours.",
      "citation": { ... }
    },
    {
      "department": "bank_partnerships",
      "statement": "Level 2 SLA is 8 business hours.",
      "citation": { ... }
    }
  ]
}
```

**`ClarifyingQuestion` shape:**

```json
{
  "prompt": "Which department's policies are you asking about?",
  "options": ["risk", "grow_enablement"]
}
```

**Error responses:**

| Status | Body | Cause |
|---|---|---|
| `400` | `{"detail": "Missing required header: ..."}` | Missing User-Id or Session-Id header |
| `408` | `{"detail": "Request timeout"}` | Exceeded `GRAPH_BUDGET_S` |
| `503` | `{"detail": "Knowledge base not ready — please sync first"}` | No FAISS index built yet |

---

### `POST /chat/stream`

**Streaming chat endpoint (SSE).** Same request body and headers as `POST /chat`.
Emits Server-Sent Events as JSON lines (`data: {...}\n\n`).

**Event envelope:**

```json
{ "event": "start" | "node" | "done" | "error", "data": { ... } }
```

| Event | `data` shape | Description |
|---|---|---|
| `start` | `{ "question": string }` | Stream opened; echoes the question |
| `node` | `StreamNodeEvent` | LangGraph node completed (pipeline timeline) |
| `done` | `ChatResponse` | Terminal answer (same shape as `POST /chat`) |
| `error` | `{ "detail": string }` | Fatal stream error |

**`StreamNodeEvent` shape (backward compatible):**

| Field | Type | Required | Description |
|---|---|---|---|
| `node` | `string` | **Yes** | Raw LangGraph node name (e.g. `router`, `dept_subgraph`) |
| `step_key` | `string` | No | Stable step id for UI timeline (e.g. `retrieve`, `reconcile`) |
| `step_label` | `string` | No | Human-readable step label |
| `departments` | `Department[]` | No | Departments being queried when known |
| `elapsed_ms` | `int` | No | Milliseconds since stream start |

Example `node` event:

```json
{
  "event": "node",
  "data": {
    "node": "dept_subgraph",
    "step_key": "retrieve",
    "step_label": "Searching internal documents",
    "departments": ["risk", "grow_enablement"],
    "elapsed_ms": 842
  }
}
```

Existing clients may continue to read only `data.node`; new fields are optional.

**Error responses:** same as `POST /chat` for HTTP-level failures (400, 503).
Stream-level failures use the `error` SSE event.

---

### `POST /feedback`

Submit thumbs up/down feedback for an answer.

**Required headers:** all four `X-GreenNode-AgentBase-*` headers.

**Request body:**

```json
{
  "feedback_id": "fb-550e8400-e29b-41d4-a716-446655440000",
  "rating": "up",
  "comment": "Very helpful, found the exact policy I needed."
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `feedback_id` | `string` | **Yes** | UUID from `ChatResponse.feedback_id` |
| `rating` | `"up" \| "down"` | **Yes** | Thumbs up or down |
| `comment` | `string \| null` | No | Optional free-text comment (max 2000 chars) |

**Response `204 No Content`** on success.

**Error responses:**

| Status | Cause |
|---|---|
| `400` | Missing required header or missing required field |
| `404` | `feedback_id` not found in the audit store |

---

### `POST /sync/confluence`

Trigger an asynchronous Confluence sync job.

**Required headers:** all four `X-GreenNode-AgentBase-*` headers.

**Request body:** empty (no body required).

**Response `202 Accepted`:**

```json
{
  "source": "confluence",
  "started": true,
  "message": "Confluence sync started in background"
}
```

If a sync is already running, returns `409 Conflict` with `started: false`.

---

### `POST /sync/gdrive`

Trigger an asynchronous Google Drive PDF sync job.

**Prerequisites:** `GDRIVE_FOLDER_ID` configured. On AgentBase, Drive credentials from Outbound Auth OAuth `identity-google-space` (M2M, `drive.readonly`). Local dev: `GDRIVE_SA_JSON_PATH` or `GDRIVE_API_KEY`. See `.env.example`.

**Required headers:** all four `X-GreenNode-AgentBase-*` headers.

**Request body:** empty (no body required).

**Response `202 Accepted`:**

```json
{
  "source": "gdrive",
  "started": true,
  "message": "Google Drive sync started in background"
}
```

If a sync is already running, returns `409 Conflict` with `started: false`.

---

### `GET /sync/status`

Poll sync job state and index freshness.  Used by the Dashboard SyncStatusPanel
and the Settings SyncControls (polled every 2 s while running, 30 s idle).

**No auth headers required** (read-only, non-sensitive).

**Response `200 OK`:**

```json
{
  "sources": [
    {
      "source": "confluence",
      "state": "idle",
      "doc_count": 142,
      "chunk_count": 1834,
      "last_success_at": "2024-12-01T14:30:00Z",
      "freshness_hours": 2.5,
      "errors": [],
      "progress": null
    },
    {
      "source": "gdrive",
      "state": "running",
      "doc_count": 17,
      "chunk_count": 203,
      "last_success_at": "2024-11-28T09:00:00Z",
      "freshness_hours": 77.5,
      "errors": [],
      "progress": {
        "files_processed": 12,
        "files_total": 17
      }
    }
  ]
}
```

**`SourceStatus` shape:**

| Field | Type | Description |
|---|---|---|
| `source` | `string` | `"confluence"` or `"gdrive"` |
| `state` | `"running" \| "idle" \| "error"` | Current sync state |
| `doc_count` | `int` | Number of documents indexed |
| `chunk_count` | `int` | Number of chunks in the FAISS partition |
| `last_success_at` | `string \| null` | ISO-8601 of last successful sync |
| `freshness_hours` | `float \| null` | Hours since last success; `null` = never synced |
| `errors` | `string[]` | Recent error messages |
| `progress` | `object \| null` | Running-sync progress (files, pages, etc.) |

**Freshness badge thresholds (UI):**  
- Green: `freshness_hours ≤ 24`  
- Amber: `freshness_hours > 24`  
- Red / never: `last_success_at == null`

---

### `GET /api/dashboard`

Aggregate usage metrics for the Dashboard page.

**No auth headers required** (aggregated, PII-masked).

**Response `200 OK`:**

```json
{
  "query_count": 312,
  "refusal_rate": 0.08,
  "partial_rate": 0.12,
  "conflict_rate": 0.04,
  "latency_p50_ms": 1840,
  "latency_p95_ms": 4200,
  "feedback_up": 201,
  "feedback_down": 23,
  "total_tokens": 1240500,
  "history": [
    {
      "ts": "2024-12-01T15:42:00Z",
      "question": "What is the KYC re-verification threshold?",
      "departments": ["risk"],
      "status": "answered",
      "confidence": 0.91,
      "latency_ms": 1523
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `query_count` | `int` | Total queries processed |
| `refusal_rate` | `float` 0–1 | Fraction of queries that resulted in `"refused"` |
| `partial_rate` | `float` 0–1 | Fraction that resulted in `"partial"` |
| `conflict_rate` | `float` 0–1 | Fraction where `conflicts` was non-empty |
| `latency_p50_ms` | `float` | Median end-to-end latency in ms |
| `latency_p95_ms` | `float` | 95th-percentile latency in ms |
| `feedback_up` | `int` | Total thumbs-up feedback events |
| `feedback_down` | `int` | Total thumbs-down feedback events |
| `total_tokens` | `int` | Total LLM tokens consumed (prompt + completion) |
| `history` | `HistoryItem[]` | Recent query log (PII-masked question, last 100) |

---

## Wire-format notes

1. **snake_case everywhere** — no camelCase transformation at the API boundary.
   `source_departments`, `feedback_id`, `last_modified`, `clarifying_question`, etc.
2. **`null` vs absent** — optional fields are represented as JSON `null` when
   present, or may be omitted entirely.  Frontend should use `?? null` / `?? []`
   defaults.
3. **`Content-Type: application/json`** for all POST requests.
4. **HTTP 204** for feedback (no body).
5. **HTTP 202** for sync starts (job is async; poll `/sync/status`).
6. **HTTP 409** if sync already running.
