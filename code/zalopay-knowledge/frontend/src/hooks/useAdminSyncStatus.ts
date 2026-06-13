import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/apiClient";
import type { AdminSyncStatus } from "@/lib/types";

export function useAdminSyncStatus() {
  const [status, setStatus] = useState<AdminSyncStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const data = await api.adminSyncStatus();
      setStatus(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load admin sync status");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    const isRunning = status?.running || status?.sources.some((s) => s.state === "running");
    const interval = isRunning ? 2000 : 30_000;
    const id = setInterval(refresh, interval);
    return () => clearInterval(id);
  }, [status, refresh]);

  return { status, error, loading, refresh };
}
