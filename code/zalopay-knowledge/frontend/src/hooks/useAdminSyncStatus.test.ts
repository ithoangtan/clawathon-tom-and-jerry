import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAdminSyncStatus } from "./useAdminSyncStatus";
import { api } from "@/lib/apiClient";

vi.mock("@/lib/apiClient", () => ({
  api: {
    adminSyncStatus: vi.fn(),
    adminSyncHistory: vi.fn(),
  },
}));

const mockedAdminSyncStatus = vi.mocked(api.adminSyncStatus);
const mockedAdminSyncHistory = vi.mocked(api.adminSyncHistory);

const wireStatus = {
  jobs: {
    confluence: {
      status: "pending" as const,
      doc_count: 0,
      chunk_count: 0,
      errors: [],
      departments: [],
    },
  },
  departments_indexed: {
    risk: { chunk_count: 0, doc_count: 0, has_data: false },
    grow_enablement: { chunk_count: 0, doc_count: 0, has_data: false },
    bank_partnerships: { chunk_count: 0, doc_count: 0, has_data: false },
  },
};

describe("useAdminSyncStatus", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAdminSyncStatus.mockResolvedValue(wireStatus);
    mockedAdminSyncHistory.mockResolvedValue({ entries: [] });
  });

  it("normalizes wire API payloads with empty history", async () => {
    const { result } = renderHook(() => useAdminSyncStatus());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.status).toMatchObject({
      running: false,
      recent_jobs: [],
    });
    expect(result.current.status?.departments).toHaveLength(3);
    expect(result.current.status?.sources).toHaveLength(2);
    expect(result.current.error).toBeNull();
  });

  it("includes recent jobs from history endpoint", async () => {
    mockedAdminSyncHistory.mockResolvedValue({
      entries: [
        {
          job_id: "job-1",
          source: "confluence",
          status: "success",
          started_at: "2026-06-13T00:00:00Z",
          finished_at: "2026-06-13T00:01:00Z",
          doc_count: 5,
          errors: [],
          departments: [],
        },
      ],
    });

    const { result } = renderHook(() => useAdminSyncStatus());

    await waitFor(() => {
      expect(result.current.status?.recent_jobs).toHaveLength(1);
    });

    expect(result.current.status?.recent_jobs[0]).toMatchObject({
      id: "job-1",
      state: "success",
      pages_synced: 5,
    });
  });

  it("continues when history fetch fails", async () => {
    mockedAdminSyncHistory.mockRejectedValue(new Error("history unavailable"));

    const { result } = renderHook(() => useAdminSyncStatus());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBeNull();
    expect(result.current.status?.recent_jobs).toEqual([]);
  });

  it("refresh can be called after initial load", async () => {
    const { result } = renderHook(() => useAdminSyncStatus());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.refresh();
    });

    expect(mockedAdminSyncStatus).toHaveBeenCalledTimes(2);
    expect(mockedAdminSyncHistory).toHaveBeenCalledTimes(2);
  });
});
