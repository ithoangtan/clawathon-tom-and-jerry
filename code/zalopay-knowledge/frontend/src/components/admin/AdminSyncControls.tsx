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
  const [loadingKeys, setLoadingKeys] = useState<Set<string>>(new Set());
  const [messages, setMessages] = useState<Map<string, string>>(new Map());
  const [errors, setErrors] = useState<Map<string, string>>(new Map());
  const wasRunningRef = useRef(false);
  const locale = useUserStore((s) => s.locale);

  const sources = status?.sources ?? [];
  const departments = status?.departments ?? [];
  const confluenceSource = sources.find((s) => s.source === "confluence");
  const gdriveSource = sources.find((s) => s.source === "gdrive");

  // sync-all is running (blocks per-dept buttons)
  const syncAllRunning = confluenceSource?.sync_all_running ?? false;
  // any confluence sync is running (blocks the Sync All button)
  const confluenceRunning = confluenceSource?.state === "running";
  const gdriveRunning = gdriveSource?.state === "running";
  const anyRunning = confluenceRunning || gdriveRunning;

  useEffect(() => {
    if (wasRunningRef.current && !anyRunning) {
      refreshHealth();
    }
    wasRunningRef.current = Boolean(anyRunning);
  }, [anyRunning, refreshHealth]);

  function isDeptRunning(dept: Department): boolean {
    return departments.find((d) => d.department === dept)?.state === "running";
  }

  async function trigger(source: "confluence" | "gdrive", department?: Department) {
    const key = department ?? source;
    setLoadingKeys((prev) => new Set(prev).add(key));
    setMessages((prev) => { const m = new Map(prev); m.delete(key); return m; });
    setErrors((prev) => { const m = new Map(prev); m.delete(key); return m; });
    try {
      const res = await api.adminSync(
        { source, department: department ?? null },
        getUserContext(),
      );
      setMessages((prev) => new Map(prev).set(key, res.message || t("adminSyncStarted", locale)));
      if (!res.started) {
        setErrors((prev) => new Map(prev).set(key, t("adminSyncInProgress", locale)));
      }
      refresh();
      refreshHealth();
    } catch (e) {
      setErrors((prev) =>
        new Map(prev).set(
          key,
          e instanceof ApiError ? (e.detail ?? e.message) : t("adminSyncFailed", locale),
        ),
      );
    } finally {
      setLoadingKeys((prev) => { const s = new Set(prev); s.delete(key); return s; });
    }
  }

  return {
    status,
    loadingKeys,
    messages,
    errors,
    syncAllRunning,
    confluenceRunning,
    gdriveRunning,
    isDeptRunning,
    trigger,
  };
}

export function ConfluenceSyncControls() {
  const locale = useUserStore((s) => s.locale);
  const {
    loadingKeys,
    messages,
    errors,
    syncAllRunning,
    confluenceRunning,
    isDeptRunning,
    trigger,
  } = useSyncTrigger();

  // Collect all messages/errors to show (latest non-null entries)
  const latestMessage = Array.from(messages.values()).at(-1) ?? null;
  const latestError = Array.from(errors.values()).at(-1) ?? null;

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
          loading={loadingKeys.has("confluence")}
          disabled={confluenceRunning}
          onClick={() => trigger("confluence")}
        >
          {syncAllRunning ? t("syncing", locale) : t("adminSyncAll", locale)}
        </Button>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
        {DEPARTMENTS.map((dept) => {
          const label = departmentMetaLabel(dept, locale);
          const deptRunning = isDeptRunning(dept.key);
          // Disable if sync-all is running OR this specific dept is already syncing
          const isDisabled = syncAllRunning || deptRunning;
          return (
            <Button
              key={dept.key}
              variant="secondary"
              loading={loadingKeys.has(dept.key)}
              disabled={isDisabled}
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

      {latestMessage && (
        <p className="mt-4 text-sm text-emerald-700" role="status">
          {latestMessage}
        </p>
      )}
      {latestError && (
        <p className="mt-2 text-sm text-red-600" role="alert">
          {latestError}
        </p>
      )}
    </Card>
  );
}

export function GDriveSyncControls() {
  const locale = useUserStore((s) => s.locale);
  const { status, loadingKeys, messages, errors, gdriveRunning, trigger } = useSyncTrigger();
  const gdriveSource = status?.sources.find((s) => s.source === "gdrive");
  const gdriveMessage = messages.get("gdrive") ?? null;
  const gdriveError = errors.get("gdrive") ?? null;

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
          loading={loadingKeys.has("gdrive")}
          disabled={gdriveRunning}
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

      {gdriveMessage && (
        <p className="mt-4 text-sm text-emerald-700" role="status">
          {gdriveMessage}
        </p>
      )}
      {gdriveError && (
        <p className="mt-2 text-sm text-red-600" role="alert">
          {gdriveError}
        </p>
      )}
    </Card>
  );
}

/** @deprecated Use ConfluenceSyncControls instead */
export function AdminSyncControls() {
  return <ConfluenceSyncControls />;
}
