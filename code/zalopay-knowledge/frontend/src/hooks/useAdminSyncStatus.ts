import { useCallback, useEffect, useState } from "react";
import { normalizeAdminSyncPayload } from "@/lib/adminSyncAdapter";
import { api } from "@/lib/apiClient";
import type { AdminSyncStatus } from "@/lib/types";

function isAnySyncRunning(status: AdminSyncStatus | null): boolean {
  if (!status) return false;
  return (
    status.running ||
    status.sources.some((s) => s.state === "running") ||
    status.departments.some((d) => d.state === "running")
  );
}

export function useAdminSyncStatus() {
  const [status, setStatus] = useState<AdminSyncStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [statusData, historyData] = await Promise.all([
        api.adminSyncStatus(),
        api.adminSyncHistory().catch(() => ({ entries: [] })),
      ]);
      setStatus(
        normalizeAdminSyncPayload(statusData, historyData.entries ?? []),
      );
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
    const interval = isAnySyncRunning(status) ? 2000 : 30_000;
    const id = setInterval(refresh, interval);
    return () => clearInterval(id);
  }, [status, refresh]);

  return { status, error, loading, refresh };
}
