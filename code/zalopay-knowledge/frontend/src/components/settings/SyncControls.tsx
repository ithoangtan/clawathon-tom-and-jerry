import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { api, ApiError } from "@/lib/apiClient";
import { t } from "@/lib/i18n";
import { getUserContext, useUserStore } from "@/store/userStore";
import { useHealth } from "@/hooks/useHealth";
import { useSyncStatus } from "@/hooks/useSyncStatus";
import { useEffect, useRef, useState } from "react";

export function SyncControls() {
  const locale = useUserStore((s) => s.locale);
  const { refresh, status } = useSyncStatus();
  const { refresh: refreshHealth } = useHealth();
  const [loadingSource, setLoadingSource] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wasRunningRef = useRef(false);

  const confluenceRunning = status?.sources.find((s) => s.source === "confluence")?.state === "running";
  const gdriveRunning = status?.sources.find((s) => s.source === "gdrive")?.state === "running";
  const anyRunning = Boolean(confluenceRunning || gdriveRunning);

  useEffect(() => {
    if (wasRunningRef.current && !anyRunning) {
      refreshHealth();
    }
    wasRunningRef.current = anyRunning;
  }, [anyRunning, refreshHealth]);

  async function trigger(source: "confluence" | "gdrive") {
    setLoadingSource(source);
    setMessage(null);
    setError(null);
    try {
      const res =
        source === "confluence"
          ? await api.syncConfluence(getUserContext())
          : await api.syncGdrive(getUserContext());
      setMessage(res.message);
      if (!res.started) {
        setError("Sync already in progress");
      }
      refresh();
      refreshHealth();
    } catch (e) {
      setError(e instanceof ApiError ? e.detail ?? e.message : "Sync failed");
    } finally {
      setLoadingSource(null);
    }
  }

  return (
    <Card>
      <h3 className="font-semibold text-slate-800 mb-4">{t("syncControls", locale)}</h3>
      <div className="flex flex-wrap gap-3">
        <Button
          variant="secondary"
          loading={loadingSource === "confluence"}
          disabled={confluenceRunning}
          onClick={() => trigger("confluence")}
        >
          {confluenceRunning ? t("syncing", locale) : t("syncConfluence", locale)}
        </Button>
        <Button
          variant="secondary"
          loading={loadingSource === "gdrive"}
          disabled={gdriveRunning}
          onClick={() => trigger("gdrive")}
        >
          {gdriveRunning ? t("syncing", locale) : t("syncGdrive", locale)}
        </Button>
      </div>
      {message && (
        <p className="mt-3 text-sm text-emerald-700" role="status">
          {message}
        </p>
      )}
      {error && (
        <p className="mt-3 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </Card>
  );
}
