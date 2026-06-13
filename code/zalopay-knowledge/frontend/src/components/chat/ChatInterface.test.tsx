import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ChatInterface } from "./ChatInterface";
import type { ChatMessage } from "@/hooks/useChat";
import type { ChatResponse } from "@/lib/types";
import { renderWithUser } from "@/test/test-utils";

const sendMessageMock = vi.fn();
const retryLastMock = vi.fn();
const setInputMock = vi.fn();
const setTargetDepartmentsMock = vi.fn();

const clarifyResponse: ChatResponse = {
  answer: "Which department are you asking about?",
  citations: [],
  source_departments: [],
  confidence: 0.3,
  feedback_id: "fb-clarify",
  status: "refused",
  clarifying_question: {
    prompt: "Which department are you asking about?",
    options: ["risk", "grow_enablement", "bank_partnerships"],
  },
};

let mockChatState = {
  messages: [] as ChatMessage[],
  input: "",
  setInput: setInputMock,
  targetDepartments: [] as ChatResponse["source_departments"],
  setTargetDepartments: setTargetDepartmentsMock,
  loading: false,
  streamingStatus: null as string | null,
  error: null as string | null,
  sendMessage: sendMessageMock,
  retryLast: retryLastMock,
};

let mockHealth = {
  health: { status: "healthy" as const, index_ready: true },
  error: null,
  loading: false,
  refresh: vi.fn(),
};

vi.mock("@/hooks/useChat", () => ({
  useChat: () => mockChatState,
}));

vi.mock("@/hooks/useHealth", () => ({
  useHealth: () => mockHealth,
}));

describe("ChatInterface", () => {
  beforeEach(() => {
    sendMessageMock.mockReset();
    retryLastMock.mockReset();
    setInputMock.mockReset();
    setTargetDepartmentsMock.mockReset();
    mockChatState = {
      messages: [],
      input: "",
      setInput: setInputMock,
      targetDepartments: [],
      setTargetDepartments: setTargetDepartmentsMock,
      loading: false,
      streamingStatus: null,
      error: null,
      sendMessage: sendMessageMock,
      retryLast: retryLastMock,
    };
    mockHealth = {
      health: { status: "healthy", index_ready: true },
      error: null,
      loading: false,
      refresh: vi.fn(),
    };
  });

  it("shows warning and disables input when index is not ready", () => {
    mockHealth.health = { status: "healthy", index_ready: false };
    renderWithUser(<ChatInterface />);

    expect(screen.getByText(/Knowledge base not synced yet/i)).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toBeDisabled();
  });

  it("renders empty state with example questions", async () => {
    const user = userEvent.setup();
    renderWithUser(<ChatInterface />);

    expect(screen.getByRole("heading", { name: "How can I help?" })).toBeInTheDocument();
    const example = screen.getByRole("button", {
      name: /How does settlement reconciliation work with partner banks/i,
    });
    await user.click(example);
    expect(sendMessageMock).toHaveBeenCalledWith(
      "How does settlement reconciliation work with partner banks?",
    );
  });

  it("shows Vietnamese empty state examples when locale is vi", () => {
    renderWithUser(<ChatInterface />, { locale: "vi" });
    expect(screen.getByRole("heading", { name: "Tôi có thể giúp gì?" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Quy trình đối soát thanh toán/i }),
    ).toBeInTheDocument();
  });

  it("shows typing indicator while loading with streaming status", () => {
    mockChatState.loading = true;
    mockChatState.streamingStatus = "synthesize";
    mockChatState.messages = [
      {
        id: "user-1",
        role: "user",
        content: "Hello?",
        timestamp: new Date().toISOString(),
      },
    ];

    renderWithUser(<ChatInterface />);
    expect(screen.getByText("synthesize")).toBeInTheDocument();
    expect(screen.getByText(/Thinking/i)).toBeInTheDocument();
  });

  it("maps timeout errors and offers retry", async () => {
    const user = userEvent.setup();
    mockChatState.error = "Request timeout 408";
    mockChatState.messages = [
      {
        id: "user-1",
        role: "user",
        content: "Slow question?",
        timestamp: new Date().toISOString(),
      },
    ];

    renderWithUser(<ChatInterface />);
    expect(
      screen.getByText(/Request timed out. Try a narrower question./i),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(retryLastMock).toHaveBeenCalled();
  });

  it("clarify flow resends the last user question with the chosen department", async () => {
    const user = userEvent.setup();
    mockChatState.messages = [
      {
        id: "user-1",
        role: "user",
        content: "What is the policy?",
        timestamp: new Date().toISOString(),
      },
      {
        id: "assistant-1",
        role: "assistant",
        content: clarifyResponse.answer,
        timestamp: new Date().toISOString(),
        response: clarifyResponse,
      },
    ];

    renderWithUser(<ChatInterface />);
    const clarifyRegion = screen.getByRole("region", { name: "Clarification needed" });
    await user.click(within(clarifyRegion).getByRole("button", { name: "Risk" }));

    expect(setTargetDepartmentsMock).toHaveBeenCalledWith(["risk"]);
    expect(sendMessageMock).toHaveBeenCalledWith("What is the policy?", ["risk"]);
  });

  it("renders access_denied refusal in the message thread", () => {
    mockChatState.messages = [
      {
        id: "assistant-1",
        role: "assistant",
        content: "Access blocked.",
        timestamp: new Date().toISOString(),
        response: {
          answer: "Access blocked.",
          citations: [],
          source_departments: [],
          confidence: 0,
          feedback_id: "fb-denied",
          status: "refused",
          refusal_reason: "access_denied",
        },
      },
    ];

    renderWithUser(<ChatInterface />);
    expect(screen.getByRole("heading", { name: "Access denied" })).toBeInTheDocument();
    expect(screen.getByText("Access blocked.")).toBeInTheDocument();
  });
});
