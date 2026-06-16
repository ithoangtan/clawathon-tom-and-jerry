import { beforeEach, describe, expect, it } from "vitest";
import type { ChatMessage } from "@/hooks/useChat";
import { useSessionStore } from "./sessionStore";
import { resetSessionStore } from "@/test/test-utils";

const sampleMessages: ChatMessage[] = [
  {
    id: "user-1",
    role: "user",
    content: "Hello?",
    timestamp: "2024-01-01T10:00:00.000Z",
  },
];

describe("sessionStore", () => {
  beforeEach(() => {
    localStorage.clear();
    resetSessionStore();
  });

  it("saves and lists threads", () => {
    useSessionStore.getState().saveThread("sess-1", sampleMessages, ["risk"], false);
    const threads = useSessionStore.getState().listThreads();
    expect(threads).toHaveLength(1);
    expect(threads[0]?.sessionId).toBe("sess-1");
    expect(threads[0]?.messages).toHaveLength(1);
  });

  it("deletes a thread", () => {
    useSessionStore.getState().saveThread("sess-1", sampleMessages, [], true);
    useSessionStore.getState().deleteThread("sess-1");
    expect(useSessionStore.getState().listThreads()).toHaveLength(0);
  });

  it("queues session switch actions", () => {
    useSessionStore.getState().requestSwitchSession("sess-1");
    expect(useSessionStore.getState().sessionAction).toEqual({
      type: "switch",
      sessionId: "sess-1",
    });

    useSessionStore.getState().clearSessionAction();
    useSessionStore.getState().requestSwitchSession("sess-2", true);
    expect(useSessionStore.getState().sessionAction).toEqual({
      type: "switch",
      sessionId: "sess-2",
      skipSave: true,
    });
  });
});
