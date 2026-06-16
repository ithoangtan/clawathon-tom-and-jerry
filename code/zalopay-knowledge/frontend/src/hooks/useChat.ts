import { useCallback, useEffect, useRef, useState, type Dispatch, type SetStateAction } from "react";
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

const REVEAL_CHUNK_CHARS = 24;

/** Refusals and clarifications should render instantly — not typewriter-animated. */
function shouldRevealAnswerProgressively(response: ChatResponse): boolean {
  return response.status === "answered" || response.status === "partial";
}

function isTransportError(err: unknown): boolean {
  if (err instanceof ApiError) return false;
  if (err instanceof DOMException && err.name === "AbortError") return false;
  return true;
}

async function revealAnswerProgressively(
  assistantId: string,
  response: ChatResponse,
  setMessages: Dispatch<SetStateAction<ChatMessage[]>>,
): Promise<void> {
  const { answer } = response;
  if (!answer) {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === assistantId
          ? { ...m, content: "", response, streaming: false }
          : m,
      ),
    );
    return;
  }

  let revealed = 0;
  await new Promise<void>((resolve) => {
    const tick = () => {
      revealed = Math.min(revealed + REVEAL_CHUNK_CHARS, answer.length);
      const slice = answer.slice(0, revealed);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content: slice,
                response: { ...response, answer: slice },
                streaming: revealed < answer.length,
              }
            : m,
        ),
      );
      if (revealed < answer.length) {
        requestAnimationFrame(tick);
      } else {
        resolve();
      }
    };
    requestAnimationFrame(tick);
  });
}

function resetChatState(
  setMessages: Dispatch<SetStateAction<ChatMessage[]>>,
  setTargetDepartments: Dispatch<SetStateAction<Department[]>>,
  setTargetAutoRoute: Dispatch<SetStateAction<boolean>>,
  setError: Dispatch<SetStateAction<string | null>>,
  setLastQuestion: Dispatch<SetStateAction<string | null>>,
  setInput: Dispatch<SetStateAction<string>>,
  setPipelineProgress: Dispatch<SetStateAction<PipelineProgressState | null>>,
) {
  setMessages([]);
  setTargetDepartments([]);
  setTargetAutoRoute(true);
  setError(null);
  setLastQuestion(null);
  setInput("");
  setPipelineProgress(null);
}

export function useChat() {
  const location = useLocation();
  const chatScenarioKey = useMockStore((s) => s.chatScenario);
  const sessionId = useUserStore((s) => s.sessionId);
  const sessionAction = useSessionStore((s) => s.sessionAction);
  const saveThread = useSessionStore((s) => s.saveThread);
  const getThread = useSessionStore((s) => s.getThread);
  const clearSessionAction = useSessionStore((s) => s.clearSessionAction);
  // Subscribe to live thread changes so webhook-triggered sessions update in real-time.
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
  const hydratedSessionRef = useRef<string | null>(null);
  // Tracks how many messages were in the session when it was last loaded.
  // The save effect skips when messages haven't grown past this baseline so
  // that merely viewing a session never bumps its updatedAt.
  const loadedMessageCountRef = useRef(-1);
  const messagesRef = useRef(messages);
  const targetDepartmentsRef = useRef(targetDepartments);
  const targetAutoRouteRef = useRef(targetAutoRoute);

  messagesRef.current = messages;
  targetDepartmentsRef.current = targetDepartments;
  targetAutoRouteRef.current = targetAutoRoute;

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  // Re-sync messages from the store in two cases:
  // 1. Webhook sessions — background polling delivers new progress messages every ~3s.
  // 2. Late hydration — loadThreads completed AFTER the session switch, so the initial
  //    hydration found no thread and left messages empty; sync once the store catches up.
  useEffect(() => {
    if (!liveThread) return;
    const isWebhook = liveThread.processingStatus != null;
    const isActive = !loading;
    if (isWebhook && isActive && liveThread.messages.length > 0 && liveThread.messages.length >= messages.length) {
      // Webhook polling update.
      setMessages(liveThread.messages as ChatMessage[]);
    } else if (!isWebhook && !loading && messages.length === 0 && liveThread.messages.length > 0) {
      // Late hydration: store was empty at switch time, now populated from DB.
      setMessages(liveThread.messages as ChatMessage[]);
      loadedMessageCountRef.current = liveThread.messages.length;
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liveThread?.messages?.length, liveThread?.processingStatus]);

  useEffect(() => {
    if (hydratedSessionRef.current === sessionId) return;

    const thread = getThread(sessionId);
    if (thread) {
      setMessages(thread.messages);
      setTargetDepartmentsState(thread.targetDepartments);
      setTargetAutoRouteState(resolveTargetAutoRoute(thread));
      loadedMessageCountRef.current = thread.messages.length;
    } else if (hydratedSessionRef.current !== null) {
      resetChatState(
        setMessages,
        setTargetDepartmentsState,
        setTargetAutoRouteState,
        setError,
        setLastQuestion,
        setInput,
        setPipelineProgress,
      );
      loadedMessageCountRef.current = 0;
    }

    hydratedSessionRef.current = sessionId;
  }, [sessionId, getThread]);

  useEffect(() => {
    if (!sessionAction) return;

    abortRef.current?.abort();
    const { setSessionId, newSession } = useUserStore.getState();
    const currentSessionId = useUserStore.getState().sessionId;
    const currentMessages = messagesRef.current;
    const currentDepartments = targetDepartmentsRef.current;
    const currentAutoRoute = targetAutoRouteRef.current;

    if (!(sessionAction.type === "new" && sessionAction.skipSave)) {
      saveThread(
        currentSessionId,
        currentMessages,
        currentDepartments,
        currentAutoRoute,
      );
    }

    if (sessionAction.type === "new") {
      resetChatState(
        setMessages,
        setTargetDepartmentsState,
        setTargetAutoRouteState,
        setError,
        setLastQuestion,
        setInput,
        setPipelineProgress,
      );
      newSession();
      loadedMessageCountRef.current = 0;
      hydratedSessionRef.current = useUserStore.getState().sessionId;
    } else {
      const thread = getThread(sessionAction.sessionId);
      setSessionId(sessionAction.sessionId);
      setMessages(thread?.messages ?? []);
      setTargetDepartmentsState(thread?.targetDepartments ?? []);
      setTargetAutoRouteState(thread ? resolveTargetAutoRoute(thread) : true);
      setError(null);
      setLastQuestion(null);
      setInput("");
      setPipelineProgress(null);
      loadedMessageCountRef.current = thread?.messages?.length ?? 0;
      hydratedSessionRef.current = sessionAction.sessionId;
    }

    clearSessionAction();
  }, [sessionAction, saveThread, getThread, clearSessionAction]);

  useEffect(() => {
    if (messages.length === 0) return;
    if (messages.length <= loadedMessageCountRef.current) return;
    // Skip while the assistant is still streaming — the final setMessages (streaming: false)
    // will trigger this effect again with the complete content, giving exactly 2 PUTs per
    // exchange: one when the user message is appended, one when the response is complete.
    if (messages.some((m) => m.streaming)) return;
    saveThread(sessionId, messages, targetDepartments, targetAutoRoute);
  }, [messages, targetDepartments, targetAutoRoute, sessionId, saveThread]);

  const appendAssistant = useCallback(
    async (response: ChatResponse, assistantId: string, progressive: boolean) => {
      const timestamp = new Date().toISOString();
      const base: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: progressive ? "" : response.answer,
        timestamp,
        response: progressive ? { ...response, answer: "" } : response,
        streaming: progressive,
      };

      setMessages((prev) => [...prev, base]);

      if (progressive) {
        await revealAnswerProgressively(assistantId, response, setMessages);
      }
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
        await appendAssistant(
          mockScenario.response,
          assistantId,
          shouldRevealAnswerProgressively(mockScenario.response),
        );
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
        let streamingStarted = false;
        let streamedText = "";

        for await (const event of chatStream(body, ctx, {
          signal: controller.signal,
        })) {
          if (event.event === "text") {
            const chunk = typeof event.data.chunk === "string" ? event.data.chunk : "";
            if (!chunk) continue;
            streamedText += chunk;

            if (!streamingStarted) {
              streamingStarted = true;
              setLoading(false);
              const timestamp = new Date().toISOString();
              setMessages((prev) => [
                ...prev,
                {
                  id: assistantId,
                  role: "assistant" as const,
                  content: streamedText,
                  timestamp,
                  streaming: true,
                  response: {
                    answer: streamedText,
                    citations: [],
                    source_departments: [],
                    confidence: 1,
                    feedback_id: "",
                    status: "answered" as const,
                    conflicts: [],
                    clarifying_question: null,
                    refusal_reason: null,
                    refusals: [],
                    model_used: null,
                  },
                },
              ]);
            } else {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? {
                        ...m,
                        content: streamedText,
                        response: m.response
                          ? { ...m.response, answer: streamedText }
                          : undefined,
                      }
                    : m,
                ),
              );
            }
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
          if (streamingStarted) {
            setMessages((prev) => prev.filter((m) => m.id !== assistantId));
          }
          return;
        }

        if (finalResponse) {
          if (streamingStarted) {
            // Enrich existing streaming message with full metadata
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? {
                      ...m,
                      content: finalResponse!.answer || streamedText,
                      response: finalResponse!,
                      streaming: false,
                    }
                  : m,
              ),
            );
          } else {
            // No text was streamed (refusal / clarify) — use normal append
            setLoading(false);
            await appendAssistant(
              finalResponse,
              assistantId,
              shouldRevealAnswerProgressively(finalResponse),
            );
          }
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
          await appendAssistant(response, assistantId, false);
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
