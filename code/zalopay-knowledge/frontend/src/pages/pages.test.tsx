import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ChatPage } from "./ChatPage";
import { DashboardPage } from "./DashboardPage";
import { SettingsPage } from "./SettingsPage";
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

const dashboardRefreshMock = vi.fn();

let mockDashboard = {
  data: {
    query_count: 10,
    refusal_rate: 0.1,
    partial_rate: 0.05,
    conflict_rate: 0.02,
    latency_p50_ms: 500,
    latency_p95_ms: 1200,
    feedback_up: 8,
    feedback_down: 2,
    total_tokens: 1000,
    history: [],
  },
  error: null as string | null,
  loading: false,
  refresh: dashboardRefreshMock,
};

vi.mock("@/hooks/useDashboard", () => ({
  useDashboard: () => mockDashboard,
}));

vi.mock("@/hooks/useSyncStatus", () => ({
  useSyncStatus: () => ({
    status: { sources: [] },
    error: null,
    loading: false,
    refresh: vi.fn(),
  }),
}));

describe("ChatPage", () => {
  it("renders chat interface smoke test", () => {
    renderWithUser(<ChatPage />);
    expect(screen.getByRole("log")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "How can I help?" })).toBeInTheDocument();
  });
});

describe("DashboardPage", () => {
  beforeEach(() => {
    dashboardRefreshMock.mockReset();
    mockDashboard = {
      data: {
        query_count: 10,
        refusal_rate: 0.1,
        partial_rate: 0.05,
        conflict_rate: 0.02,
        latency_p50_ms: 500,
        latency_p95_ms: 1200,
        feedback_up: 8,
        feedback_down: 2,
        total_tokens: 1000,
        history: [],
      },
      error: null,
      loading: false,
      refresh: dashboardRefreshMock,
    };
  });

  it("renders dashboard title and sections", () => {
    renderWithUser(<DashboardPage />);
    expect(screen.getByRole("heading", { name: "Usage & Health" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Sync Status" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Recent Queries" })).toBeInTheDocument();
    expect(screen.getByText("Total queries")).toBeInTheDocument();
  });

  it("shows loading spinner before dashboard data arrives", () => {
    mockDashboard = {
      data: null,
      error: null,
      loading: true,
      refresh: dashboardRefreshMock,
    };

    renderWithUser(<DashboardPage />);
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("shows dashboard error with retry", async () => {
    const user = userEvent.setup();
    mockDashboard = {
      data: null,
      error: "Dashboard unavailable",
      loading: false,
      refresh: dashboardRefreshMock,
    };

    renderWithUser(<DashboardPage />);
    expect(screen.getByRole("alert")).toHaveTextContent("Dashboard unavailable");

    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(dashboardRefreshMock).toHaveBeenCalled();
  });
});

describe("SettingsPage", () => {
  it("renders settings sections", () => {
    renderWithUser(<SettingsPage />);
    expect(screen.getByRole("heading", { name: "Settings" })).toBeInTheDocument();
    expect(screen.getByText("Your identity")).toBeInTheDocument();
    expect(
      screen.getByText(/Role and home department are sent with every chat request/i),
    ).toBeInTheDocument();
    expect(screen.getByText("Knowledge sync")).toBeInTheDocument();
    expect(screen.getByText("Runtime config")).toBeInTheDocument();
  });
});
