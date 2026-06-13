import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ChatPage } from "./ChatPage";
import { DashboardPage } from "./DashboardPage";
import { SettingsPage } from "./SettingsPage";
import { AdminPage } from "./AdminPage";
import { renderWithUser } from "@/test/test-utils";
import { useSidebarStore } from "@/store/sidebarStore";

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
    deflection_rate: 0.85,
    answered_wrong_rate: 0.05,
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

describe("ChatPage", () => {
  beforeEach(() => {
    useSidebarStore.setState({ open: false });
    useSidebarStore.persist?.clearStorage?.();
  });

  it("renders chat interface smoke test", () => {
    renderWithUser(<ChatPage />);
    expect(screen.getByRole("log")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "How can I help?" })).toBeInTheDocument();
  });

  it("shows session history button on desktop when sidebar is closed", () => {
    vi.stubGlobal(
      "matchMedia",
      vi.fn((query: string) => ({
        matches: query === "(min-width: 768px)",
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    );

    renderWithUser(<ChatPage />);
    expect(screen.getByRole("button", { name: "Open session history" })).toBeInTheDocument();
    expect(screen.queryByRole("complementary", { name: "Session history" })).not.toBeInTheDocument();
  });

  it("opens desktop sidebar from corner button and closes with header button", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "matchMedia",
      vi.fn((query: string) => ({
        matches: query === "(min-width: 768px)",
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    );

    renderWithUser(<ChatPage />);
    await user.click(screen.getByRole("button", { name: "Open session history" }));
    expect(screen.getByRole("complementary", { name: "Session history" })).toBeInTheDocument();
    expect(useSidebarStore.getState().open).toBe(true);

    await user.click(screen.getByRole("button", { name: "Close session history" }));
    expect(screen.queryByRole("complementary", { name: "Session history" })).not.toBeInTheDocument();
    expect(useSidebarStore.getState().open).toBe(false);
  });
});

describe("DashboardPage", () => {
  beforeEach(() => {
    dashboardRefreshMock.mockReset();
    mockDashboard = {
      data: {
        query_count: 10,
        refusal_rate: 0.1,
        deflection_rate: 0.85,
        answered_wrong_rate: 0.05,
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
    expect(screen.getByText("Partial answer rate")).toBeInTheDocument();
    expect(screen.getByText("Conflict rate")).toBeInTheDocument();
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

describe("AdminPage", () => {
  it("renders admin sync controls and status sections", () => {
    renderWithUser(<AdminPage />);
    expect(screen.getByRole("heading", { name: "Knowledge sync" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sync all departments" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Recent sync jobs" })).toBeInTheDocument();
    expect(screen.getByText("No sync jobs yet.")).toBeInTheDocument();
  });
});
