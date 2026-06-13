import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { FreshnessBadge } from "@/components/ui/FreshnessBadge";
import { ErrorState } from "@/components/ui/StateViews";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { RotateCw, ArrowRight } from "@/components/ui/icons";
import { formatFreshnessHours } from "@/lib/format";
import { departmentLabel, getDepartment } from "@/lib/departments";
import { syncStateLabel, t } from "@/lib/i18n";
import { useAdminSyncStatus } from "@/hooks/useAdminSyncStatus";
import { api, ApiError } from "@/lib/apiClient";
import { getUserContext, useUserStore } from "@/store/userStore";
import { useHealth } from "@/hooks/useHealth";
import type { Department } from "@/lib/types";
import { AdminDetailModal, type ModalRow } from "./AdminDetailModal";

type Filter = "all" | "confluence" | "gdrive";

export function AdminSyncTable() {
  const locale = useUserStore((s) => s.locale);
  const { status, loading, error, refresh } = useAdminSyncStatus();
  const { loadingKey, message, syncError, anyRunning, trigger } = useSyncTableActions();
  const [selectedRow, setSelectedRow] = useState<ModalRow | null>(null);
  const [filter, setFilter] = useState<Filter>("all");

  if (loading && !status) return <LoadingSpinner />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;

  const depts = status?.departments ?? [];
  const gdrive = status?.sources.find((s) => s.source === "gdrive");

  const confluenceRows = depts.map((dept) => ({ kind: "confluence" as const, dept }));
  const gdriveRow = gdrive ? [{ kind: "gdrive" as const, source: gdrive }] : [];

  const allRows: ModalRow[] =
    filter === "confluence"
      ? confluenceRows
      : filter === "gdrive"
        ? gdriveRow
        : [...confluenceRows, ...gdriveRow];

  return (
    <>
      <Card className="overflow-hidden p-0">
        {/* Table header */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-content-primary">{t("adminKnowledgeSources", locale)}</h3>
            {anyRunning && (
              <Badge tone="info">{t("syncing", locale)}</Badge>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {/* Filter tabs */}
            <div className="flex rounded-lg border border-border bg-surface-glass p-0.5 text-xs">
              {(["all", "confluence", "gdrive"] as Filter[]).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`rounded-md px-3 py-1.5 font-medium transition-colors ${
                    filter === f
                      ? "bg-surface-elevated text-content-primary shadow-sm"
                      : "text-content-secondary hover:text-content-primary"
                  }`}
                >
                  {f === "all"
                    ? t("adminFilterAll", locale)
                    : f === "confluence"
                      ? t("adminFilterConfluence", locale)
                      : t("adminFilterDrive", locale)}
                </button>
              ))}
            </div>
            {/* Sync all */}
            <Button
              variant="primary"
              loading={loadingKey === "confluence"}
              disabled={anyRunning}
              onClick={() => trigger("confluence")}
            >
              <RotateCw size="sm" />
              {anyRunning ? t("syncing", locale) : t("adminSyncAll", locale)}
            </Button>
          </div>
        </div>

        {/* Feedback */}
        {message && (
          <p className="border-b border-emerald-100 bg-emerald-50 px-5 py-2 text-sm text-emerald-700" role="status">
            {message}
          </p>
        )}
        {syncError && (
          <p className="border-b border-red-100 bg-red-50 px-5 py-2 text-sm text-red-600" role="alert">
            {syncError}
          </p>
        )}

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="border-b border-border text-xs uppercase tracking-wide text-content-muted">
                <th className="px-5 py-3 font-medium">Nguồn</th>
                <th className="px-4 py-3 font-medium">Trạng thái</th>
                <th className="px-4 py-3 font-medium text-right">Tài liệu</th>
                <th className="px-4 py-3 font-medium text-right">Chunks</th>
                <th className="px-4 py-3 font-medium">Cập nhật</th>
                <th className="px-4 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {allRows.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-slate-400">
                    {t("adminNoData", locale)}
                  </td>
                </tr>
              ) : (
                allRows.map((row, i) => (
                  <SyncTableRow
                    key={i}
                    row={row}
                    anyRunning={anyRunning}
                    loadingKey={loadingKey}
                    onSync={trigger}
                    onDetail={() => setSelectedRow(row)}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <AdminDetailModal
        row={selectedRow}
        anyRunning={anyRunning}
        loadingKey={loadingKey}
        onClose={() => setSelectedRow(null)}
        onSync={trigger}
      />
    </>
  );
}

function useSyncTableActions() {
  const { refresh, status } = useAdminSyncStatus();
  const { refresh: refreshHealth } = useHealth();
  const [loadingKey, setLoadingKey] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);
  const locale = useUserStore((s) => s.locale);

  const sources = status?.sources ?? [];
  const departments = status?.departments ?? [];
  const anyRunning = Boolean(
    status?.running ||
    sources.some((s) => s.state === "running") ||
    departments.some((d) => d.state === "running"),
  );

  async function trigger(source: "confluence" | "gdrive", department?: Department) {
    const key = department ?? source;
    setLoadingKey(key);
    setMessage(null);
    setSyncError(null);
    try {
      const res = await api.adminSync(
        { source, department: department ?? null },
        getUserContext(),
      );
      setMessage(res.message || t("adminSyncStarted", locale));
      if (!res.started) setSyncError(t("adminSyncInProgress", locale));
      refresh();
      refreshHealth();
    } catch (e) {
      setSyncError(e instanceof ApiError ? (e.detail ?? e.message) : t("adminSyncFailed", locale));
    } finally {
      setLoadingKey(null);
    }
  }

  return { loadingKey, message, syncError, anyRunning, trigger };
}

interface RowProps {
  row: ModalRow;
  anyRunning: boolean;
  loadingKey: string | null;
  onSync: (source: "confluence" | "gdrive", dept?: Department) => void;
  onDetail: () => void;
}

function SyncTableRow({ row, anyRunning, loadingKey, onSync, onDetail }: RowProps) {
  const locale = useUserStore((s) => s.locale);

  if (row.kind === "confluence") {
    const { dept } = row;
    let meta: ReturnType<typeof getDepartment> | null = null;
    try { meta = getDepartment(dept.department); } catch { /* skip */ }
    const syncKey = dept.department;
    const isLoading = loadingKey === syncKey;
    const stateTone = dept.state === "running" ? "info" : dept.state === "error" ? "danger" : "default";

    return (
      <tr className="group border-b border-border/60 transition-colors hover:bg-surface-glass last:border-0">
        <td className="px-5 py-3.5">
          <div className="flex items-center gap-2.5">
            <span
              className="h-2.5 w-2.5 flex-shrink-0 rounded-full"
              style={{ background: meta?.accent_color ?? "#94a3b8" }}
            />
            <div>
              <p className="font-medium text-content-primary">{departmentLabel(dept.department, locale)}</p>
              <p className="text-xs text-content-muted">{t("adminTypeConfluence", locale)}</p>
            </div>
          </div>
        </td>
        <td className="px-4 py-3.5">
          <div className="flex flex-col gap-1">
            <Badge tone={stateTone}>{syncStateLabel(dept.state, locale)}</Badge>
            <FreshnessBadge lastSuccessAt={dept.last_success_at} freshnessHours={dept.freshness_hours} />
          </div>
        </td>
        <td className="px-4 py-3.5 text-right tabular-nums">
          <p className="font-medium text-content-primary">{(dept.doc_count ?? 0).toLocaleString()}</p>
          {dept.page_count > 0 && (
            <p className="text-xs text-content-muted">{dept.page_count.toLocaleString()} {t("adminPagesLabel", locale)}</p>
          )}
        </td>
        <td className="px-4 py-3.5 text-right tabular-nums font-medium text-content-primary">
          {(dept.chunk_count ?? 0).toLocaleString()}
        </td>
        <td className="px-4 py-3.5 text-content-secondary text-xs">
          {dept.freshness_hours != null
            ? formatFreshnessHours(dept.freshness_hours, locale)
            : dept.last_success_at
              ? "—"
              : t("adminNeverSynced", locale)}
        </td>
        <td className="px-4 py-3.5">
          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              variant="secondary"
              loading={isLoading}
              disabled={anyRunning}
              onClick={(e) => { e.stopPropagation(); onSync("confluence", dept.department); }}
              className="py-1 px-2 text-xs"
            >
              <RotateCw size="xs" />
            </Button>
            <button
              onClick={onDetail}
              className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs text-brand hover:bg-brand-muted transition-colors"
            >
              {t("adminViewDetail", locale)} <ArrowRight size="xs" />
            </button>
          </div>
        </td>
      </tr>
    );
  }

  // GDrive row
  const { source } = row;
  const isLoading = loadingKey === "gdrive";
  const stateTone = source.state === "running" ? "info" : source.state === "error" ? "danger" : "default";

  return (
    <tr className="group border-b border-border/60 transition-colors hover:bg-surface-glass last:border-0">
      <td className="px-5 py-3.5">
        <div className="flex items-center gap-2.5">
          <span className="h-2.5 w-2.5 flex-shrink-0 rounded-full bg-accent" />
          <div>
            <p className="font-medium text-content-primary">{t("syncGdrive", locale)}</p>
            <p className="text-xs text-content-muted">{t("adminTypeDrive", locale)}</p>
          </div>
        </div>
      </td>
      <td className="px-4 py-3.5">
        <div className="flex flex-col gap-1">
          <Badge tone={stateTone}>{syncStateLabel(source.state, locale)}</Badge>
          <FreshnessBadge lastSuccessAt={source.last_success_at} freshnessHours={source.freshness_hours} />
        </div>
      </td>
      <td className="px-4 py-3.5 text-right tabular-nums">
        <p className="font-medium text-content-primary">{(source.doc_count ?? 0).toLocaleString()}</p>
        <p className="text-xs text-content-muted">{t("adminFilesLabel", locale)}</p>
      </td>
      <td className="px-4 py-3.5 text-right tabular-nums font-medium text-content-primary">
        {(source.chunk_count ?? 0).toLocaleString()}
      </td>
      <td className="px-4 py-3.5 text-content-secondary text-xs">
        {source.freshness_hours != null
          ? formatFreshnessHours(source.freshness_hours, locale)
          : source.last_success_at
            ? "—"
            : t("adminNeverSynced", locale)}
      </td>
      <td className="px-4 py-3.5">
        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            variant="secondary"
            loading={isLoading}
            disabled={anyRunning}
            onClick={(e) => { e.stopPropagation(); onSync("gdrive"); }}
            className="py-1 px-2 text-xs"
          >
            <RotateCw size="xs" />
          </Button>
          <button
            onClick={onDetail}
            className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs text-brand hover:bg-brand-muted transition-colors"
          >
            {t("adminViewDetail", locale)} <ArrowRight size="xs" />
          </button>
        </div>
      </td>
    </tr>
  );
}
