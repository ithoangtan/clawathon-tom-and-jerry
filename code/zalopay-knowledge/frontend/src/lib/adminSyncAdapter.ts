import { DEPARTMENTS } from "@/lib/departments";
import type {
  AdminDepartmentSyncStatus,
  AdminSyncJob,
  AdminSyncStatus,
  Department,
  SourceStatus,
} from "@/lib/types";
import type {
  AdminDepartmentIndexWire,
  AdminDepartmentResultWire,
  AdminJobStatusWire,
  AdminSyncHistoryEntryWire,
  AdminSyncStatusWire,
} from "@/lib/types";

const ADMIN_SOURCES = ["confluence", "gdrive"] as const;

function emptyAdminSyncStatus(): AdminSyncStatus {
  return {
    running: false,
    departments: [],
    recent_jobs: [],
    sources: [],
  };
}

function freshnessHoursFromIso(iso: string | null | undefined): number | null {
  if (!iso) return null;
  const parsed = Date.parse(iso.replace("Z", "+00:00"));
  if (Number.isNaN(parsed)) return null;
  return (Date.now() - parsed) / 3_600_000;
}

function mapJobStatusToSourceState(status: AdminJobStatusWire): SourceStatus["state"] {
  if (status === "running") return "running";
  if (status === "failed") return "error";
  return "idle";
}

function mapDeptStatusToState(status: AdminJobStatusWire): AdminDepartmentSyncStatus["state"] {
  if (status === "running") return "running";
  if (status === "failed") return "error";
  return "idle";
}

function mapHistoryStatusToJobState(status: AdminJobStatusWire): AdminSyncJob["state"] {
  if (status === "running") return "running";
  if (status === "success") return "success";
  return "failure";
}

function isWireAdminSyncStatus(data: object): data is AdminSyncStatusWire {
  return "jobs" in data || "departments_indexed" in data;
}

function isLegacyAdminSyncStatus(data: object): boolean {
  return "sources" in data || "recent_jobs" in data || "running" in data;
}

function normalizeLegacyAdminSyncStatus(
  data: Partial<AdminSyncStatus> | null | undefined,
): AdminSyncStatus {
  return {
    running: data?.running ?? false,
    departments: data?.departments ?? [],
    recent_jobs: data?.recent_jobs ?? [],
    sources: data?.sources ?? [],
  };
}

function buildSources(jobs: AdminSyncStatusWire["jobs"]): SourceStatus[] {
  return ADMIN_SOURCES.map((source) => {
    const job = jobs?.[source];
    if (!job) {
      return {
        source,
        state: "idle",
        doc_count: 0,
        chunk_count: 0,
        errors: [],
      };
    }

    return {
      source,
      state: mapJobStatusToSourceState(job.status ?? "pending"),
      doc_count: job.doc_count ?? 0,
      chunk_count: job.chunk_count ?? 0,
      last_success_at: job.last_success_at ?? null,
      freshness_hours: freshnessHoursFromIso(job.last_success_at),
      errors: job.errors ?? [],
      progress: job.progress ?? null,
    };
  });
}

function buildDepartments(
  jobs: AdminSyncStatusWire["jobs"],
  departmentsIndexed: Partial<Record<Department, AdminDepartmentIndexWire>>,
): AdminDepartmentSyncStatus[] {
  const confluenceJob = jobs?.confluence;
  const deptResults = new Map<Department, AdminDepartmentResultWire>(
    (confluenceJob?.departments ?? []).map((d) => [d.department, d]),
  );

  return DEPARTMENTS.map(({ key }) => {
    const indexed = departmentsIndexed[key] ?? {
      chunk_count: 0,
      doc_count: 0,
      has_data: false,
    };
    const result = deptResults.get(key);
    const state = result
      ? mapDeptStatusToState(result.status ?? "pending")
      : "idle";
    const lastSuccessAt =
      result?.status === "success" ? (confluenceJob?.last_success_at ?? null) : null;

    return {
      department: key,
      space_key: result?.space_key ?? null,
      state,
      page_count: result?.page_count ?? 0,
      doc_count: indexed.doc_count ?? 0,
      chunk_count: result?.chunk_count ?? indexed.chunk_count ?? 0,
      last_success_at: lastSuccessAt,
      freshness_hours: freshnessHoursFromIso(lastSuccessAt),
      errors: result?.errors ?? [],
      progress: state === "running" ? (confluenceJob?.progress ?? null) : null,
    };
  });
}

function buildRecentJobs(entries: AdminSyncHistoryEntryWire[]): AdminSyncJob[] {
  return entries.map((entry) => ({
    id: entry.job_id,
    source: entry.source === "gdrive" ? "gdrive" : "confluence",
    department: entry.department ?? null,
    state: mapHistoryStatusToJobState(entry.status ?? "pending"),
    started_at: entry.started_at,
    finished_at: entry.finished_at ?? null,
    pages_synced: entry.doc_count ?? null,
    errors: entry.errors ?? [],
  }));
}

function isAnyRunning(
  jobs: AdminSyncStatusWire["jobs"],
  departments: AdminDepartmentSyncStatus[],
  sources: SourceStatus[],
): boolean {
  const jobRunning = Object.values(jobs ?? {}).some((job) => job?.status === "running");
  const deptRunning = departments.some((d) => d.state === "running");
  const sourceRunning = sources.some((s) => s.state === "running");
  return jobRunning || deptRunning || sourceRunning;
}

function normalizeWireAdminSyncStatus(
  data: AdminSyncStatusWire,
  historyEntries: AdminSyncHistoryEntryWire[] = [],
): AdminSyncStatus {
  const jobs = data.jobs ?? {};
  const departments = buildDepartments(jobs, data.departments_indexed ?? {});
  const sources = buildSources(jobs);
  const recent_jobs = buildRecentJobs(historyEntries);

  return {
    running: isAnyRunning(jobs, departments, sources),
    departments,
    recent_jobs,
    sources,
  };
}

/** Normalize GET /api/admin/sync/status (+ optional history) into UI state. */
export function normalizeAdminSyncPayload(
  statusData: AdminSyncStatusWire | Partial<AdminSyncStatus> | null | undefined,
  historyEntries: AdminSyncHistoryEntryWire[] = [],
): AdminSyncStatus {
  if (!statusData || typeof statusData !== "object") {
    return emptyAdminSyncStatus();
  }

  if (isWireAdminSyncStatus(statusData)) {
    return normalizeWireAdminSyncStatus(statusData, historyEntries);
  }

  if (isLegacyAdminSyncStatus(statusData)) {
    return normalizeLegacyAdminSyncStatus(statusData);
  }

  return emptyAdminSyncStatus();
}
