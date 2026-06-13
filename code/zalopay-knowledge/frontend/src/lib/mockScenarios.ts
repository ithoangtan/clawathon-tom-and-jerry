import type {
  AdminSyncStatus,
  DashboardData,
} from "@/lib/types";

export type ScenarioKey =
  | "healthy"
  | "syncing"
  | "errors"
  | "fresh_install"
  | "stale";

export interface Scenario {
  key: ScenarioKey;
  label: string;
  description: string;
  adminStatus: AdminSyncStatus;
  dashboard: DashboardData;
}

// ── Admin status helpers ──────────────────────────────────────────────────────

const NOW = "2026-06-14T08:00:00Z";
const HOUR_AGO = "2026-06-14T07:00:00Z";
const DAY_AGO = "2026-06-13T08:00:00Z";
const WEEK_AGO = "2026-06-07T08:00:00Z";

// ── Dashboard helpers ─────────────────────────────────────────────────────────

const HISTORY_HEALTHY = [
  { ts: "2026-06-14T07:52:11Z", question: "Quy trình xử lý giao dịch hoàn tiền cho merchant là gì?", departments: ["risk"] as const, status: "answered" as const, confidence: 0.92, latency_ms: 1210 },
  { ts: "2026-06-14T07:43:05Z", question: "SLA của đối tác ngân hàng Vietcombank là bao nhiêu?", departments: ["bank_partnerships"] as const, status: "answered" as const, confidence: 0.88, latency_ms: 1540 },
  { ts: "2026-06-14T07:31:22Z", question: "Tiêu chí onboarding merchant mới trong Q3 2026?", departments: ["grow_enablement"] as const, status: "partial" as const, confidence: 0.61, latency_ms: 2100 },
  { ts: "2026-06-14T07:18:44Z", question: "Chính sách KYC cho khách hàng cá nhân cập nhật mới nhất?", departments: ["risk"] as const, status: "answered" as const, confidence: 0.95, latency_ms: 980 },
  { ts: "2026-06-14T07:05:30Z", question: "Hướng dẫn đối soát cuối ngày với ngân hàng ACB?", departments: ["bank_partnerships"] as const, status: "answered" as const, confidence: 0.84, latency_ms: 1670 },
  { ts: "2026-06-14T06:50:17Z", question: "Chiến lược giữ chân merchant tier Gold?", departments: ["grow_enablement"] as const, status: "refused" as const, confidence: 0.12, latency_ms: 820 },
  { ts: "2026-06-14T06:38:59Z", question: "Mức độ ưu tiên xử lý alert fraud type B2?", departments: ["risk"] as const, status: "answered" as const, confidence: 0.9, latency_ms: 1350 },
  { ts: "2026-06-14T06:22:03Z", question: "Quy trình escalation khi merchant khiếu nại quá 48h?", departments: ["grow_enablement", "risk"] as const, status: "answered" as const, confidence: 0.79, latency_ms: 2450 },
];

const HISTORY_POOR = [
  { ts: "2026-06-14T07:50:00Z", question: "Quy trình hoàn tiền merchant khi lỗi hệ thống?", departments: ["risk"] as const, status: "refused" as const, confidence: 0.18, latency_ms: 900 },
  { ts: "2026-06-14T07:41:00Z", question: "SLA Vietcombank với giao dịch quốc tế?", departments: ["bank_partnerships"] as const, status: "refused" as const, confidence: 0.22, latency_ms: 1100 },
  { ts: "2026-06-14T07:28:00Z", question: "Điều kiện onboarding merchant thương mại điện tử?", departments: ["grow_enablement"] as const, status: "partial" as const, confidence: 0.45, latency_ms: 2800 },
  { ts: "2026-06-14T07:10:00Z", question: "Chính sách KYC cập nhật tháng 6?", departments: ["risk"] as const, status: "refused" as const, confidence: 0.09, latency_ms: 750 },
  { ts: "2026-06-14T06:55:00Z", question: "Đối soát cuối tháng với ngân hàng BIDV?", departments: ["bank_partnerships"] as const, status: "partial" as const, confidence: 0.38, latency_ms: 3200 },
];

// ── Scenarios ─────────────────────────────────────────────────────────────────

export const SCENARIOS: Scenario[] = [
  {
    key: "healthy",
    label: "Hệ thống bình thường",
    description: "Tất cả sync thành công, metrics tốt",
    adminStatus: {
      running: false,
      departments: [
        { department: "risk", space_key: "RISK", state: "idle", page_count: 142, doc_count: 98, chunk_count: 1240, last_success_at: HOUR_AGO, freshness_hours: 1, errors: [] },
        { department: "grow_enablement", space_key: "GROW", state: "idle", page_count: 87, doc_count: 61, chunk_count: 784, last_success_at: HOUR_AGO, freshness_hours: 1.5, errors: [] },
        { department: "bank_partnerships", space_key: "BANK", state: "idle", page_count: 113, doc_count: 79, chunk_count: 956, last_success_at: HOUR_AGO, freshness_hours: 0.8, errors: [] },
      ],
      recent_jobs: [
        { id: "job-001", source: "confluence", department: "risk", state: "success", started_at: HOUR_AGO, finished_at: HOUR_AGO, pages_synced: 142, message: "Synced 142 pages" },
        { id: "job-002", source: "confluence", department: "grow_enablement", state: "success", started_at: HOUR_AGO, finished_at: HOUR_AGO, pages_synced: 87 },
        { id: "job-003", source: "gdrive", state: "success", started_at: DAY_AGO, finished_at: DAY_AGO, pages_synced: 34 },
      ],
      sources: [
        { source: "gdrive", state: "idle", doc_count: 34, chunk_count: 412, last_success_at: DAY_AGO, freshness_hours: 24, errors: [] },
      ],
    },
    dashboard: {
      query_count: 1284,
      deflection_rate: 0.823,
      answered_wrong_rate: 0.042,
      refusal_rate: 0.091,
      partial_rate: 0.044,
      conflict_rate: 0.018,
      latency_p50_ms: 1340,
      latency_p95_ms: 3870,
      feedback_up: 947,
      feedback_down: 63,
      total_tokens: 2_480_000,
      eval_golden_total: 120,
      eval_faithfulness: 0.91,
      eval_answer_relevance: 0.88,
      eval_refusal_precision: 0.94,
      eval_refusal_recall: 0.87,
      eval_context_recall_at_5: 0.82,
      eval_context_precision_at_5: 0.79,
      eval_last_run_at: "2026-06-13T08:30:00Z",
      eval_mode: "golden",
      history: HISTORY_HEALTHY,
    },
  },

  {
    key: "syncing",
    label: "Đang sync",
    description: "Confluence đang chạy, gdrive idle",
    adminStatus: {
      running: true,
      departments: [
        { department: "risk", space_key: "RISK", state: "running", page_count: 142, doc_count: 98, chunk_count: 1240, last_success_at: DAY_AGO, freshness_hours: 24, errors: [], progress: { pages_done: 74, pages_total: 142 } },
        { department: "grow_enablement", space_key: "GROW", state: "running", page_count: 87, doc_count: 61, chunk_count: 784, last_success_at: DAY_AGO, freshness_hours: 24, errors: [], progress: { pages_done: 12, pages_total: 87 } },
        { department: "bank_partnerships", space_key: "BANK", state: "idle", page_count: 113, doc_count: 79, chunk_count: 956, last_success_at: HOUR_AGO, freshness_hours: 1, errors: [] },
      ],
      recent_jobs: [
        { id: "job-010", source: "confluence", department: "risk", state: "running", started_at: NOW, pages_synced: null, message: "Syncing page 74/142…" },
        { id: "job-011", source: "confluence", department: "grow_enablement", state: "running", started_at: NOW, pages_synced: null },
        { id: "job-009", source: "gdrive", state: "success", started_at: DAY_AGO, finished_at: DAY_AGO, pages_synced: 34 },
      ],
      sources: [
        { source: "gdrive", state: "idle", doc_count: 34, chunk_count: 412, last_success_at: DAY_AGO, freshness_hours: 24, errors: [] },
      ],
    },
    dashboard: {
      query_count: 1284,
      deflection_rate: 0.823,
      answered_wrong_rate: 0.042,
      refusal_rate: 0.091,
      partial_rate: 0.044,
      conflict_rate: 0.018,
      latency_p50_ms: 1340,
      latency_p95_ms: 3870,
      feedback_up: 947,
      feedback_down: 63,
      total_tokens: 2_480_000,
      history: HISTORY_HEALTHY,
    },
  },

  {
    key: "errors",
    label: "Có lỗi sync",
    description: "Risk và GDrive gặp lỗi, Grow OK",
    adminStatus: {
      running: false,
      departments: [
        { department: "risk", space_key: "RISK", state: "error", page_count: 98, doc_count: 67, chunk_count: 843, last_success_at: WEEK_AGO, freshness_hours: 168, errors: ["Confluence API timeout after 30s", "Retry 3/3 failed"] },
        { department: "grow_enablement", space_key: "GROW", state: "idle", page_count: 87, doc_count: 61, chunk_count: 784, last_success_at: HOUR_AGO, freshness_hours: 1.5, errors: [] },
        { department: "bank_partnerships", space_key: "BANK", state: "idle", page_count: 113, doc_count: 79, chunk_count: 956, last_success_at: DAY_AGO, freshness_hours: 24, errors: [] },
      ],
      recent_jobs: [
        { id: "job-020", source: "confluence", department: "risk", state: "failure", started_at: DAY_AGO, finished_at: DAY_AGO, pages_synced: 0, errors: ["Confluence API timeout after 30s"] },
        { id: "job-021", source: "gdrive", state: "failure", started_at: DAY_AGO, finished_at: DAY_AGO, pages_synced: 0, errors: ["Drive API quota exceeded"] },
        { id: "job-019", source: "confluence", department: "grow_enablement", state: "success", started_at: HOUR_AGO, finished_at: HOUR_AGO, pages_synced: 87 },
      ],
      sources: [
        { source: "gdrive", state: "error", doc_count: 34, chunk_count: 412, last_success_at: WEEK_AGO, freshness_hours: 168, errors: ["Drive API quota exceeded"] },
      ],
    },
    dashboard: {
      query_count: 342,
      deflection_rate: 0.41,
      answered_wrong_rate: 0.18,
      refusal_rate: 0.38,
      partial_rate: 0.13,
      conflict_rate: 0.06,
      latency_p50_ms: 2100,
      latency_p95_ms: 6400,
      feedback_up: 180,
      feedback_down: 112,
      total_tokens: 840_000,
      history: HISTORY_POOR,
    },
  },

  {
    key: "fresh_install",
    label: "Cài mới (chưa sync)",
    description: "Chưa có dữ liệu nào, cần chạy sync lần đầu",
    adminStatus: {
      running: false,
      departments: [
        { department: "risk", space_key: null, state: "idle", page_count: 0, doc_count: 0, chunk_count: 0, last_success_at: null, freshness_hours: null, errors: [] },
        { department: "grow_enablement", space_key: null, state: "idle", page_count: 0, doc_count: 0, chunk_count: 0, last_success_at: null, freshness_hours: null, errors: [] },
        { department: "bank_partnerships", space_key: null, state: "idle", page_count: 0, doc_count: 0, chunk_count: 0, last_success_at: null, freshness_hours: null, errors: [] },
      ],
      recent_jobs: [],
      sources: [
        { source: "gdrive", state: "idle", doc_count: 0, chunk_count: 0, last_success_at: null, freshness_hours: null, errors: [] },
      ],
    },
    dashboard: {
      query_count: 0,
      deflection_rate: 0,
      answered_wrong_rate: 0,
      refusal_rate: 0,
      partial_rate: 0,
      conflict_rate: 0,
      latency_p50_ms: 0,
      latency_p95_ms: 0,
      feedback_up: 0,
      feedback_down: 0,
      total_tokens: 0,
      history: [],
    },
  },

  {
    key: "stale",
    label: "Index cũ (stale)",
    description: "Sync thành công từ tuần trước, index đã lỗi thời",
    adminStatus: {
      running: false,
      departments: [
        { department: "risk", space_key: "RISK", state: "idle", page_count: 138, doc_count: 95, chunk_count: 1190, last_success_at: WEEK_AGO, freshness_hours: 168, errors: [] },
        { department: "grow_enablement", space_key: "GROW", state: "idle", page_count: 82, doc_count: 58, chunk_count: 740, last_success_at: WEEK_AGO, freshness_hours: 172, errors: [] },
        { department: "bank_partnerships", space_key: "BANK", state: "idle", page_count: 110, doc_count: 76, chunk_count: 920, last_success_at: WEEK_AGO, freshness_hours: 165, errors: [] },
      ],
      recent_jobs: [
        { id: "job-030", source: "confluence", department: "risk", state: "success", started_at: WEEK_AGO, finished_at: WEEK_AGO, pages_synced: 138 },
        { id: "job-031", source: "confluence", department: "grow_enablement", state: "success", started_at: WEEK_AGO, finished_at: WEEK_AGO, pages_synced: 82 },
        { id: "job-032", source: "gdrive", state: "success", started_at: WEEK_AGO, finished_at: WEEK_AGO, pages_synced: 28 },
      ],
      sources: [
        { source: "gdrive", state: "idle", doc_count: 28, chunk_count: 336, last_success_at: WEEK_AGO, freshness_hours: 165, errors: [] },
      ],
    },
    dashboard: {
      query_count: 892,
      deflection_rate: 0.71,
      answered_wrong_rate: 0.09,
      refusal_rate: 0.17,
      partial_rate: 0.08,
      conflict_rate: 0.03,
      latency_p50_ms: 1580,
      latency_p95_ms: 4200,
      feedback_up: 612,
      feedback_down: 89,
      total_tokens: 1_840_000,
      history: HISTORY_HEALTHY.slice(0, 5),
    },
  },
];

export const SCENARIO_MAP = Object.fromEntries(
  SCENARIOS.map((s) => [s.key, s]),
) as Record<ScenarioKey, Scenario>;
