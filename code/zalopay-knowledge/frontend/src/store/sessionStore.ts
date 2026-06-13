import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ChatMessage } from "@/hooks/useChat";
import {
  buildThread,
  sortThreads,
  type SessionThread,
} from "@/lib/sessionThread";
import type { Department } from "@/lib/types";

export type SessionAction =
  | { type: "new" }
  | { type: "switch"; sessionId: string };

interface SessionStore {
  threads: Record<string, SessionThread>;
  sessionAction: SessionAction | null;
  saveThread: (
    sessionId: string,
    messages: ChatMessage[],
    targetDepartments: Department[],
    targetAutoRoute: boolean,
  ) => void;
  deleteThread: (sessionId: string) => void;
  getThread: (sessionId: string) => SessionThread | undefined;
  listThreads: () => SessionThread[];
  requestNewSession: () => void;
  requestSwitchSession: (sessionId: string) => void;
  clearSessionAction: () => void;
}

export const useSessionStore = create<SessionStore>()(
  persist(
    (set, get) => ({
      threads: {},
      sessionAction: null,

      saveThread: (sessionId, messages, targetDepartments, targetAutoRoute) => {
        const existing = get().threads[sessionId];
        const thread = buildThread(
          sessionId,
          messages,
          targetDepartments,
          targetAutoRoute,
          existing,
        );
        if (!thread) return;

        set((state) => ({
          threads: { ...state.threads, [sessionId]: thread },
        }));
      },

      deleteThread: (sessionId) => {
        set((state) => {
          const { [sessionId]: _removed, ...rest } = state.threads;
          return { threads: rest };
        });
      },

      getThread: (sessionId) => get().threads[sessionId],

      listThreads: () => sortThreads(Object.values(get().threads)),

      requestNewSession: () => set({ sessionAction: { type: "new" } }),

      requestSwitchSession: (sessionId) =>
        set({ sessionAction: { type: "switch", sessionId } }),

      clearSessionAction: () => set({ sessionAction: null }),
    }),
    {
      name: "zalopay-knowledge-sessions",
      partialize: (state) => ({ threads: state.threads }),
    },
  ),
);
