/**
 * types.ts — TypeScript mirror of app/api/schemas.py
 *
 * This file is the FE↔BE wire contract.  Field names are intentionally
 * snake_case to match the JSON wire format exactly — do NOT camelCase them.
 * Any change here MUST be reflected in schemas.py and docs/API-CONTRACT.md.
 *
 * See docs/API-CONTRACT.md for endpoint documentation and header requirements.
 */

// ── Primitive literals ───────────────────────────────────────────────────────

export type Department = "risk" | "grow_enablement" | "bank_partnerships";
export type Role = "engineer" | "pm" | "ops" | "risk" | "business";
export type AnswerStatus = "answered" | "refused" | "partial";
export type Lang = "en" | "vi";

// ── Citation ─────────────────────────────────────────────────────────────────

/** A single document citation attached to an answer. */
export interface Citation {
  title: string;
  url: string;
  section?: string | null;
  last_modified?: string | null;
  lifecycle_state?: string | null;
  deprecated?: boolean;
  successor_url?: string | null;
  source_type?: string | null;
  /** PDF page number (1-indexed); null for Confluence chunks. */
  page?: number | null;
}

// ── Conflict ─────────────────────────────────────────────────────────────────

/** One side of a factual conflict between two department sources. */
export interface ConflictSide {
  department: Department;
  statement: string;
  citation: Citation;
}

/** A detected factual conflict surfaced by the reconcile node. */
export interface Conflict {
  topic?: string | null;
  sides: ConflictSide[];
}

// ── Clarifying question ───────────────────────────────────────────────────────

/** A clarifying question emitted when routing confidence is too low. */
export interface ClarifyingQuestion {
  prompt: string;
  /** Quick-reply department options. */
  options: Department[];
}

// ── Chat ─────────────────────────────────────────────────────────────────────

/** Body of POST /chat */
export interface ChatRequest {
  question: string;
  /**
   * Optional explicit department pins set by the UI DepartmentTargetBar.
   * When provided, the router skips confidence gating for these departments.
   */
  target_departments?: Department[] | null;
}

/** Body of a successful POST /chat response */
export interface ChatResponse {
  /** Markdown-formatted answer text with inline [n] citation markers. */
  answer: string;
  /** Ordered list of citations corresponding to [1]…[n] markers. */
  citations: Citation[];
  /** Departments that contributed to this answer. */
  source_departments: Department[];
  /** Aggregate confidence score 0–1. */
  confidence: number;
  /** Opaque UUID to use when submitting feedback via POST /feedback. */
  feedback_id: string;
  status: AnswerStatus;
  /** Non-empty when the reconcile node detected genuine factual conflicts. */
  conflicts?: Conflict[] | null;
  /** Non-null when the router emits a clarifying question instead of answering. */
  clarifying_question?: ClarifyingQuestion | null;
  /** Language of the response: "en" or "vi". */
  lang?: Lang | null;
}

// ── Feedback ─────────────────────────────────────────────────────────────────

/** Body of POST /feedback */
export interface FeedbackRequest {
  /** UUID from ChatResponse.feedback_id. */
  feedback_id: string;
  rating: "up" | "down";
  comment?: string | null;
}

// ── Sync ─────────────────────────────────────────────────────────────────────

/** Body returned by POST /sync/confluence and POST /sync/gdrive */
export interface SyncStartResponse {
  /** Which source was triggered: "confluence" or "gdrive". */
  source: string;
  /** True if a new sync job was started; false if one was already running. */
  started: boolean;
  message: string;
}

/** Per-source sync status entry */
export interface SourceStatus {
  /** Source identifier: "confluence" or "gdrive". */
  source: string;
  state: "running" | "idle" | "error";
  doc_count: number;
  chunk_count: number;
  /** ISO-8601 timestamp of the last successful sync completion. */
  last_success_at?: string | null;
  /** Hours since the last successful sync; null if never synced. */
  freshness_hours?: number | null;
  errors: string[];
  /** Optional running-sync progress payload. */
  progress?: Record<string, unknown> | null;
}

/** Body of GET /sync/status */
export interface SyncStatus {
  sources: SourceStatus[];
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

/** One row in the query history table on the Dashboard. */
export interface HistoryItem {
  /** ISO-8601 timestamp of the query. */
  ts: string;
  question: string;
  departments: Department[];
  status: AnswerStatus;
  confidence: number;
  latency_ms: number;
}

/** Body of GET /dashboard */
export interface DashboardData {
  query_count: number;
  refusal_rate: number;
  partial_rate: number;
  conflict_rate: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  feedback_up: number;
  feedback_down: number;
  total_tokens: number;
  history: HistoryItem[];
}

// ── Health ────────────────────────────────────────────────────────────────────

/** Body of GET /health */
export interface HealthInfo {
  status: "healthy";
  version?: string | null;
  index_ready: boolean;
  /** Non-sensitive config snapshot for the Settings ConfigPanel. */
  config?: Record<string, unknown> | null;
}

// ── Client-only types ─────────────────────────────────────────────────────────

/**
 * UserContext is a client-only construct — it is never sent as a JSON body
 * but is used to build the X-GreenNode-AgentBase-* request headers.
 * Persisted in localStorage via Zustand.
 */
export interface UserContext {
  userId: string;
  sessionId: string;
  role: Role;
  homeDept: Department;
  locale: Lang;
}
