import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/apiClient";
import { MOCK_DASHBOARD } from "@/lib/mockDashboard";
import type { DashboardData } from "@/lib/types";

const IS_DEV = import.meta.env.DEV || window.location.hostname === "localhost";

export function useDashboard(pollMs = 30_000) {
  const [data, setData] = useState<DashboardData | null>(IS_DEV ? MOCK_DASHBOARD : null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(!IS_DEV);

  const refresh = useCallback(async () => {
    if (IS_DEV) {
      setData(MOCK_DASHBOARD);
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
  }, []);

  useEffect(() => {
    if (IS_DEV) return;
    refresh();
    const id = setInterval(refresh, pollMs);
    return () => clearInterval(id);
  }, [refresh, pollMs]);

  return { data, error, loading, refresh };
}
