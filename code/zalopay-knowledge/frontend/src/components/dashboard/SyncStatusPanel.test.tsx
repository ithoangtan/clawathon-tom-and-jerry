import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SyncStatusPanel } from "./SyncStatusPanel";
import { renderWithUser } from "@/test/test-utils";

const refreshMock = vi.fn();

vi.mock("@/hooks/useSyncStatus", () => ({
  useSyncStatus: vi.fn(),
}));

import { useSyncStatus } from "@/hooks/useSyncStatus";

const mockedUseSyncStatus = vi.mocked(useSyncStatus);

describe("SyncStatusPanel", () => {
  it("shows loading spinner on initial fetch", () => {
    mockedUseSyncStatus.mockReturnValue({
      status: null,
      error: null,
      loading: true,
      refresh: refreshMock,
    });

    renderWithUser(<SyncStatusPanel />);
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("shows never-synced message when sources are empty", () => {
    mockedUseSyncStatus.mockReturnValue({
      status: { sources: [] },
      error: null,
      loading: false,
      refresh: refreshMock,
    });

    renderWithUser(<SyncStatusPanel />);
    expect(screen.getByText("Never synced")).toBeInTheDocument();
  });

  it("renders source cards with counts and errors", () => {
    mockedUseSyncStatus.mockReturnValue({
      status: {
        sources: [
          {
            source: "confluence",
            state: "error",
            doc_count: 120,
            chunk_count: 450,
            last_success_at: "2024-06-01T10:00:00.000Z",
            freshness_hours: 12,
            progress: null,
            errors: ["Rate limit exceeded"],
          },
        ],
      },
      error: null,
      loading: false,
      refresh: refreshMock,
    });

    renderWithUser(<SyncStatusPanel />);

    expect(screen.getByRole("heading", { name: "Confluence" })).toBeInTheDocument();
    expect(screen.getByText("error")).toBeInTheDocument();
    expect(screen.getByText("120")).toBeInTheDocument();
    expect(screen.getByText("450")).toBeInTheDocument();
    expect(screen.getByText("Rate limit exceeded")).toBeInTheDocument();
  });

  it("shows error state with retry", async () => {
    const user = userEvent.setup();
    mockedUseSyncStatus.mockReturnValue({
      status: null,
      error: "Sync status unavailable",
      loading: false,
      refresh: refreshMock,
    });

    renderWithUser(<SyncStatusPanel />);
    expect(screen.getByRole("alert")).toHaveTextContent("Sync status unavailable");

    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(refreshMock).toHaveBeenCalled();
  });
});
