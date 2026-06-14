import { create } from "zustand";
import { persist } from "zustand/middleware";

export type TutorialKey = "chat" | "dashboard" | "settings" | "admin" | "response";

interface TutorialStore {
  dismissed: Partial<Record<TutorialKey, boolean>>;
  hasHydrated: boolean;
  setDismissed: (key: TutorialKey, value: boolean) => void;
  isDismissed: (key: TutorialKey) => boolean;
}

export const useTutorialStore = create<TutorialStore>()(
  persist(
    (set, get) => ({
      dismissed: {},
      hasHydrated: false,
      setDismissed: (key, value) =>
        set((s) => ({ dismissed: { ...s.dismissed, [key]: value } })),
      isDismissed: (key) => get().dismissed[key] ?? false,
    }),
    {
      name: "zalopay-knowledge-tutorial-v2",
      partialize: (state) => ({ dismissed: state.dismissed }),
      onRehydrateStorage: () => () => {
        useTutorialStore.setState({ hasHydrated: true });
      },
    },
  ),
);
