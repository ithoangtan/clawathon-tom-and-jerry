import { create } from "zustand";
import type { ChatMessage } from "@/hooks/useChat";
import { api } from "@/lib/apiClient";
import {
  buildThread,
  sortThreads,
  type SessionThread,
} from "@/lib/sessionThread";
import type { Department } from "@/lib/types";

export type SessionAction =
  | { type: "new"; skipSave?: boolean }
  | { type: "switch"; sessionId: string };

interface SessionStore {
  threads: Record<string, SessionThread>;
  sessionAction: SessionAction | null;
  loaded: boolean;
  loadThreads: () => Promise<void>;
  saveThread: (
    sessionId: string,
    messages: ChatMessage[],
    targetDepartments: Department[],
    targetAutoRoute: boolean,
  ) => void;
  deleteThread: (sessionId: string) => void;
  getThread: (sessionId: string) => SessionThread | undefined;
  listThreads: () => SessionThread[];
  requestNewSession: (skipSave?: boolean) => void;
  requestSwitchSession: (sessionId: string) => void;
  clearSessionAction: () => void;
}

export const useSessionStore = create<SessionStore>()((set, get) => ({
  threads: {},
  sessionAction: null,
  loaded: false,

  loadThreads: async () => {
    try {
      const { threads } = await api.listSessions();
      const record: Record<string, SessionThread> = {};
      for (const t of threads as SessionThread[]) {
        record[t.sessionId] = t;
      }
      set({ threads: record, loaded: true });
    } catch {
      set({ loaded: true });
    }
  },

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

    api.upsertSession(sessionId, thread).catch(() => {/* best-effort */});
  },

  deleteThread: (sessionId) => {
    set((state) => {
      const { [sessionId]: _removed, ...rest } = state.threads;
      return { threads: rest };
    });
    api.deleteSession(sessionId).catch(() => {/* best-effort */});
  },

  getThread: (sessionId) => get().threads[sessionId],

  listThreads: () => sortThreads(Object.values(get().threads)),

  requestNewSession: (skipSave) => set({ sessionAction: { type: "new", skipSave } }),

  requestSwitchSession: (sessionId) =>
    set({ sessionAction: { type: "switch", sessionId } }),

  clearSessionAction: () => set({ sessionAction: null }),
}));
