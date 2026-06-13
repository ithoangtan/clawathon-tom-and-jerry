import { useEffect } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { FreshnessBadge } from "@/components/ui/FreshnessBadge";
import { X, RotateCw, FileText } from "@/components/ui/icons";
import { formatDate, formatFreshnessHours } from "@/lib/format";
import { syncStateLabel, t } from "@/lib/i18n";
import { getDepartment, departmentLabel } from "@/lib/departments";
import type { AdminDepartmentSyncStatus, SourceStatus, Department } from "@/lib/types";
import { useUserStore } from "@/store/userStore";

export type ModalRow =
  | { kind: "confluence"; dept: AdminDepartmentSyncStatus }
  | { kind: "gdrive"; source: SourceStatus };

interface Props {
  row: ModalRow | null;
  anyRunning: boolean;
  loadingKey: string | null;
  onClose: () => void;
  onSync: (source: "confluence" | "gdrive", dept?: Department) => void;
}

export function AdminDetailModal({ row, anyRunning, loadingKey, onClose, onSync }: Props) {
  const locale = useUserStore((s) => s.locale);

  useEffect(() => {
    if (!row) return;
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [row, onClose]);

  if (!row) return null;

  const isConfluence = row.kind === "confluence";
  const dept = isConfluence ? row.dept : null;
  const src = !isConfluence ? row.source : null;
  const meta = dept ? getDepartment(dept.department) : null;

  const title = isConfluence
    ? departmentLabel(dept!.department, locale)
    : t("syncGdrive", locale);

  const state = isConfluence ? dept!.state : src!.state;
  const stateTone = state === "running" ? "info" : state === "error" ? "danger" : "default";

  const docCount = isConfluence ? dept!.doc_count : src!.doc_count;
  const chunkCount = isConfluence ? dept!.chunk_count : src!.chunk_count;
  const lastSuccessAt = isConfluence ? dept!.last_success_at : src!.last_success_at;
  const freshnessHours = isConfluence ? dept!.freshness_hours : src!.freshness_hours;
  const errors = isConfluence ? dept!.errors : src!.errors;
  const progress = isConfluence ? dept!.progress : src!.progress;

  const syncKey = isConfluence ? dept!.department : "gdrive";
  const isLoadingThis = loadingKey === syncKey;

  function handleSync() {
    if (isConfluence) {
      onSync("confluence", dept!.department);
    } else {
      onSync("gdrive");
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="relative w-full max-w-lg rounded-2xl bg-white shadow-2xl ring-1 ring-slate-200">
        {/* Header */}
        <div
          className="flex items-center gap-3 rounded-t-2xl p-5"
          style={meta ? { borderBottom: `3px solid ${meta.accent_color}` } : { borderBottom: "3px solid #6366f1" }}
        >
          <div
            className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl"
            style={meta ? { background: `${meta.accent_color}18`, color: meta.accent_color } : { background: "#6366f118", color: "#6366f1" }}
          >
            {isConfluence ? <RotateCw size="md" /> : <FileText size="md" />}
          </div>
          <div className="min-w-0 flex-1">
            <h2 id="modal-title" className="font-semibold text-slate-800">{title}</h2>
            {isConfluence && dept?.space_key && (
              <p className="text-xs text-slate-500">
                {t("adminSpace", locale)}: <span className="font-mono">{dept.space_key}</span>
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
            aria-label={t("adminClose", locale)}
          >
            <X size="sm" />
          </button>
        </div>

        {/* Body */}
        <div className="space-y-5 p-5">
          {/* Status & freshness */}
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={stateTone}>{syncStateLabel(state, locale)}</Badge>
            <FreshnessBadge lastSuccessAt={lastSuccessAt} freshnessHours={freshnessHours} />
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-3">
            {isConfluence && (
              <div className="rounded-xl bg-slate-50 p-3 text-center">
                <p className="text-xs text-slate-500">{t("adminPagesLabel", locale)}</p>
                <p className="mt-1 text-xl font-bold text-slate-800 tabular-nums">
                  {(dept?.page_count ?? 0).toLocaleString()}
                </p>
              </div>
            )}
            <div className="rounded-xl bg-slate-50 p-3 text-center">
              <p className="text-xs text-slate-500">{t("docs", locale)}</p>
              <p className="mt-1 text-xl font-bold text-slate-800 tabular-nums">
                {(docCount ?? 0).toLocaleString()}
              </p>
            </div>
            <div className="rounded-xl bg-slate-50 p-3 text-center">
              <p className="text-xs text-slate-500">{t("chunks", locale)}</p>
              <p className="mt-1 text-xl font-bold text-slate-800 tabular-nums">
                {(chunkCount ?? 0).toLocaleString()}
              </p>
            </div>
          </div>

          {/* Last sync */}
          {lastSuccessAt && (
            <p className="text-sm text-slate-500">
              {t("lastSync", locale, { date: formatDate(lastSuccessAt, locale) })}
              {freshnessHours != null && (
                <span className="ml-2 text-slate-400">
                  · {formatFreshnessHours(freshnessHours, locale)}
                </span>
              )}
            </p>
          )}

          {/* Progress */}
          {progress && state === "running" && (
            <div className="rounded-lg bg-brand-muted/50 p-3 text-sm text-brand">
              {Object.entries(progress)
                .map(([k, v]) => `${k.replace(/_/g, " ")}: ${String(v)}`)
                .join(" · ")}
            </div>
          )}

          {/* Errors */}
          {errors.length > 0 && (
            <ul className="space-y-1 rounded-lg bg-red-50 p-3 text-sm text-red-700" role="alert">
              {errors.map((err, i) => (
                <li key={i} className="leading-snug">{err}</li>
              ))}
            </ul>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 border-t border-slate-100 px-5 py-4">
          <Button variant="secondary" onClick={onClose}>
            {t("adminClose", locale)}
          </Button>
          <Button
            variant="primary"
            loading={isLoadingThis}
            disabled={Boolean(anyRunning)}
            onClick={handleSync}
          >
            <RotateCw size="sm" />
            {t("adminSyncThis", locale)}
          </Button>
        </div>
      </div>
    </div>
  );
}
