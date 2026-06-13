import { describe, expect, it } from "vitest";
import { normalizeAdminSyncPayload } from "./adminSyncAdapter";

describe("normalizeAdminSyncPayload", () => {
  it("returns empty arrays for null/undefined", () => {
    expect(normalizeAdminSyncPayload(null)).toEqual({
      running: false,
      departments: [],
      recent_jobs: [],
      sources: [],
    });
  });

  it("preserves legacy flat payloads", () => {
    const legacy = {
      running: true,
      departments: [],
      recent_jobs: [],
      sources: [
        {
          source: "confluence",
          state: "running" as const,
          doc_count: 1,
          chunk_count: 2,
          errors: [],
        },
      ],
    };
    expect(normalizeAdminSyncPayload(legacy)).toEqual(legacy);
  });

  it("maps wire status + history into UI shape", () => {
    const wire = {
      jobs: {
        confluence: {
          job_id: "job-1",
          status: "running" as const,
          started_at: "2026-06-13T00:00:00Z",
          finished_at: null,
          last_success_at: null,
          target_department: "risk" as const,
          doc_count: 0,
          chunk_count: 0,
          errors: [],
          progress: { pages: 3 },
          departments: [
            {
              department: "risk" as const,
              space_key: "RISK",
              status: "running" as const,
              page_count: 3,
              chunk_count: 0,
              errors: [],
            },
          ],
        },
        gdrive: {
          status: "pending" as const,
          doc_count: 0,
          chunk_count: 0,
          errors: [],
          departments: [],
        },
      },
      departments_indexed: {
        risk: { chunk_count: 10, doc_count: 2, has_data: true },
        grow_enablement: { chunk_count: 0, doc_count: 0, has_data: false },
        bank_partnerships: { chunk_count: 0, doc_count: 0, has_data: false },
      },
    };

    const history = [
      {
        job_id: "job-0",
        source: "confluence",
        status: "success" as const,
        started_at: "2026-06-12T00:00:00Z",
        finished_at: "2026-06-12T00:05:00Z",
        department: null,
        doc_count: 12,
        chunk_count: 40,
        errors: [],
        departments: [],
      },
    ];

    const result = normalizeAdminSyncPayload(wire, history);

    expect(result.running).toBe(true);
    expect(result.sources).toHaveLength(2);
    expect(result.sources[0]).toMatchObject({
      source: "confluence",
      state: "running",
      progress: { pages: 3 },
    });
    expect(result.sources[1]).toMatchObject({ source: "gdrive", state: "idle" });

    expect(result.departments).toHaveLength(3);
    const risk = result.departments.find((d) => d.department === "risk");
    expect(risk).toMatchObject({
      state: "running",
      space_key: "RISK",
      page_count: 3,
      doc_count: 2,
      progress: { pages: 3 },
    });

    expect(result.recent_jobs).toHaveLength(1);
    expect(result.recent_jobs[0]).toMatchObject({
      id: "job-0",
      state: "success",
      pages_synced: 12,
    });
  });

  it("handles wire payloads with missing jobs and indexed departments", () => {
    const result = normalizeAdminSyncPayload({ jobs: {}, departments_indexed: {} });
    expect(result.departments).toHaveLength(3);
    expect(result.sources).toHaveLength(2);
    expect(result.running).toBe(false);
  });
});
