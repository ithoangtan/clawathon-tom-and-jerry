import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { RotateCw, FileText } from "@/components/ui/icons";
import { useHealth } from "@/hooks/useHealth";
import { useAdminSyncStatus } from "@/hooks/useAdminSyncStatus";
import { api, ApiError } from "@/lib/apiClient";
import { DEPARTMENTS, departmentMetaLabel } from "@/lib/departments";
import { t } from "@/lib/i18n";
import { getUserContext, useUserStore } from "@/store/userStore";
import type { Department } from "@/lib/types";
import { useEffect, useRef, useState } from "react";

function useSyncTrigger() {
  const { refresh, status } = useAdminSyncStatus();
  const { refresh: refreshHealth } = useHealth();
  const [loadingKey, setLoadingKey] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wasRunningRef = useRef(false);
  const locale = useUserStore((s) => s.locale);

  const sources = status?.sources ?? [];
  const departments = status?.departments ?? [];
  const anyRunning =
    status?.running ||
    sources.some((s) => s.state === "running") ||
    departments.some((d) => d.state === "running");

  useEffect(() => {
    if (wasRunningRef.current && !anyRunning) {
      refreshHealth();
    }
    wasRunningRef.current = Boolean(anyRunning);
  }, [anyRunning, refreshHealth]);

  async function trigger(source: "confluence" | "gdrive", department?: Department) {
    const key = department ?? source;
    setLoadingKey(key);
    setMessage(null);
    setError(null);
    try {
      const res = await api.adminSync(
        { source, department: department ?? null },
        getUserContext(),
      );
      setMessage(res.message || t("adminSyncStarted", locale));
      if (!res.started) {
        setError(t("adminSyncInProgress", locale));
      }
      refresh();
      refreshHealth();
    } catch (e) {
      setError(
        e instanceof ApiError ? (e.detail ?? e.message) : t("adminSyncFailed", locale),
      );
    } finally {
      setLoadingKey(null);
    }
  }

  return { status, loadingKey, message, error, anyRunning, trigger };
}

export function ConfluenceSyncControls() {
  const locale = useUserStore((s) => s.locale);
  const { status, loadingKey, message, error, anyRunning, trigger } = useSyncTrigger();
  const departments = status?.departments ?? [];

  return (
    <Card>
      <div className="flex items-start gap-3">
        <div
          className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-brand-muted text-brand"
          aria-hidden
        >
          <RotateCw size="md" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-slate-800">{t("adminSyncActions", locale)}</h3>
          <p className="mt-0.5 text-xs text-slate-500">{t("syncConfluence", locale)}</p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-3">
        <Button
          variant="primary"
          loading={loadingKey === "confluence"}
          disabled={Boolean(anyRunning)}
          onClick={() => trigger("confluence")}
        >
          {anyRunning ? t("syncing", locale) : t("adminSyncAll", locale)}
        </Button>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
        {DEPARTMENTS.map((dept) => {
          const label = departmentMetaLabel(dept, locale);
          const deptRunning =
            departments.find((d) => d.department === dept.key)?.state === "running";
          return (
            <Button
              key={dept.key}
              variant="secondary"
              loading={loadingKey === dept.key}
              disabled={Boolean(anyRunning)}
              onClick={() => trigger("confluence", dept.key)}
              className="justify-start truncate"
            >
              <span className="truncate">
                {deptRunning ? t("syncing", locale) : t("adminSyncDepartment", locale, { department: label })}
              </span>
            </Button>
          );
        })}
      </div>

      {message && (
        <p className="mt-4 text-sm text-emerald-700" role="status">
          {message}
        </p>
      )}
      {error && (
        <p className="mt-2 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </Card>
  );
}

export function GDriveSyncControls() {
  const locale = useUserStore((s) => s.locale);
  const { status, loadingKey, message, error, anyRunning, trigger } = useSyncTrigger();
  const gdriveSource = status?.sources.find((s) => s.source === "gdrive");
  const gdriveRunning = gdriveSource?.state === "running";

  return (
    <Card>
      <div className="flex items-start gap-3">
        <div
          className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-accent/10 text-accent"
          aria-hidden
        >
          <FileText size="md" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-slate-800">{t("syncGdrive", locale)}</h3>
          <p className="mt-0.5 text-xs text-slate-500">{t("adminGdriveHint", locale)}</p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-4">
        <Button
          variant="secondary"
          loading={loadingKey === "gdrive"}
          disabled={Boolean(anyRunning)}
          onClick={() => trigger("gdrive")}
        >
          {gdriveRunning ? t("syncing", locale) : t("syncGdrive", locale)}
        </Button>

        {gdriveSource && (
          <dl className="flex gap-6 text-sm">
            <div>
              <dt className="text-xs text-slate-500">{t("docs", locale)}</dt>
              <dd className="font-medium">{(gdriveSource.doc_count ?? 0).toLocaleString()}</dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">{t("chunks", locale)}</dt>
              <dd className="font-medium">{(gdriveSource.chunk_count ?? 0).toLocaleString()}</dd>
            </div>
          </dl>
        )}
      </div>

      {message && (
        <p className="mt-4 text-sm text-emerald-700" role="status">
          {message}
        </p>
      )}
      {error && (
        <p className="mt-2 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </Card>
  );
}

/** @deprecated Use ConfluenceSyncControls instead */
export function AdminSyncControls() {
  return <ConfluenceSyncControls />;
}
