import { useCallback, useEffect, useState } from "react";
import { normalizeAdminSyncPayload } from "@/lib/adminSyncAdapter";
import { api } from "@/lib/apiClient";
import { SCENARIO_MAP } from "@/lib/mockScenarios";
import { useMockStore } from "@/store/mockStore";
import type { AdminSyncStatus } from "@/lib/types";

const IS_DEV = import.meta.env.DEV || window.location.hostname === "localhost";

function isAnySyncRunning(status: AdminSyncStatus | null): boolean {
  if (!status) return false;
  return (
    status.running ||
    status.sources.some((s) => s.state === "running") ||
    status.departments.some((d) => d.state === "running")
  );
}

export function useAdminSyncStatus() {
  const scenarioKey = useMockStore((s) => s.scenario);
  const scenario = IS_DEV && scenarioKey ? SCENARIO_MAP[scenarioKey] : null;

  const [status, setStatus] = useState<AdminSyncStatus | null>(
    scenario ? scenario.adminStatus : null,
  );
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(!scenario);

  const refresh = useCallback(async () => {
    if (IS_DEV && scenarioKey) {
      const s = SCENARIO_MAP[scenarioKey];
      setStatus(s.adminStatus);
      setError(null);
      setLoading(false);
      return;
    }
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
  }, [scenarioKey]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (IS_DEV && scenarioKey) return;
    const interval = isAnySyncRunning(status) ? 2000 : 30_000;
    const id = setInterval(refresh, interval);
    return () => clearInterval(id);
  }, [status, refresh, scenarioKey]);

  return { status, error, loading, refresh };
}
