import { create } from "zustand";
import { persist } from "zustand/middleware";

interface TutorialStore {
  dismissed: boolean;
  hasHydrated: boolean;
  setDismissed: (dismissed: boolean) => void;
}

export const useTutorialStore = create<TutorialStore>()(
  persist(
    (set) => ({
      dismissed: false,
      hasHydrated: false,
      setDismissed: (dismissed) => set({ dismissed }),
    }),
    {
      name: "zalopay-knowledge-tutorial",
      partialize: (state) => ({ dismissed: state.dismissed }),
      onRehydrateStorage: () => () => {
        useTutorialStore.setState({ hasHydrated: true });
      },
    },
  ),
);
