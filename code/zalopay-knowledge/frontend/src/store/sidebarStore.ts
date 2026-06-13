import { create } from "zustand";
import { persist } from "zustand/middleware";

interface SidebarStore {
  open: boolean;
  setOpen: (open: boolean) => void;
  toggle: () => void;
}

export const useSidebarStore = create<SidebarStore>()(
  persist(
    (set) => ({
      open: false,
      setOpen: (open) => set({ open }),
      toggle: () => set((state) => ({ open: !state.open })),
    }),
    { name: "zalopay-knowledge-sidebar" },
  ),
);
