import { beforeEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, chatStream, parseSseBuffer } from "./apiClient";
import type { ChatResponse, UserContext } from "./types";

const ctx: UserContext = {
  userId: "user-abc123",
  sessionId: "sess-xyz789",
  role: "engineer",
  homeDept: "risk",
  locale: "en",
};

function mockFetch(response: {
  ok?: boolean;
  status?: number;
  statusText?: string;
  body?: unknown;
}) {
  const {
    ok = true,
    status = 200,
    statusText = "OK",
    body = {},
  } = response;

  return vi.fn().mockResolvedValue({
    ok,
    status,
    statusText,
    json: () => Promise.resolve(body),
  } as Response);
}

describe("apiClient", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetch({ body: { status: "healthy", index_ready: true } }));
  });

  it("injects AgentBase headers on chat requests", async () => {
    const chatBody = {
      answer: "test",
      citations: [],
      source_departments: [],
      confidence: 0.9,
      feedback_id: "fb-1",
      status: "answered" as const,
    };
    vi.stubGlobal("fetch", mockFetch({ body: chatBody }));

    await api.chat({ question: "Hello?" }, ctx);

    expect(fetch).toHaveBeenCalledOnce();
    const [, init] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Record<string, string>;

    expect(headers["Content-Type"]).toBe("application/json");
    expect(headers["X-GreenNode-AgentBase-User-Id"]).toBe(ctx.userId);
    expect(headers["X-GreenNode-AgentBase-Session-Id"]).toBe(ctx.sessionId);
    expect(headers["X-GreenNode-AgentBase-Role"]).toBe(ctx.role);
    expect(headers["X-GreenNode-AgentBase-Home-Department"]).toBe(ctx.homeDept);
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify({ question: "Hello?" }));
  });

  it("injects headers on feedback and sync endpoints", async () => {
    vi.stubGlobal("fetch", mockFetch({ status: 204, body: undefined }));

    await api.feedback({ feedback_id: "fb-1", rating: "up" }, ctx);
    await api.syncConfluence(ctx);

    const calls = (fetch as ReturnType<typeof vi.fn>).mock.calls;
    expect(calls[0][0]).toBe("/feedback");
    expect(calls[1][0]).toBe("/sync/confluence");

    for (const [, init] of calls) {
      const headers = (init as RequestInit).headers as Record<string, string>;
      expect(headers["X-GreenNode-AgentBase-User-Id"]).toBe(ctx.userId);
    }
  });

  it("does not inject user headers on health without context", async () => {
    const health = { status: "healthy" as const, index_ready: true };
    vi.stubGlobal("fetch", mockFetch({ body: health }));

    const result = await api.health();

    expect(result).toEqual(health);
    const [, init] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Record<string, string>;
    expect(headers["X-GreenNode-AgentBase-User-Id"]).toBeUndefined();
  });

  it("throws ApiError with detail from response body", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch({
        ok: false,
        status: 503,
        statusText: "Service Unavailable",
        body: { detail: "Knowledge base not ready" },
      }),
    );

    await expect(api.dashboard()).rejects.toMatchObject({
      name: "ApiError",
      status: 503,
      detail: "Knowledge base not ready",
      message: "Knowledge base not ready",
    } satisfies Partial<ApiError>);
  });

  it("returns undefined for 204 responses", async () => {
    vi.stubGlobal("fetch", mockFetch({ status: 204, body: undefined }));

    const result = await api.feedback({ feedback_id: "fb-1", rating: "down" }, ctx);
    expect(result).toBeUndefined();
  });

  it("calls syncGdrive with user headers", async () => {
    vi.stubGlobal("fetch", mockFetch({ body: { job_id: "gdrive-1" } }));

    await api.syncGdrive(ctx);

    expect(fetch).toHaveBeenCalledWith("/sync/gdrive", expect.objectContaining({ method: "POST" }));
    const [, init] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Record<string, string>;
    expect(headers["X-GreenNode-AgentBase-User-Id"]).toBe(ctx.userId);
  });

  it("throws ApiError using statusText when body has no detail", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch({
        ok: false,
        status: 502,
        statusText: "Bad Gateway",
        body: {},
      }),
    );

    await expect(api.health()).rejects.toMatchObject({
      name: "ApiError",
      status: 502,
      message: "Bad Gateway",
    });
  });

  it("calls sync status and dashboard without user context", async () => {
    const syncStatus = { sources: [] };
    const dashboard = {
      query_count: 0,
      refusal_rate: 0,
      partial_rate: 0,
      conflict_rate: 0,
      latency_p50_ms: 0,
      latency_p95_ms: 0,
      feedback_up: 0,
      feedback_down: 0,
      total_tokens: 0,
      history: [],
    };

    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve(syncStatus),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve(dashboard),
        }),
    );

    await expect(api.syncStatus()).resolves.toEqual(syncStatus);
    await expect(api.dashboard()).resolves.toEqual(dashboard);

    const calls = (fetch as ReturnType<typeof vi.fn>).mock.calls;
    expect(calls[0]?.[0]).toBe("/sync/status");
    expect(calls[1]?.[0]).toBe("/api/dashboard");
  });
});

describe("parseSseBuffer", () => {
  it("parses complete SSE data lines", () => {
    const buffer =
      'data: {"event":"start","data":{"question":"hi"}}\n\n' +
      'data: {"event":"node","data":{"node":"retrieve"}}\n';

    const { events, remainder } = parseSseBuffer(buffer);

    expect(events).toHaveLength(2);
    expect(events[0]).toEqual({ event: "start", data: { question: "hi" } });
    expect(events[1]).toEqual({ event: "node", data: { node: "retrieve" } });
    expect(remainder).toBe("");
  });

  it("keeps incomplete trailing line in remainder", () => {
    const buffer = 'data: {"event":"start","data":{}}\n\ndata: {"ev';
    const { events, remainder } = parseSseBuffer(buffer);

    expect(events).toHaveLength(1);
    expect(remainder).toBe('data: {"ev');
  });

  it("skips malformed SSE JSON lines", () => {
    const buffer =
      'data: not-json\n\n' +
      'data: {"event":"done","data":{"answer":"ok"}}\n\n';

    const { events } = parseSseBuffer(buffer);
    expect(events).toHaveLength(1);
    expect(events[0]?.event).toBe("done");
  });
});

function mockStreamResponse(chunks: string[], init?: { ok?: boolean; status?: number }) {
  const encoder = new TextEncoder();
  let index = 0;

  const reader = {
    read: vi.fn().mockImplementation(async () => {
      if (index >= chunks.length) {
        return { done: true, value: undefined };
      }
      const value = encoder.encode(chunks[index]);
      index += 1;
      return { done: false, value };
    }),
    releaseLock: vi.fn(),
  };

  return {
    ok: init?.ok ?? true,
    status: init?.status ?? 200,
    body: { getReader: () => reader },
    reader,
  };
}

describe("chatStream", () => {
  const ctx: UserContext = {
    userId: "user-abc123",
    sessionId: "sess-xyz789",
    role: "engineer",
    homeDept: "risk",
    locale: "en",
  };

  const donePayload: ChatResponse = {
    answer: "Streamed answer",
    citations: [],
    source_departments: ["risk"],
    confidence: 0.9,
    feedback_id: "fb-stream",
    status: "answered",
  };

  it("yields parsed SSE events from a readable stream", async () => {
    const sse =
      'data: {"event":"start","data":{"question":"Hello?"}}\n\n' +
      `data: ${JSON.stringify({ event: "done", data: donePayload })}\n\n`;

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(mockStreamResponse([sse])),
    );

    const events = [];
    for await (const event of chatStream({ question: "Hello?" }, ctx)) {
      events.push(event);
    }

    expect(events).toHaveLength(2);
    expect(events[0]?.event).toBe("start");
    expect(events[1]?.event).toBe("done");
    expect((events[1]?.data as ChatResponse).answer).toBe("Streamed answer");

    expect(fetch).toHaveBeenCalledWith(
      "/chat/stream",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ question: "Hello?" }),
      }),
    );
  });

  it("invokes onEvent for each parsed chunk", async () => {
    const sse =
      'data: {"event":"node","data":{"node":"synthesize"}}\n\n';
    const onEvent = vi.fn();

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(mockStreamResponse([sse])),
    );

    for await (const _ of chatStream({ question: "q" }, ctx, { onEvent })) {
      /* drain */
    }

    expect(onEvent).toHaveBeenCalledWith({
      event: "node",
      data: { node: "synthesize" },
    });
  });

  it("throws ApiError when the stream response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        statusText: "Service Unavailable",
        json: () => Promise.resolve({ detail: "Knowledge base not ready" }),
      }),
    );

    await expect(async () => {
      for await (const _ of chatStream({ question: "q" }, ctx)) {
        /* drain */
      }
    }).rejects.toMatchObject({
      name: "ApiError",
      status: 503,
      detail: "Knowledge base not ready",
    });
  });

  it("injects AgentBase headers on stream requests", async () => {
    const sse = `data: ${JSON.stringify({ event: "done", data: donePayload })}\n\n`;
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockStreamResponse([sse])));

    for await (const _ of chatStream({ question: "Hello?" }, ctx)) {
      /* drain */
    }

    const [, init] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Record<string, string>;
    expect(headers["X-GreenNode-AgentBase-User-Id"]).toBe(ctx.userId);
    expect(headers["X-GreenNode-AgentBase-Home-Department"]).toBe(ctx.homeDept);
  });

  it("forwards abort signal to fetch", async () => {
    const controller = new AbortController();
    const sse = `data: ${JSON.stringify({ event: "done", data: donePayload })}\n\n`;
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockStreamResponse([sse])));

    for await (const _ of chatStream({ question: "q" }, ctx, { signal: controller.signal })) {
      /* drain */
    }

    const [, init] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0] as [string, RequestInit];
    expect(init.signal).toBe(controller.signal);
  });

  it("throws when the response body cannot be streamed", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        body: null,
      }),
    );

    await expect(async () => {
      for await (const _ of chatStream({ question: "q" }, ctx)) {
        /* drain */
      }
    }).rejects.toThrow("Streaming not supported");
  });

  it("posts to /invocations via api.invocations", async () => {
    const chatBody = {
      answer: "alias",
      citations: [],
      source_departments: [],
      confidence: 1,
      feedback_id: "fb-2",
      status: "answered" as const,
    };
    vi.stubGlobal("fetch", mockFetch({ body: chatBody }));

    await api.invocations({ question: "Hello?" }, ctx);

    expect(fetch).toHaveBeenCalledWith(
      "/invocations",
      expect.objectContaining({ method: "POST" }),
    );
  });
});
