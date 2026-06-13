import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useChat } from "./useChat";
import { ApiError } from "@/lib/apiClient";
import { getUserContext } from "@/store/userStore";
import type { ChatResponse } from "@/lib/types";
import { resetUserStore } from "@/test/test-utils";

const chatStreamMock = vi.fn();
const chatMock = vi.fn();

vi.mock("@/lib/apiClient", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/apiClient")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      chat: (...args: unknown[]) => chatMock(...args),
    },
    chatStream: (...args: unknown[]) => chatStreamMock(...args),
  };
});

const answeredResponse: ChatResponse = {
  answer: "Settlement policy requires approval.",
  citations: [],
  source_departments: ["risk"],
  confidence: 0.9,
  feedback_id: "fb-1",
  status: "answered",
};

async function* streamOf(
  events: Array<{ event: string; data: Record<string, unknown> }>,
) {
  for (const event of events) {
    yield event;
  }
}

function installSyncRaf() {
  vi.stubGlobal("requestAnimationFrame", (cb: FrameRequestCallback) => {
    cb(0);
    return 1;
  });
}

describe("useChat", () => {
  beforeEach(() => {
    chatStreamMock.mockReset();
    chatMock.mockReset();
    resetUserStore();
    installSyncRaf();
  });

  it("sends a message via stream and appends user and assistant messages", async () => {
    chatStreamMock.mockReturnValue(
      streamOf([
        { event: "node", data: { node: "retrieve" } },
        { event: "done", data: answeredResponse as unknown as Record<string, unknown> },
      ]),
    );

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("What is settlement policy?");
    });

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(2);
    });

    expect(result.current.messages[0]).toMatchObject({
      role: "user",
      content: "What is settlement policy?",
    });
    expect(result.current.messages[1]).toMatchObject({
      role: "assistant",
      content: answeredResponse.answer,
    });
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("includes pinned target_departments in the stream request body", async () => {
    chatStreamMock.mockReturnValue(
      streamOf([
        { event: "done", data: answeredResponse as unknown as Record<string, unknown> },
      ]),
    );

    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.setTargetDepartments(["risk", "grow_enablement"]);
    });

    await act(async () => {
      await result.current.sendMessage("Pinned question?");
    });

    expect(chatStreamMock).toHaveBeenCalledWith(
      {
        question: "Pinned question?",
        target_departments: ["risk", "grow_enablement"],
      },
      getUserContext(),
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );
  });

  it("sends null target_departments when auto-route is active", async () => {
    chatStreamMock.mockReturnValue(
      streamOf([
        { event: "done", data: answeredResponse as unknown as Record<string, unknown> },
      ]),
    );

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("Auto-routed question?");
    });

    expect(chatStreamMock).toHaveBeenCalledWith(
      expect.objectContaining({ target_departments: null }),
      expect.any(Object),
      expect.any(Object),
    );
  });

  it("allows override departments on sendMessage", async () => {
    chatStreamMock.mockReturnValue(
      streamOf([
        { event: "done", data: answeredResponse as unknown as Record<string, unknown> },
      ]),
    );

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("Clarify resend?", ["bank_partnerships"]);
    });

    expect(chatStreamMock).toHaveBeenCalledWith(
      expect.objectContaining({
        question: "Clarify resend?",
        target_departments: ["bank_partnerships"],
      }),
      expect.any(Object),
      expect.any(Object),
    );
  });

  it("sets streamingStatus from node events", async () => {
    let resolveDone: () => void;
    const donePromise = new Promise<void>((resolve) => {
      resolveDone = resolve;
    });

    chatStreamMock.mockReturnValue(
      (async function* () {
        yield { event: "node", data: { node: "synthesize" } };
        await donePromise;
        yield { event: "done", data: answeredResponse as unknown as Record<string, unknown> };
      })(),
    );

    const { result } = renderHook(() => useChat());

    let sendPromise!: Promise<void>;
    act(() => {
      sendPromise = result.current.sendMessage("Stream status?");
    });

    await waitFor(() => {
      expect(result.current.streamingStatus).toBe("synthesize");
    });

    await act(async () => {
      resolveDone!();
      await sendPromise;
    });
  });

  it("sets error when stream emits an error event", async () => {
    chatStreamMock.mockReturnValue(
      streamOf([{ event: "error", data: { detail: "Grade gate refused" } }]),
    );

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("Blocked question?");
    });

    expect(result.current.error).toBe("Grade gate refused");
    expect(result.current.messages).toHaveLength(1);
  });

  it("sets error from ApiError when stream HTTP fails", async () => {
    chatStreamMock.mockImplementation(() => {
      throw new ApiError("Knowledge base not ready", 503, "Knowledge base not ready");
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("Unavailable KB?");
    });

    expect(result.current.error).toBe("Knowledge base not ready");
    expect(chatMock).not.toHaveBeenCalled();
  });

  it("falls back to api.chat on transport errors", async () => {
    chatStreamMock.mockImplementation(() => {
      throw new TypeError("Failed to fetch");
    });
    chatMock.mockResolvedValue(answeredResponse);

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("Fallback question?");
    });

    expect(chatMock).toHaveBeenCalledWith(
      { question: "Fallback question?", target_departments: null },
      getUserContext(),
    );
    await waitFor(() => {
      expect(result.current.messages[1]?.content).toBe(answeredResponse.answer);
    });
  });

  it("sets error when chat fallback also fails", async () => {
    chatStreamMock.mockImplementation(() => {
      throw new TypeError("Network down");
    });
    chatMock.mockRejectedValue(new ApiError("Server error", 500, "Server error"));

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("Double failure?");
    });

    expect(result.current.error).toBe("Server error");
  });

  it("ignores blank questions and concurrent sends while loading", async () => {
    let resolveStream: () => void;
    const streamGate = new Promise<void>((resolve) => {
      resolveStream = resolve;
    });

    chatStreamMock.mockReturnValue(
      (async function* () {
        await streamGate;
        yield { event: "done", data: answeredResponse as unknown as Record<string, unknown> };
      })(),
    );

    const { result } = renderHook(() => useChat());

    let firstSend!: Promise<void>;
    act(() => {
      firstSend = result.current.sendMessage("First?");
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(true);
    });

    await act(async () => {
      await result.current.sendMessage("   ");
      await result.current.sendMessage("Second while loading?");
    });

    await act(async () => {
      resolveStream!();
      await firstSend;
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.messages.filter((m) => m.role === "user")).toHaveLength(1);
  });

  it("retryLast removes the failed exchange and resends the last question", async () => {
    chatStreamMock
      .mockReturnValueOnce(streamOf([{ event: "error", data: { detail: "Temporary failure" } }]))
      .mockReturnValueOnce(
        streamOf([
          { event: "done", data: answeredResponse as unknown as Record<string, unknown> },
        ]),
      );

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("Retry me?");
    });

    expect(result.current.error).toBe("Temporary failure");

    await act(async () => {
      result.current.retryLast();
    });

    await waitFor(() => {
      expect(result.current.error).toBeNull();
      expect(result.current.messages).toHaveLength(2);
    });

    expect(chatStreamMock).toHaveBeenCalledTimes(2);
    expect(chatStreamMock).toHaveBeenLastCalledWith(
      expect.objectContaining({ question: "Retry me?" }),
      expect.any(Object),
      expect.any(Object),
    );
  });

  it("clears input after sending", async () => {
    chatStreamMock.mockReturnValue(
      streamOf([
        { event: "done", data: answeredResponse as unknown as Record<string, unknown> },
      ]),
    );

    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.setInput("Draft question");
    });

    await act(async () => {
      await result.current.sendMessage("Draft question");
    });

    expect(result.current.input).toBe("");
  });
});
