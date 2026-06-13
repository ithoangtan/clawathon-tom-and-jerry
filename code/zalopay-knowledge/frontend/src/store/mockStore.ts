import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ChatScenarioKey, ScenarioKey } from "@/lib/mockScenarios";

interface MockStore {
  /** Active scenario for /dashboard and /admin pages */
  syncScenario: ScenarioKey | null;
  /** Active scenario for / (Chat) page */
  chatScenario: ChatScenarioKey | null;
  setSyncScenario: (s: ScenarioKey | null) => void;
  setChatScenario: (s: ChatScenarioKey | null) => void;
}

export const useMockStore = create<MockStore>()(
  persist(
    (set) => ({
      syncScenario: null,
      chatScenario: null,
      setSyncScenario: (syncScenario) => set({ syncScenario }),
      setChatScenario: (chatScenario) => set({ chatScenario }),
    }),
    { name: "zp-dev-mock-scenario" },
  ),
);
