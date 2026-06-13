import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import App from "./App";
import { renderWithUser } from "@/test/test-utils";
import { useTutorialStore } from "@/store/tutorialStore";

const driveMock = vi.fn();
const destroyMock = vi.fn();

vi.mock("driver.js", () => ({
  driver: vi.fn(() => ({
    drive: driveMock,
    destroy: destroyMock,
    refresh: vi.fn(),
    moveNext: vi.fn(),
  })),
}));

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

describe("onboarding tutorial", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useTutorialStore.persist?.clearStorage?.();
    useTutorialStore.setState({ dismissed: true, hasHydrated: true });
  });

  it("renders Help button and starts tutorial on click", async () => {
    const user = userEvent.setup();
    renderWithUser(<App />);

    const helpButton = screen.getByRole("button", { name: "Help and tutorial" });
    expect(helpButton).toBeInTheDocument();

    await user.click(helpButton);
    expect(driveMock).toHaveBeenCalled();
  });

  it("auto-starts tutorial on first visit when not dismissed", async () => {
    useTutorialStore.setState({ dismissed: false, hasHydrated: true });
    renderWithUser(<App />);

    await vi.waitFor(() => {
      expect(driveMock).toHaveBeenCalled();
    });
  });

  it("does not auto-start when tutorial was dismissed", async () => {
    useTutorialStore.setState({ dismissed: true, hasHydrated: true });
    renderWithUser(<App />);

    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(driveMock).not.toHaveBeenCalled();
  });

  it("waits for store hydration before auto-start", async () => {
    useTutorialStore.setState({ dismissed: false, hasHydrated: false });
    renderWithUser(<App />);

    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(driveMock).not.toHaveBeenCalled();

    useTutorialStore.setState({ hasHydrated: true });
    await vi.waitFor(() => {
      expect(driveMock).toHaveBeenCalled();
    });
  });
});
