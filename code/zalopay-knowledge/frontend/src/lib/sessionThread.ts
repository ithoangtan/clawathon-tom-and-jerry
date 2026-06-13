import type { ChatMessage } from "@/hooks/useChat";
import type { Department } from "@/lib/types";

export interface SessionThread {
  sessionId: string;
  /** Display title derived from the first submitted user prompt. */
  title?: string;
  messages: ChatMessage[];
  targetDepartments: Department[];
  /** When true (default), Agent Center auto-routes; when false, pinned departments apply. */
  targetAutoRoute?: boolean;
  createdAt: string;
  updatedAt: string;
}

export type ThreadStatus = "answered" | "refused" | "conflict" | "pending";

export function firstUserQuestion(messages: ChatMessage[]): string | null {
  const first = messages.find((m) => m.role === "user");
  return first?.content.trim() || null;
}

export function previewText(text: string, maxLen = 72): string {
  const trimmed = text.trim();
  if (trimmed.length <= maxLen) return trimmed;
  return `${trimmed.slice(0, maxLen - 1)}…`;
}

/** First sentence or line from a submitted prompt, trimmed for sidebar display. */
export function deriveSessionTitle(prompt: string, maxLen = 72): string {
  const trimmed = prompt.trim();
  if (!trimmed) return "";

  const firstLine = trimmed.split(/\n+/)[0]?.trim() ?? trimmed;
  const sentenceEnd = firstLine.search(/[.!?。！？](?:\s|$)/);
  const firstIdea =
    sentenceEnd >= 0 ? firstLine.slice(0, sentenceEnd + 1).trim() : firstLine;

  return previewText(firstIdea, maxLen);
}

export function threadTitle(thread: SessionThread): string | null {
  if (thread.title) return thread.title;
  const question = firstUserQuestion(thread.messages);
  return question ? deriveSessionTitle(question) : null;
}

export function threadDepartments(thread: SessionThread): Department[] {
  const fromResponse = [...thread.messages]
    .reverse()
    .find((m) => m.role === "assistant" && m.response)?.response?.source_departments;

  if (fromResponse && fromResponse.length > 0) return fromResponse;
  return thread.targetDepartments;
}

export function threadStatus(thread: SessionThread): ThreadStatus {
  const lastAssistant = [...thread.messages]
    .reverse()
    .find((m) => m.role === "assistant" && m.response);

  if (!lastAssistant?.response) return "pending";

  if (lastAssistant.response.conflicts && lastAssistant.response.conflicts.length > 0) {
    return "conflict";
  }

  if (lastAssistant.response.status === "refused") return "refused";
  return "answered";
}

export function buildThread(
  sessionId: string,
  messages: ChatMessage[],
  targetDepartments: Department[],
  targetAutoRoute: boolean,
  existing?: SessionThread,
): SessionThread | null {
  if (messages.length === 0) return null;

  const now = new Date().toISOString();
  const firstPrompt = firstUserQuestion(messages);
  const title =
    existing?.title ??
    (firstPrompt ? deriveSessionTitle(firstPrompt) : undefined);

  return {
    sessionId,
    title,
    messages,
    targetDepartments,
    targetAutoRoute,
    createdAt: existing?.createdAt ?? now,
    updatedAt: now,
  };
}

/** Restores auto-route flag for threads saved before targetAutoRoute existed. */
export function resolveTargetAutoRoute(thread: SessionThread): boolean {
  if (thread.targetAutoRoute !== undefined) return thread.targetAutoRoute;
  return thread.targetDepartments.length === 0;
}

export function matchesSearch(thread: SessionThread, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;

  const title = threadTitle(thread);
  if (title?.toLowerCase().includes(q)) return true;

  return thread.messages.some((m) => m.content.toLowerCase().includes(q));
}

export function sortThreads(threads: SessionThread[]): SessionThread[] {
  return [...threads].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
  );
}
