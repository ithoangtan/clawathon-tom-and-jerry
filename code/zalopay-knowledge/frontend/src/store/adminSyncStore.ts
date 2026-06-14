import { create } from "zustand";
import { normalizeAdminSyncPayload } from "@/lib/adminSyncAdapter";
import { api } from "@/lib/apiClient";
import { SCENARIO_MAP } from "@/lib/mockScenarios";
import type { ScenarioKey } from "@/lib/mockScenarios";
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

interface AdminSyncStore {
  status: AdminSyncStatus | null;
  error: string | null;
  loading: boolean;
  _timerId: ReturnType<typeof setTimeout> | null;
  _subscribers: number;
  _scenarioKey: string | null;

  refresh: () => Promise<void>;
  subscribe: (scenarioKey: string | null) => void;
  unsubscribe: () => void;
}

export const useAdminSyncStore = create<AdminSyncStore>((set, get) => ({
  status: null,
  error: null,
  loading: true,
  _timerId: null,
  _subscribers: 0,
  _scenarioKey: null,

  refresh: async () => {
    const { _scenarioKey, _subscribers } = get();

    if (IS_DEV && _scenarioKey) {
      const s = SCENARIO_MAP[_scenarioKey as ScenarioKey];
      set({ status: s.adminStatus, error: null, loading: false });
      return;
    }

    try {
      const [statusData, historyData] = await Promise.all([
        api.adminSyncStatus(),
        api.adminSyncHistory().catch(() => ({ entries: [] })),
      ]);
      const nextStatus = normalizeAdminSyncPayload(statusData, historyData.entries ?? []);
      set({ status: nextStatus, error: null, loading: false });

      // schedule next poll only if still has subscribers
      if (_subscribers > 0) {
        const delay = isAnySyncRunning(nextStatus) ? 2_000 : 30_000;
        const id = setTimeout(() => get().refresh(), delay);
        set({ _timerId: id });
      }
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : "Failed to load admin sync status",
        loading: false,
      });
      // retry after 30s on error
      if (_subscribers > 0) {
        const id = setTimeout(() => get().refresh(), 30_000);
        set({ _timerId: id });
      }
    }
  },

  subscribe: (scenarioKey) => {
    const { _subscribers } = get();
    const isFirst = _subscribers === 0;
    set({ _subscribers: _subscribers + 1, _scenarioKey: scenarioKey });
    if (isFirst) {
      get().refresh();
    }
  },

  unsubscribe: () => {
    const { _subscribers, _timerId } = get();
    const next = _subscribers - 1;
    if (next <= 0 && _timerId) {
      clearTimeout(_timerId);
      set({ _subscribers: 0, _timerId: null });
    } else {
      set({ _subscribers: Math.max(0, next) });
    }
  },
}));
