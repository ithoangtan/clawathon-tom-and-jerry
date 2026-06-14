import { useEffect } from "react";
import { useShallow } from "zustand/react/shallow";
import { useAdminSyncStore } from "@/store/adminSyncStore";
import { useMockStore } from "@/store/mockStore";

export function useAdminSyncStatus() {
  const scenarioKey = useMockStore((s) => s.syncScenario);
  const { subscribe, unsubscribe, status, error, loading, refresh } =
    useAdminSyncStore(
      useShallow((s) => ({
        subscribe: s.subscribe,
        unsubscribe: s.unsubscribe,
        status: s.status,
        error: s.error,
        loading: s.loading,
        refresh: s.refresh,
      })),
    );

  useEffect(() => {
    subscribe(scenarioKey ?? null);
    return () => unsubscribe();
  }, [scenarioKey, subscribe, unsubscribe]);

  return { status, error, loading, refresh };
}
