import type {
  AdminSyncHistoryWire,
  AdminSyncRequest,
  AdminSyncResponse,
  AdminSyncStatusWire,
  ChatRequest,
  ChatResponse,
  ChatStreamEvent,
  DashboardData,
  FeedbackRequest,
  HealthInfo,
  SyncStartResponse,
  SyncStatus,
  UserContext,
} from "./types";

export type { ChatStreamEvent };

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly detail?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function buildHeaders(ctx: UserContext): HeadersInit {
  return {
    "Content-Type": "application/json",
    "X-GreenNode-AgentBase-User-Id": ctx.userId,
    "X-GreenNode-AgentBase-Session-Id": ctx.sessionId,
    "X-GreenNode-AgentBase-Role": ctx.role,
    "X-GreenNode-AgentBase-Home-Department": ctx.homeDept,
  };
}

async function parseError(res: Response): Promise<ApiError> {
  let detail: string | undefined;
  try {
    const body = (await res.json()) as { detail?: string };
    detail = body.detail;
  } catch {
    /* empty body */
  }
  const message = detail ?? res.statusText ?? "Request failed";
  return new ApiError(message, res.status, detail);
}

async function request<T>(
  path: string,
  init: RequestInit,
  ctx?: UserContext,
): Promise<T> {
  const headers: HeadersInit = {
  ...(init.headers as Record<string, string>),
  };

  if (ctx) {
    Object.assign(headers, buildHeaders(ctx));
  }

  const res = await fetch(path, { ...init, headers });

  if (!res.ok) {
    throw await parseError(res);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}

/** POST endpoints that return a JSON body on 409 Conflict (e.g. sync already running). */
async function requestWithConflictBody<T>(
  path: string,
  init: RequestInit,
  ctx?: UserContext,
): Promise<T> {
  const headers: HeadersInit = {
    ...(init.headers as Record<string, string>),
  };

  if (ctx) {
    Object.assign(headers, buildHeaders(ctx));
  }

  const res = await fetch(path, { ...init, headers });

  if (res.status === 409) {
    return (await res.json()) as T;
  }

  if (!res.ok) {
    throw await parseError(res);
  }

  return (await res.json()) as T;
}

/** Parse SSE `data:` lines from a text buffer; returns parsed events and leftover text. */
export function parseSseBuffer(buffer: string): {
  events: ChatStreamEvent[];
  remainder: string;
} {
  const events: ChatStreamEvent[] = [];
  const lines = buffer.split("\n");
  const remainder = lines.pop() ?? "";

  for (const raw of lines) {
    const line = raw.endsWith("\r") ? raw.slice(0, -1) : raw;
    if (!line.startsWith("data: ")) continue;
    const payload = line.slice(6).trim();
    if (!payload) continue;
    try {
      events.push(JSON.parse(payload) as ChatStreamEvent);
    } catch {
      /* skip malformed SSE chunk */
    }
  }

  return { events, remainder };
}

export type ChatStreamHandlers = {
  onEvent?: (event: ChatStreamEvent) => void;
  signal?: AbortSignal;
};

/**
 * Stream chat via POST /chat/stream (fetch + ReadableStream).
 * Yields parsed SSE events until the stream closes.
 */
export async function* chatStream(
  body: ChatRequest,
  ctx: UserContext,
  options: ChatStreamHandlers = {},
): AsyncGenerator<ChatStreamEvent> {
  const res = await fetch("/chat/stream", {
    method: "POST",
    headers: buildHeaders(ctx),
    body: JSON.stringify(body),
    signal: options.signal,
  });

  if (!res.ok) {
    throw await parseError(res);
  }

  const reader = res.body?.getReader();
  if (!reader) {
    throw new Error("Streaming not supported");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parsed = parseSseBuffer(buffer);
      buffer = parsed.remainder;

      for (const event of parsed.events) {
        options.onEvent?.(event);
        yield event;
      }
    }

    if (buffer.trim()) {
      const parsed = parseSseBuffer(`${buffer}\n`);
      for (const event of parsed.events) {
        options.onEvent?.(event);
        yield event;
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export const api = {
  health(): Promise<HealthInfo> {
    return request<HealthInfo>("/health", { method: "GET" });
  },

  chat(body: ChatRequest, ctx: UserContext): Promise<ChatResponse> {
    return request<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify(body),
    }, ctx);
  },

  /** AgentBase-compatible alias for POST /chat. */
  invocations(body: ChatRequest, ctx: UserContext): Promise<ChatResponse> {
    return request<ChatResponse>("/invocations", {
      method: "POST",
      body: JSON.stringify(body),
    }, ctx);
  },

  chatStream,

  feedback(body: FeedbackRequest, ctx: UserContext): Promise<void> {
    return request<void>("/feedback", {
      method: "POST",
      body: JSON.stringify(body),
    }, ctx);
  },

  syncConfluence(ctx: UserContext): Promise<SyncStartResponse> {
    return request<SyncStartResponse>("/sync/confluence", { method: "POST" }, ctx);
  },

  syncGdrive(ctx: UserContext): Promise<SyncStartResponse> {
    return request<SyncStartResponse>("/sync/gdrive", { method: "POST" }, ctx);
  },

  syncStatus(): Promise<SyncStatus> {
    return request<SyncStatus>("/sync/status", { method: "GET" });
  },

  dashboard(): Promise<DashboardData> {
    return request<DashboardData>("/api/dashboard", { method: "GET" });
  },

  adminSync(body: AdminSyncRequest, ctx: UserContext): Promise<AdminSyncResponse> {
    return requestWithConflictBody<AdminSyncResponse>(
      "/api/admin/sync",
      { method: "POST", body: JSON.stringify(body) },
      ctx,
    );
  },

  adminSyncStatus(): Promise<AdminSyncStatusWire> {
    return request<AdminSyncStatusWire>("/api/admin/sync/status", { method: "GET" });
  },

  adminSyncHistory(limit = 10): Promise<AdminSyncHistoryWire> {
    const params = new URLSearchParams({ limit: String(limit) });
    return request<AdminSyncHistoryWire>(`/api/admin/sync/history?${params}`, {
      method: "GET",
    });
  },

  suggestedQuestions(): Promise<{ questions: string[] }> {
    return request<{ questions: string[] }>("/api/suggested-questions", { method: "GET" });
  },
};
