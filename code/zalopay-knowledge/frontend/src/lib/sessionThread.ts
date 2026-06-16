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
  /** Workflow ID when this session was created by a webhook-triggered workflow run. */
  workflowId?: string | null;
  /** Jira issue key associated with this session (webhook-triggered runs). */
  jiraKey?: string | null;
  /** Processing state for webhook-triggered sessions: "processing" | "done" | "error" | null. */
  processingStatus?: string | null;
}

export type ThreadStatus = "answered" | "refused" | "conflict" | "pending";

export function firstUserQuestion(messages: ChatMessage[]): string | null {
  const first = messages.find((m) => m.role === "user");
  return first?.content.trim() || null;
}

/** Common Vietnamese/English filler openers that add no meaning to a title. */
const FILLER_OPENER = /^(?:(?:bạn\s+)?(?:hãy\s+)?(?:cho\s+(?:tôi|mình)\s+biết|giải\s+thích|mô\s+tả|liệt\s+kê|tóm\s+tắt)|(?:can\s+you|please|tell\s+me|explain|describe|list)\s+(?:the\s+|a\s+)?)[,:\s]*/i;

/** Truncate at the last word boundary before maxLen — never cuts mid-word. */
export function previewText(text: string, maxLen = 60): string {
  const trimmed = text.trim();
  if (trimmed.length <= maxLen) return trimmed;
  // Find last space at or before maxLen - 1 to leave room for "…"
  const cut = trimmed.lastIndexOf(" ", maxLen - 1);
  const end = cut > 0 ? cut : maxLen - 1;
  return `${trimmed.slice(0, end)}…`;
}

/** Derive a concise sidebar title from the user's first prompt. */
export function deriveSessionTitle(prompt: string, maxLen = 60): string {
  const trimmed = prompt.trim().replace(FILLER_OPENER, "");
  if (!trimmed) return "";

  // Use first non-empty line (multi-line messages)
  const firstLine = trimmed.split(/\n+/)[0]?.trim() ?? trimmed;

  // If the first sentence ends with a sentence-terminating punctuation, use it
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

  // Only advance updatedAt when messages actually grew (new exchange or webhook step).
  // Preserving it when count is unchanged prevents merely viewing a session from
  // bumping it to the top of the list.
  const messagesGrew = !existing || messages.length > existing.messages.length;

  return {
    sessionId,
    title,
    messages,
    targetDepartments,
    targetAutoRoute,
    createdAt: existing?.createdAt ?? now,
    updatedAt: messagesGrew ? now : (existing?.updatedAt ?? now),
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
