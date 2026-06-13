import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import App from "./App";
import { renderWithUser } from "@/test/test-utils";

vi.mock("@/hooks/useChat", () => ({
  useChat: () => ({
    messages: [],
    input: "",
    setInput: vi.fn(),
    targetDepartments: [],
    setTargetDepartments: vi.fn(),
    targetAutoRoute: true,
    setTargetAutoRoute: vi.fn(),
    loading: false,
    streamingStatus: null,
    pipelineProgress: null,
    dismissPipelineSummary: vi.fn(),
    error: null,
    sendMessage: vi.fn(),
    retryLast: vi.fn(),
  }),
}));

vi.mock("@/hooks/useHealth", () => ({
  useHealth: () => ({
    health: { status: "healthy", index_ready: true },
    error: null,
    loading: false,
    refresh: vi.fn(),
  }),
}));

vi.mock("@/hooks/useDashboard", () => ({
  useDashboard: () => ({
    data: {
      query_count: 0,
      refusal_rate: 0,
      deflection_rate: 0,
      answered_wrong_rate: 0,
      partial_rate: 0,
      conflict_rate: 0,
      latency_p50_ms: 0,
      latency_p95_ms: 0,
      feedback_up: 0,
      feedback_down: 0,
      total_tokens: 0,
      history: [],
    },
    error: null,
    loading: false,
    refresh: vi.fn(),
  }),
}));

vi.mock("@/hooks/useSyncStatus", () => ({
  useSyncStatus: () => ({
    status: { sources: [] },
    error: null,
    loading: false,
    refresh: vi.fn(),
  }),
}));

vi.mock("@/hooks/useAdminSyncStatus", () => ({
  useAdminSyncStatus: () => ({
    status: {
      running: false,
      departments: [],
      recent_jobs: [],
      sources: [],
    },
    error: null,
    loading: false,
    refresh: vi.fn(),
  }),
}));

describe("App navigation", () => {
  it("renders chat at / and navigates to dashboard", async () => {
    const user = userEvent.setup();
    renderWithUser(<App />);

    expect(screen.getByRole("heading", { name: "How can I help?" })).toBeInTheDocument();
    const header = screen.getByRole("banner");
    expect(within(header).getByRole("button", { name: "Switch to Vietnamese" })).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: "Dashboard" }));
    expect(screen.getByRole("heading", { name: "Usage & Health" })).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: "Admin" }));
    expect(screen.getByRole("heading", { name: "Knowledge sync" })).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: "Chat" }));
    expect(screen.getByRole("heading", { name: "How can I help?" })).toBeInTheDocument();
  });

  it("switches UI language from the header control", async () => {
    const user = userEvent.setup();
    renderWithUser(<App />);

    const header = screen.getByRole("banner");
    await user.click(within(header).getByRole("button", { name: "Switch to Vietnamese" }));

    expect(screen.getByRole("link", { name: "Hỏi đáp" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Tôi có thể giúp gì?" })).toBeInTheDocument();
  });
});
