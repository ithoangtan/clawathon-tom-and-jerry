import { useCallback, useEffect, useRef, useState, type Dispatch, type SetStateAction } from "react";
import { api, ApiError, chatStream } from "@/lib/apiClient";
import { getUserContext } from "@/store/userStore";
import type { ChatResponse, Department } from "@/lib/types";

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

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [targetDepartments, setTargetDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(false);
  const [streamingStatus, setStreamingStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

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

      const depts = overrideDepts ?? targetDepartments;
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
      setError(null);
      setLastQuestion(trimmed);

      const body = {
        question: trimmed,
        target_departments: depts.length > 0 ? depts : null,
      };
      const ctx = getUserContext();
      const assistantId = `assistant-${Date.now()}`;

      try {
        let finalResponse: ChatResponse | null = null;
        let streamError: string | null = null;

        for await (const event of chatStream(body, ctx, {
          signal: controller.signal,
        })) {
          if (event.event === "node") {
            const node = event.data.node;
            if (typeof node === "string") {
              setStreamingStatus(node);
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
          return;
        }

        if (finalResponse) {
          setLoading(false);
          setStreamingStatus(null);
          await appendAssistant(finalResponse, assistantId, true);
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
    [loading, targetDepartments, appendAssistant],
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

  return {
    messages,
    input,
    setInput,
    targetDepartments,
    setTargetDepartments,
    loading,
    streamingStatus,
    error,
    sendMessage,
    retryLast,
  };
}
