import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { api, ApiError, chatStream } from "@/lib/apiClient";
import {
  hidePipeline,
  type PipelineProgressState,
} from "@/lib/pipelineSteps";
import { CHAT_SCENARIO_MAP } from "@/lib/mockScenarios";
import { getUserContext, useUserStore } from "@/store/userStore";
import { resolveTargetAutoRoute } from "@/lib/sessionThread";
import { useSessionStore } from "@/store/sessionStore";
import { useMockStore } from "@/store/mockStore";
import type { ChatResponse, Department } from "@/lib/types";

const IS_DEV = import.meta.env.DEV || window.location.hostname === "localhost";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  /** ISO-8601 client timestamp when the message was created. */
  timestamp: string;
  response?: ChatResponse;
  /** True while the answer text is being revealed after a stream `done` event. */
  streaming?: boolean;
}

function isTransportError(err: unknown): boolean {
  if (err instanceof ApiError) return false;
  if (err instanceof DOMException && err.name === "AbortError") return false;
  return true;
}


export function useChat() {
  const location = useLocation();
  const chatScenarioKey = useMockStore((s) => s.chatScenario);
  const sessionId = useUserStore((s) => s.sessionId);
  const sessionAction = useSessionStore((s) => s.sessionAction);
  const saveThread = useSessionStore((s) => s.saveThread);
  const clearSessionAction = useSessionStore((s) => s.clearSessionAction);
  const liveThread = useSessionStore((s) => s.threads[sessionId]);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [targetDepartments, setTargetDepartmentsState] = useState<Department[]>([]);
  const [targetAutoRoute, setTargetAutoRouteState] = useState(true);
  const [loading, setLoading] = useState(false);
  const [streamingStatus, setStreamingStatus] = useState<string | null>(null);
  const [pipelineProgress, setPipelineProgress] = useState<PipelineProgressState | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  // Message count at the last save (or session load). Prevents re-saving when just viewing.
  const lastSavedCountRef = useRef(0);
  const messagesRef = useRef(messages);
  const targetDepartmentsRef = useRef(targetDepartments);
  const targetAutoRouteRef = useRef(targetAutoRoute);
  // Always-current sessionId ref — lets Effect 4 read sessionId without it being a dep.
  // This prevents Effect 4 from firing when only sessionId changes (which would save stale
  // messages from the previous session into the newly created one).
  const sessionIdRef = useRef(sessionId);

  messagesRef.current = messages;
  targetDepartmentsRef.current = targetDepartments;
  targetAutoRouteRef.current = targetAutoRoute;
  sessionIdRef.current = sessionId;

  // Abort in-flight requests on unmount.
  useEffect(() => {
    return () => { abortRef.current?.abort(); };
  }, []);

  // ── Effect 1: Hydrate UI whenever the active session changes ──────────────
  // Runs on mount and every time sessionId changes (new session or switch).
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    const thread = useSessionStore.getState().getThread(sessionId);
    setLoading(false);
    setStreamingStatus(null);
    setError(null);
    setLastQuestion(null);
    setInput("");
    setPipelineProgress(null);
    if (thread) {
      setMessages(thread.messages as ChatMessage[]);
      setTargetDepartmentsState(thread.targetDepartments);
      setTargetAutoRouteState(resolveTargetAutoRoute(thread));
      lastSavedCountRef.current = thread.messages.length;
    } else {
      setMessages([]);
      setTargetDepartmentsState([]);
      setTargetAutoRouteState(true);
      lastSavedCountRef.current = 0;
    }
  }, [sessionId]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Effect 2: Late-hydration + webhook sync ───────────────────────────────
  // Two cases where we need to sync from the live store entry:
  // a) loadThreads completed after the hydration above ran (page refresh race).
  // b) Webhook sessions: polling pushes new messages every ~3s.
  useEffect(() => {
    if (!liveThread || loading) return;
    if (liveThread.processingStatus != null) {
      // Webhook: accept any update that is at least as long as what we have.
      if (liveThread.messages.length > 0 && liveThread.messages.length >= messages.length) {
        setMessages(liveThread.messages as ChatMessage[]);
      }
    } else if (messages.length === 0 && liveThread.messages.length > 0) {
      // Late-hydration: store was empty when Effect 1 ran, now populated.
      setMessages(liveThread.messages as ChatMessage[]);
      lastSavedCountRef.current = liveThread.messages.length;
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liveThread?.messages?.length, liveThread?.processingStatus]);

  // ── Effect 3: Handle session switch (existing sessions from sidebar click) ──
  useEffect(() => {
    if (!sessionAction) return;
    abortRef.current?.abort();
    if (!sessionAction.skipSave) {
      saveThread(
        useUserStore.getState().sessionId,
        messagesRef.current,
        targetDepartmentsRef.current,
        targetAutoRouteRef.current,
      );
    }
    useUserStore.getState().setSessionId(sessionAction.sessionId);
    clearSessionAction();
  }, [sessionAction, saveThread, clearSessionAction]);

  // ── Effect 4: Save after each complete exchange ───────────────────────────
  // Fires only when the last message is a fully-revealed assistant response.
  // This gives exactly 1 PUT per exchange (not 2).
  // sessionId is intentionally read via ref (not in deps): including it as a dep caused
  // Effect 4 to run when newSession() changed sessionId while messages still held the
  // previous session's data, creating a phantom history entry with the wrong title.
  useEffect(() => {
    if (messages.length === 0) return;
    const last = messages[messages.length - 1];
    if (!last || last.role !== "assistant" || last.streaming) return;
    if (messages.length <= lastSavedCountRef.current) return;
    lastSavedCountRef.current = messages.length;
    saveThread(sessionIdRef.current, messages, targetDepartments, targetAutoRoute);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages, targetDepartments, targetAutoRoute, saveThread]);

  const appendAssistant = useCallback(
    (response: ChatResponse, assistantId: string) => {
      const timestamp = new Date().toISOString();
      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          role: "assistant" as const,
          content: response.answer ?? "",
          timestamp,
          response,
          streaming: false,
        },
      ]);
    },
    [],
  );

  const sendMessage = useCallback(
    async (question: string, overrideDepts?: Department[]) => {
      const trimmed = question.trim();
      if (!trimmed || loading) return;

      if (location.pathname === "/") {
        // Use replaceState instead of navigate() to avoid React Router unmounting
        // this component (which would abort the in-flight stream and lose the session).
        window.history.replaceState(null, "", `/chat/${sessionId}`);
      }

      const now = new Date().toISOString();
      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: trimmed,
        timestamp: now,
      };

      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setMessages((prev) => [...prev, userMsg]);
      // Optimistically register the session in the sidebar immediately (like ChatGPT/Claude).
      useSessionStore.getState().registerSessionOptimistic(
        sessionId,
        [...messagesRef.current, userMsg],
        targetDepartmentsRef.current,
        targetAutoRouteRef.current,
      );
      setInput("");
      setLoading(true);
      setStreamingStatus(null);
      setPipelineProgress(null);
      setError(null);
      setLastQuestion(trimmed);

      // ── Mock branch (dev only) ────────────────────────────────────────────
      if (IS_DEV && chatScenarioKey) {
        const mockScenario = CHAT_SCENARIO_MAP[chatScenarioKey];
        setStreamingStatus("Đang xử lý (mock)…");
        await new Promise((r) => setTimeout(r, mockScenario.delayMs));
        if (controller.signal.aborted) return;
        setLoading(false);
        setStreamingStatus(null);
        if (!mockScenario.response) {
          setError(mockScenario.error ?? "Mock error");
          return;
        }
        const assistantId = `assistant-${Date.now()}`;
        appendAssistant(mockScenario.response, assistantId);
        return;
      }
      // ─────────────────────────────────────────────────────────────────────

      const depts = overrideDepts ?? targetDepartments;
      const useAutoRoute = overrideDepts === undefined ? targetAutoRoute : false;

      const body = {
        question: trimmed,
        target_departments: !useAutoRoute && depts.length > 0 ? depts : null,
      };
      const ctx = getUserContext();
      const assistantId = `assistant-${Date.now()}`;

      try {
        let finalResponse: ChatResponse | null = null;
        let streamError: string | null = null;
        let streamedText = "";

        for await (const event of chatStream(body, ctx, {
          signal: controller.signal,
        })) {
          if (event.event === "text") {
            // Accumulate silently — show full answer at once when done.
            const chunk = typeof event.data.chunk === "string" ? event.data.chunk : "";
            if (chunk) streamedText += chunk;
          } else if (event.event === "error") {
            streamError =
              typeof event.data.detail === "string"
                ? event.data.detail
                : "Stream failed";
            break;
          } else if (event.event === "done") {
            finalResponse = event.data as unknown as ChatResponse;
          }
        }

        if (streamError) {
          setError(streamError);
          return;
        }

        if (finalResponse) {
          setLoading(false);
          appendAssistant(
            { ...finalResponse, answer: finalResponse.answer || streamedText },
            assistantId,
          );
          return;
        }

        throw new Error("Stream ended without a response");
      } catch (streamErr) {
        if (controller.signal.aborted) return;

        if (!isTransportError(streamErr)) {
          const message =
            streamErr instanceof ApiError
              ? streamErr.detail ?? streamErr.message
              : "Request failed";
          setError(message);
          return;
        }

        try {
          const response = await api.chat(body, ctx);
          setLoading(false);
          setStreamingStatus(null);
          appendAssistant(response, assistantId);
        } catch (e) {
          const message =
            e instanceof ApiError ? e.detail ?? e.message : "Request failed";
          setError(message);
        }
      } finally {
        setLoading(false);
        setStreamingStatus(null);
      }
    },
    [loading, targetDepartments, targetAutoRoute, appendAssistant, chatScenarioKey, location.pathname, sessionId],
  );

  const retryLast = useCallback(() => {
    if (lastQuestion) {
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last?.role === "user") {
          return prev.slice(0, -1);
        }
        return prev.slice(0, -2);
      });
      setError(null);
      if (lastQuestion) sendMessage(lastQuestion);
    }
  }, [lastQuestion, sendMessage]);

  const dismissPipelineSummary = useCallback(() => {
    setPipelineProgress((prev) => (prev ? hidePipeline(prev) : null));
  }, []);

  const setTargetDepartments = useCallback((departments: Department[]) => {
    setTargetDepartmentsState(departments);
    if (departments.length > 0) {
      setTargetAutoRouteState(false);
    }
  }, []);

  const setTargetAutoRoute = useCallback((autoRoute: boolean) => {
    setTargetAutoRouteState(autoRoute);
    if (autoRoute) {
      setTargetDepartmentsState([]);
    }
  }, []);

  return {
    messages,
    input,
    setInput,
    targetDepartments,
    setTargetDepartments,
    targetAutoRoute,
    setTargetAutoRoute,
    loading,
    streamingStatus,
    pipelineProgress,
    dismissPipelineSummary,
    error,
    sendMessage,
    retryLast,
  };
}
