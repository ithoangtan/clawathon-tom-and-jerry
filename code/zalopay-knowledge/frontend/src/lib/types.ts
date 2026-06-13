/**
 * types.ts — TypeScript mirror of app/api/schemas.py
 *
 * This file is the FE↔BE wire contract.  Field names are intentionally
 * snake_case to match the JSON wire format exactly — do NOT camelCase them.
 * Any change here MUST be reflected in schemas.py and docs/API-CONTRACT.md.
 *
 * See docs/API-CONTRACT.md for endpoint documentation and header requirements.
 */

import catalog from "./departments.data.json";

// ── Primitive literals ───────────────────────────────────────────────────────

/** Department keys — derived from app/common/departments.py via departments.data.json */
export type Department = (typeof catalog.departments)[number]["key"];
export type Role = "engineer" | "pm" | "ops" | "risk" | "business";
export type AnswerStatus = "answered" | "refused" | "partial";
export type RefusalReason = "access_denied" | "out_of_scope";
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
  /** Retrieved chunk text excerpt (~400 chars); optional until BE ships. */
  excerpt?: string | null;
  /** Stable chunk identifier from the vector store. */
  chunk_id?: string | null;
  /** Document type (PRD, Risk, Operation, …) from chunk metadata. */
  doc_type?: string | null;
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

/** SSE event names from POST /chat/stream */
export type ChatStreamEventName = "start" | "node" | "pipeline" | "error" | "done";

/** `node` event payload from POST /chat/stream (pipeline timeline). */
export interface StreamNodeEvent {
  /** Raw LangGraph node name (always present). */
  node: string;
  step_key?: string;
  step_label?: string;
  departments?: Department[];
  elapsed_ms?: number;
}

/** `pipeline` event payload — structured step timeline with start/end phases. */
export interface StreamPipelineEvent {
  step_key: "router" | "retrieve" | "grade" | "synthesize" | "verify";
  phase: "start" | "end";
  node: string;
  departments: Department[];
  elapsed_ms: number;
  step_elapsed_ms: number | null;
  ts: string;
}

/** One SSE payload from POST /chat/stream (`data: {event, data}` lines). */
export interface ChatStreamEvent {
  event: ChatStreamEventName;
  data: Record<string, unknown>;
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
  /** Present when refused due to department access control (FR-7.2). */
  refusal_reason?: RefusalReason | null;
  /** Departments queried but with no usable answer (partial tier). */
  refusals?: Department[] | null;
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

// ── Admin sync ────────────────────────────────────────────────────────────────

/** Job/department lifecycle status from the backend orchestrator. */
export type AdminJobStatusWire = "pending" | "running" | "success" | "failed";

/** Per-department sync result within an admin job (wire). */
export interface AdminDepartmentResultWire {
  department: Department;
  space_key?: string | null;
  status: AdminJobStatusWire;
  page_count?: number;
  chunk_count?: number;
  synced_items?: Array<{ source_id: string; title: string; url?: string | null }>;
  errors?: string[];
}

/** Sync job status for one source (wire). */
export interface AdminJobStatusWireBody {
  job_id?: string | null;
  status: AdminJobStatusWire;
  started_at?: string | null;
  finished_at?: string | null;
  last_success_at?: string | null;
  target_department?: Department | null;
  doc_count?: number;
  chunk_count?: number;
  errors?: string[];
  progress?: Record<string, unknown> | null;
  departments?: AdminDepartmentResultWire[];
}

/** Indexed corpus snapshot for one department (wire). */
export interface AdminDepartmentIndexWire {
  chunk_count: number;
  doc_count: number;
  has_data: boolean;
}

/** Body of GET /api/admin/sync/status (wire). */
export interface AdminSyncStatusWire {
  jobs: Partial<Record<"confluence" | "gdrive", AdminJobStatusWireBody>>;
  departments_indexed: Partial<Record<Department, AdminDepartmentIndexWire>>;
}

/** One row in GET /api/admin/sync/history (wire). */
export interface AdminSyncHistoryEntryWire {
  job_id: string;
  source: string;
  status: AdminJobStatusWire;
  started_at: string;
  finished_at?: string | null;
  department?: Department | null;
  doc_count?: number;
  chunk_count?: number;
  errors?: string[];
  departments?: AdminDepartmentResultWire[];
}

/** Body of GET /api/admin/sync/history (wire). */
export interface AdminSyncHistoryWire {
  entries: AdminSyncHistoryEntryWire[];
}

/** Normalized admin sync state consumed by admin UI components. */
export interface AdminDepartmentSyncStatus {
  department: Department;
  /** Confluence space key when source is confluence. */
  space_key?: string | null;
  state: "running" | "idle" | "error";
  page_count: number;
  doc_count: number;
  chunk_count: number;
  last_success_at?: string | null;
  freshness_hours?: number | null;
  errors: string[];
  progress?: Record<string, unknown> | null;
}

/** One historical or in-flight admin sync job. */
export interface AdminSyncJob {
  id: string;
  source: "confluence" | "gdrive";
  department?: Department | null;
  state: "running" | "success" | "failure";
  started_at: string;
  finished_at?: string | null;
  pages_synced?: number | null;
  message?: string | null;
  errors?: string[];
}

/** Normalized admin sync status for UI (derived from wire + history). */
export interface AdminSyncStatus {
  running: boolean;
  departments: AdminDepartmentSyncStatus[];
  recent_jobs: AdminSyncJob[];
  /** Global source rollup (mirrors GET /sync/status). */
  sources: SourceStatus[];
}

/** Body of POST /api/admin/sync */
export interface AdminSyncRequest {
  department?: Department | null;
  source?: "confluence" | "gdrive";
}

/** Body returned by POST /api/admin/sync */
export interface AdminSyncResponse {
  started: boolean;
  message: string;
  job_id?: string | null;
  department?: Department | null;
  source: "confluence" | "gdrive";
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

/** Body of GET /api/dashboard */
export interface DashboardData {
  query_count: number;
  deflection_rate: number;
  answered_wrong_rate: number;
  refusal_rate: number;
  partial_rate: number;
  conflict_rate: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  feedback_up: number;
  feedback_down: number;
  total_tokens: number;
  history: HistoryItem[];
  eval_golden_total?: number;
  eval_faithfulness?: number;
  eval_answer_relevance?: number;
  eval_refusal_precision?: number;
  eval_refusal_recall?: number;
  eval_context_recall_at_5?: number;
  eval_context_precision_at_5?: number;
  eval_last_run_at?: string | null;
  eval_mode?: string | null;
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
