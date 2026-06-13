import { create } from "zustand";
import { persist } from "zustand/middleware";
import { generateSessionId, generateUserId } from "@/lib/format";
import type { Department, Lang, Role, UserContext } from "@/lib/types";

interface UserStore extends UserContext {
  setUserId: (userId: string) => void;
  setRole: (role: Role) => void;
  setHomeDept: (homeDept: Department) => void;
  setLocale: (locale: Lang) => void;
  newSession: () => void;
  update: (partial: Partial<UserContext>) => void;
}

const defaultState: UserContext = {
  userId: generateUserId(),
  sessionId: generateSessionId(),
  role: "business",
  homeDept: "risk",
  locale: "en",
};

export const useUserStore = create<UserStore>()(
  persist(
    (set) => ({
      ...defaultState,
      setUserId: (userId) => set({ userId }),
      setRole: (role) => set({ role }),
      setHomeDept: (homeDept) => set({ homeDept }),
      setLocale: (locale) => set({ locale }),
      newSession: () => set({ sessionId: generateSessionId() }),
      update: (partial) => set(partial),
    }),
    {
      name: "zalopay-knowledge-user",
      partialize: (state) => ({
        userId: state.userId,
        sessionId: state.sessionId,
        role: state.role,
        homeDept: state.homeDept,
        locale: state.locale,
      }),
    },
  ),
);

export function getUserContext(): UserContext {
  const { userId, sessionId, role, homeDept, locale } = useUserStore.getState();
  return { userId, sessionId, role, homeDept, locale };
}
