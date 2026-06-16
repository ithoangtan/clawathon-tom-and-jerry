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
  _pollTimer: ReturnType<typeof setInterval> | null;
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
  startPolling: () => void;
  stopPolling: () => void;
}

export const useSessionStore = create<SessionStore>()((set, get) => ({
  threads: {},
  sessionAction: null,
  loaded: false,
  _pollTimer: null,

  loadThreads: async () => {
    try {
      const { threads } = await api.listSessions();
      const record: Record<string, SessionThread> = {};
      for (const t of threads as SessionThread[]) {
        record[t.sessionId] = t;
      }
      set({ threads: record, loaded: true });
      // Auto-start polling if any session is currently processing.
      const hasProcessing = Object.values(record).some(
        (t) => t.processingStatus === "processing",
      );
      if (hasProcessing) get().startPolling();
    } catch {
      set({ loaded: true });
    }
  },

  startPolling: () => {
    if (get()._pollTimer) return; // already polling
    const timer = setInterval(async () => {
      try {
        const { threads } = await api.listSessions();
        const record: Record<string, SessionThread> = {};
        for (const t of threads as SessionThread[]) {
          record[t.sessionId] = t;
        }
        set({ threads: record });
        // Stop polling when nothing is processing anymore.
        const stillProcessing = Object.values(record).some(
          (t) => t.processingStatus === "processing",
        );
        if (!stillProcessing) get().stopPolling();
      } catch {
        // ignore transient errors
      }
    }, 3000);
    set({ _pollTimer: timer });
  },

  stopPolling: () => {
    const timer = get()._pollTimer;
    if (timer) clearInterval(timer);
    set({ _pollTimer: null });
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
