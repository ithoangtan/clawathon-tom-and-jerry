import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/apiClient";
import { MOCK_DASHBOARD } from "@/lib/mockDashboard";
import { SCENARIO_MAP } from "@/lib/mockScenarios";
import { useMockStore } from "@/store/mockStore";
import type { DashboardData } from "@/lib/types";

const IS_DEV = import.meta.env.DEV || window.location.hostname === "localhost";

export function useDashboard(pollMs = 30_000) {
  const scenarioKey = useMockStore((s) => s.syncScenario);

  const [data, setData] = useState<DashboardData | null>(() => {
    if (IS_DEV && scenarioKey) return SCENARIO_MAP[scenarioKey].dashboard;
    return null;
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (IS_DEV && scenarioKey) {
      setData(SCENARIO_MAP[scenarioKey].dashboard);
      setLoading(false);
      return;
    }
    try {
      const result = await api.dashboard();
      setData(result);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }, [scenarioKey]);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, pollMs);
    return () => clearInterval(id);
  }, [refresh, pollMs]);

  return { data, error, loading, refresh };
}
