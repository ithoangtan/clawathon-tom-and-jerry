import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { FreshnessBadge } from "@/components/ui/FreshnessBadge";
import { ErrorState } from "@/components/ui/StateViews";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { formatDate, formatFreshnessHours } from "@/lib/format";
import { departmentLabel, getDepartment } from "@/lib/departments";
import { sourceLabel, syncStateLabel, t } from "@/lib/i18n";
import { useAdminSyncStatus } from "@/hooks/useAdminSyncStatus";
import { useUserStore } from "@/store/userStore";
import type { AdminDepartmentSyncStatus, AdminSyncJob } from "@/lib/types";

function jobStateLabel(state: AdminSyncJob["state"], locale: "en" | "vi"): string {
  if (state === "running") return t("adminJobRunning", locale);
  if (state === "success") return t("adminJobSuccess", locale);
  return t("adminJobFailure", locale);
}

function jobStateTone(state: AdminSyncJob["state"]): "info" | "success" | "danger" {
  if (state === "running") return "info";
  if (state === "success") return "success";
  return "danger";
}

export function DepartmentStatusSection() {
  const locale = useUserStore((s) => s.locale);
  const { status, error, loading, refresh } = useAdminSyncStatus();

  if (loading && !status) return <LoadingSpinner />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;

  const departments = status?.departments ?? [];
  if (departments.length === 0) return null;

  return (
    <section aria-labelledby="admin-dept-heading" className="space-y-4">
      <h3 id="admin-dept-heading" className="section-title">
        {t("adminDepartmentStatus", locale)}
      </h3>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4" role="list">
        {departments.map((dept) => (
          <DepartmentCard key={dept.department} dept={dept} />
        ))}
      </div>
    </section>
  );
}

export function RecentJobsSection() {
  const locale = useUserStore((s) => s.locale);
  const { status, error, loading, refresh } = useAdminSyncStatus();

  if (loading && !status) return <LoadingSpinner />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;

  const jobs = status?.recent_jobs ?? [];

  return (
    <section aria-labelledby="admin-jobs-heading">
      <Card>
        <h3 id="admin-jobs-heading" className="section-title mb-0">
          {t("adminRecentJobs", locale)}
        </h3>
        {jobs.length === 0 ? (
          <p className="mt-4 text-sm text-slate-500" role="status">
            {t("adminNoJobs", locale)}
          </p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-2 py-2 font-medium">{t("adminJobStarted", locale)}</th>
                  <th className="px-2 py-2 font-medium">{t("adminJobSource", locale)}</th>
                  <th className="px-2 py-2 font-medium">{t("adminJobDepartment", locale)}</th>
                  <th className="px-2 py-2 font-medium">{t("adminJobStatus", locale)}</th>
                  <th className="px-2 py-2 font-medium">{t("adminPages", locale)}</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <JobRow key={job.id} job={job} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </section>
  );
}

/** @deprecated Use DepartmentStatusSection + RecentJobsSection instead */
export function AdminSyncStatusPanel() {
  return (
    <div className="space-y-8">
      <DepartmentStatusSection />
      <RecentJobsSection />
    </div>
  );
}

function DepartmentCard({ dept }: { dept: AdminDepartmentSyncStatus }) {
  const locale = useUserStore((s) => s.locale);
  const meta = getDepartment(dept.department);
  const stateTone =
    dept.state === "running" ? "info" : dept.state === "error" ? "danger" : "default";

  return (
    <Card role="listitem" className="border-l-4" style={{ borderLeftColor: meta.accent_color }}>
      <div className="flex items-start justify-between gap-2">
        <h4 className="font-semibold text-slate-800">
          {departmentLabel(dept.department, locale)}
        </h4>
        <div className="flex flex-wrap justify-end gap-2">
          <Badge tone={stateTone}>{syncStateLabel(dept.state, locale)}</Badge>
          <FreshnessBadge
            lastSuccessAt={dept.last_success_at}
            freshnessHours={dept.freshness_hours}
          />
        </div>
      </div>

      {dept.space_key && (
        <p className="mt-2 text-xs text-slate-500">
          {t("adminSpace", locale)}: <span className="font-mono text-slate-700">{dept.space_key}</span>
        </p>
      )}

      <dl className="mt-3 grid grid-cols-3 gap-2 text-sm">
        <div>
          <dt className="text-slate-500">{t("adminPages", locale)}</dt>
          <dd className="font-medium">{(dept.page_count ?? 0).toLocaleString()}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t("docs", locale)}</dt>
          <dd className="font-medium">{(dept.doc_count ?? 0).toLocaleString()}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t("chunks", locale)}</dt>
          <dd className="font-medium">{(dept.chunk_count ?? 0).toLocaleString()}</dd>
        </div>
      </dl>

      {dept.last_success_at && (
        <p className="mt-2 text-xs text-slate-500">
          {t("lastSync", locale, { date: formatDate(dept.last_success_at, locale) })}
          {dept.freshness_hours != null && (
            <span> · {formatFreshnessHours(dept.freshness_hours, locale)}</span>
          )}
        </p>
      )}

      {dept.progress && (
        <p className="mt-2 text-xs text-brand">
          {Object.entries(dept.progress)
            .map(([k, v]) => `${k.replace(/_/g, " ")}: ${String(v)}`)
            .join(" · ")}
        </p>
      )}

      {(dept.errors?.length ?? 0) > 0 && (
        <ul className="mt-2 text-xs text-red-600" role="alert">
          {(dept.errors ?? []).map((err, i) => (
            <li key={i}>{err}</li>
          ))}
        </ul>
      )}
    </Card>
  );
}


function JobRow({ job }: { job: AdminSyncJob }) {
  const locale = useUserStore((s) => s.locale);

  return (
    <tr className="border-b border-slate-100 last:border-0">
      <td className="px-2 py-3 text-slate-700">
        {formatDate(job.started_at, locale)}
        {job.finished_at && (
          <span className="block text-xs text-slate-500">
            {t("adminJobFinished", locale)}: {formatDate(job.finished_at, locale)}
          </span>
        )}
      </td>
      <td className="px-2 py-3">{sourceLabel(job.source, locale)}</td>
      <td className="px-2 py-3">
        {job.department
          ? departmentLabel(job.department, locale)
          : t("adminJobAllDepartments", locale)}
      </td>
      <td className="px-2 py-3">
        <Badge tone={jobStateTone(job.state)}>{jobStateLabel(job.state, locale)}</Badge>
        {job.errors && job.errors.length > 0 && (
          <p className="mt-1 text-xs text-red-600">{job.errors[0]}</p>
        )}
        {job.message && <p className="mt-1 text-xs text-slate-500">{job.message}</p>}
      </td>
      <td className="px-2 py-3 font-medium">
        {job.pages_synced != null ? job.pages_synced.toLocaleString() : "—"}
      </td>
    </tr>
  );
}
