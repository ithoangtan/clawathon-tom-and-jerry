import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/apiClient";
import type { SyncStatus } from "@/lib/types";

export function useSyncStatus() {
  const [status, setStatus] = useState<SyncStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const data = await api.syncStatus();
      setStatus(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load sync status");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    const isRunning = status?.sources.some((s) => s.state === "running");
    const interval = isRunning ? 2000 : 30_000;
    const id = setInterval(refresh, interval);
    return () => clearInterval(id);
  }, [status, refresh]);

  return { status, error, loading, refresh };
}
