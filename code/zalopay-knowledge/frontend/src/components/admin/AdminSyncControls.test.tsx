import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AdminSyncControls } from "./AdminSyncControls";
import { renderWithUser } from "@/test/test-utils";

const refreshMock = vi.fn();

vi.mock("@/hooks/useAdminSyncStatus", () => ({
  useAdminSyncStatus: vi.fn(),
}));

vi.mock("@/hooks/useHealth", () => ({
  useHealth: () => ({
    refresh: vi.fn(),
    health: null,
    error: null,
    loading: false,
  }),
}));

import { useAdminSyncStatus } from "@/hooks/useAdminSyncStatus";

const mockedUseAdminSyncStatus = vi.mocked(useAdminSyncStatus);

describe("AdminSyncControls", () => {
  it("renders without crashing when status omits sources and departments", () => {
    mockedUseAdminSyncStatus.mockReturnValue({
      status: {
        running: false,
      } as ReturnType<typeof useAdminSyncStatus>["status"],
      error: null,
      loading: false,
      refresh: refreshMock,
    });

    renderWithUser(<AdminSyncControls />);

    expect(screen.getByRole("button", { name: "Sync all departments" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sync Risk" })).toBeInTheDocument();
  });

  it("disables sync-all when a source is running", () => {
    mockedUseAdminSyncStatus.mockReturnValue({
      status: {
        running: false,
        sources: [
          {
            source: "confluence",
            state: "running",
            doc_count: 0,
            chunk_count: 0,
            last_success_at: null,
            freshness_hours: null,
            progress: null,
            errors: [],
          },
        ],
        departments: [],
        recent_jobs: [],
      },
      error: null,
      loading: false,
      refresh: refreshMock,
    });

    renderWithUser(<AdminSyncControls />);

    expect(screen.getByRole("button", { name: "Syncing…" })).toBeDisabled();
  });
});
