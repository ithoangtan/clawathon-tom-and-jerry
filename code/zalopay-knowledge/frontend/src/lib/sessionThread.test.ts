import { describe, expect, it } from "vitest";
import {
  buildThread,
  firstUserQuestion,
  matchesSearch,
  previewText,
  threadStatus,
} from "./sessionThread";
import type { ChatMessage } from "@/hooks/useChat";

const userMessage: ChatMessage = {
  id: "user-1",
  role: "user",
  content: "What is settlement policy?",
  timestamp: "2024-01-01T10:00:00.000Z",
};

describe("sessionThread helpers", () => {
  it("extracts first user question and preview text", () => {
    expect(firstUserQuestion([userMessage])).toBe("What is settlement policy?");
    expect(previewText("A".repeat(80), 72)).toHaveLength(72);
    expect(previewText("Short question")).toBe("Short question");
  });

  it("derives thread status from last assistant response", () => {
    const answered = buildThread("sess-1", [userMessage], [], true, undefined)!;
    answered.messages.push({
      id: "assistant-1",
      role: "assistant",
      content: "Answer",
      timestamp: "2024-01-01T10:01:00.000Z",
      response: {
        answer: "Answer",
        citations: [],
        source_departments: ["risk"],
        confidence: 0.9,
        feedback_id: "fb-1",
        status: "answered",
      },
    });
    expect(threadStatus(answered)).toBe("answered");

    const refused = { ...answered };
    refused.messages = [
      ...answered.messages.slice(0, 1),
      {
        ...answered.messages[1]!,
        response: { ...answered.messages[1]!.response!, status: "refused" },
      },
    ];
    expect(threadStatus(refused)).toBe("refused");

    const conflict = { ...answered };
    conflict.messages = [
      ...answered.messages.slice(0, 1),
      {
        ...answered.messages[1]!,
        response: {
          ...answered.messages[1]!.response!,
          conflicts: [{ sides: [] }],
        },
      },
    ];
    expect(threadStatus(conflict)).toBe("conflict");
  });

  it("filters threads by search query", () => {
    const thread = buildThread("sess-1", [userMessage], [], true, undefined)!;
    expect(matchesSearch(thread, "settlement")).toBe(true);
    expect(matchesSearch(thread, "unknown topic")).toBe(false);
    expect(matchesSearch(thread, "")).toBe(true);
  });

  it("returns null when saving an empty thread", () => {
    expect(buildThread("sess-empty", [], [], true)).toBeNull();
  });
});
