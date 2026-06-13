import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ScenarioKey } from "@/lib/mockScenarios";

interface MockStore {
  scenario: ScenarioKey | null;
  setScenario: (s: ScenarioKey | null) => void;
}

export const useMockStore = create<MockStore>()(
  persist(
    (set) => ({
      scenario: null,
      setScenario: (scenario) => set({ scenario }),
    }),
    { name: "zp-dev-mock-scenario" },
  ),
);
