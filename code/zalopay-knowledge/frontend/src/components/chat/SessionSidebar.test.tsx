import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { SessionSidebar } from "./SessionSidebar";
import { useSessionStore } from "@/store/sessionStore";
import { resetStores, renderWithUser } from "@/test/test-utils";

function getSidebarRegion() {
  return screen.getByRole("complementary", { name: "Session history", hidden: true });
}

describe("SessionSidebar", () => {
  beforeEach(() => {
    resetStores({ sessionId: "sess-active" });
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
  });

  it("lists sessions with active aria-current and filters by search", async () => {
    const user = userEvent.setup();
    renderWithUser(<SessionSidebar />, { sessionId: "sess-active" });

    const history = getSidebarRegion();
    const active = within(history).getByRole("button", { name: /Settlement policy question/i });
    expect(active).toHaveAttribute("aria-current", "true");

    const search = within(history).getByRole("searchbox", { name: "Search sessions" });
    await user.type(search, "KYC");
    expect(within(history).getByText("KYC thresholds")).toBeInTheDocument();
    expect(within(history).queryByText(/Settlement policy question/i)).not.toBeInTheDocument();
  });

  it("requests session switch when another thread is selected", async () => {
    const user = userEvent.setup();
    renderWithUser(<SessionSidebar />, { sessionId: "sess-active" });

    const history = getSidebarRegion();
    await user.click(within(history).getByRole("button", { name: /KYC thresholds/i }));

    expect(useSessionStore.getState().sessionAction).toEqual({
      type: "switch",
      sessionId: "sess-other",
    });
  });

  it("confirms delete and starts a new session when active thread is removed", async () => {
    const user = userEvent.setup();
    renderWithUser(<SessionSidebar />, { sessionId: "sess-active" });

    const history = getSidebarRegion();
    const activeItem = within(history).getByRole("button", { name: /Settlement policy question/i });
    const row = activeItem.parentElement;
    expect(row).toBeTruthy();
    await user.click(within(row as HTMLElement).getByRole("button", { name: "Delete session" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    expect(useSessionStore.getState().getThread("sess-active")).toBeUndefined();
    expect(useSessionStore.getState().sessionAction).toEqual({ type: "new" });
  });

  it("opens mobile drawer with dialog semantics", async () => {
    const user = userEvent.setup();
    renderWithUser(<SessionSidebar />, { sessionId: "sess-active" });

    await user.click(screen.getByRole("button", { name: "Open session history" }));
    expect(screen.getByRole("dialog", { name: "Session history" })).toBeInTheDocument();
  });
});
