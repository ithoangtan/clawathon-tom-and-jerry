import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SessionSidebar, SessionSidebarPanel } from "./SessionSidebar";
import { useSessionStore } from "@/store/sessionStore";
import { resetStores, renderWithRouter } from "@/test/test-utils";

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return { ...actual, useNavigate: () => mockNavigate };
});

function seedThreads() {
  useSessionStore.getState().saveThread(
    "sess-active",
    [
      {
        id: "user-1",
        role: "user",
        content: "Settlement policy question",
        timestamp: "2024-01-01T10:00:00.000Z",
      },
      {
        id: "assistant-1",
        role: "assistant",
        content: "Policy details",
        timestamp: "2024-01-01T10:01:00.000Z",
        response: {
          answer: "Policy details",
          citations: [],
          source_departments: ["risk"],
          confidence: 0.9,
          feedback_id: "fb-1",
          status: "answered",
        },
      },
    ],
    ["risk"],
    false,
  );
  useSessionStore.getState().saveThread(
    "sess-other",
    [
      {
        id: "user-2",
        role: "user",
        content: "KYC thresholds",
        timestamp: "2024-01-02T10:00:00.000Z",
      },
    ],
    [],
    true,
  );
}

describe("SessionSidebarPanel", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    resetStores({ sessionId: "sess-active" });
    seedThreads();
  });

  it("lists sessions with active aria-current and filters by search", async () => {
    const user = userEvent.setup();
    renderWithRouter(<SessionSidebarPanel />, "/chat/sess-active", { sessionId: "sess-active" });

    const active = screen.getByRole("button", { name: /Settlement policy question/i });
    expect(active).toHaveAttribute("aria-current", "true");

    const search = screen.getByRole("searchbox", { name: "Search sessions" });
    await user.type(search, "KYC");
    expect(screen.getByText("KYC thresholds")).toBeInTheDocument();
    expect(screen.queryByText(/Settlement policy question/i)).not.toBeInTheDocument();
  });

  it("navigates to the correct session URL when another thread is selected", async () => {
    const user = userEvent.setup();
    renderWithRouter(<SessionSidebarPanel />, "/chat/sess-active", { sessionId: "sess-active" });

    await user.click(screen.getByRole("button", { name: /KYC thresholds/i }));

    expect(mockNavigate).toHaveBeenCalledWith("/chat/sess-other");
    expect(useSessionStore.getState().sessionAction).toBeNull();
  });

  it("navigates to a new session URL when the active thread is deleted", async () => {
    const user = userEvent.setup();
    renderWithRouter(<SessionSidebarPanel />, "/chat/sess-active", { sessionId: "sess-active" });

    const activeItem = screen.getByRole("button", { name: /Settlement policy question/i });
    const row = activeItem.parentElement!;
    await user.click(within(row).getByRole("button", { name: "Delete session" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    expect(useSessionStore.getState().getThread("sess-active")).toBeUndefined();
    expect(mockNavigate).toHaveBeenCalledWith(expect.stringMatching(/^\/chat\/sess-/));
  });

  it("does not navigate when clicking the already-active session", async () => {
    const user = userEvent.setup();
    renderWithRouter(<SessionSidebarPanel />, "/chat/sess-active", { sessionId: "sess-active" });

    await user.click(screen.getByRole("button", { name: /Settlement policy question/i }));

    expect(mockNavigate).not.toHaveBeenCalled();
  });
});

describe("SessionSidebar", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    resetStores({ sessionId: "sess-active" });
    seedThreads();
  });

  it("opens mobile drawer with dialog semantics", async () => {
    const user = userEvent.setup();
    renderWithRouter(<SessionSidebar />, "/chat/sess-active", { sessionId: "sess-active" });

    // Two "Open session history" buttons exist (mobile + desktop); click the mobile one (first)
    const openBtns = screen.getAllByRole("button", { name: "Open session history" });
    await user.click(openBtns[0]);

    expect(screen.getByRole("dialog", { name: "Session history" })).toBeInTheDocument();
  });
});
