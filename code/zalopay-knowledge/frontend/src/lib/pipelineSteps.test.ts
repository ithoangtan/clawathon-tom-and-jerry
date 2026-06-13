import { describe, expect, it } from "vitest";
import {
  applyPipelineEvent,
  applyPipelineNodeEvent,
  completePipeline,
  createInitialPipeline,
  NODE_TO_STEP,
  STEP_KEY_TO_STEP,
} from "./pipelineSteps";

describe("pipelineSteps", () => {
  it("maps LangGraph node names to UI steps", () => {
    expect(NODE_TO_STEP.router).toBe("routing");
    expect(NODE_TO_STEP.retrieve).toBe("retrieval");
    expect(NODE_TO_STEP.grade).toBe("grade");
    expect(NODE_TO_STEP.verify).toBe("verify");
    expect(NODE_TO_STEP.reconcile).toBe("synthesis");
  });

  it("maps BE stream step_key values", () => {
    expect(STEP_KEY_TO_STEP.router).toBe("routing");
    expect(STEP_KEY_TO_STEP.retrieve).toBe("retrieval");
    expect(STEP_KEY_TO_STEP.reconcile).toBe("synthesis");
    expect(STEP_KEY_TO_STEP.respond).toBe("synthesis");
  });

  it("maps legacy BE step_key values", () => {
    expect(STEP_KEY_TO_STEP.agent_center_routing).toBe("routing");
    expect(STEP_KEY_TO_STEP.per_dept_retrieval).toBe("retrieval");
    expect(STEP_KEY_TO_STEP.answer_synthesis).toBe("synthesis");
  });

  it("advances steps on node events and tracks departments", () => {
    const base = createInitialPipeline(1_000);
    const afterRouter = applyPipelineNodeEvent(
      base,
      { node: "router", departments: ["risk", "grow_enablement"] },
      1_200,
    );

    expect(afterRouter.steps.find((s) => s.id === "routing")?.status).toBe("active");
    expect(afterRouter.departments).toEqual(["risk", "grow_enablement"]);

    const afterRetrieve = applyPipelineNodeEvent(
      afterRouter,
      { node: "retrieve" },
      1_500,
    );

    expect(afterRetrieve.steps.find((s) => s.id === "routing")?.status).toBe("done");
    expect(afterRetrieve.steps.find((s) => s.id === "retrieval")?.status).toBe("active");
    expect(afterRetrieve.deptBranches.risk?.status).toBe("active");
  });

  it("prefers step_key over node when both are present", () => {
    const state = applyPipelineNodeEvent(
      createInitialPipeline(0),
      { node: "dept_subgraph", step_key: "claim_verification" },
      500,
    );
    expect(state.steps.find((s) => s.id === "verify")?.status).toBe("active");
  });

  it("uses elapsed_ms from SSE when provided", () => {
    const state = applyPipelineNodeEvent(
      createInitialPipeline(0),
      { node: "grade", elapsed_ms: 842 },
      900,
    );
    expect(state.steps.find((s) => s.id === "grade")?.elapsedMs).toBe(842);
    expect(state.totalElapsedMs).toBe(842);
  });

  it("stores step_label on the active step", () => {
    const state = applyPipelineNodeEvent(
      createInitialPipeline(0),
      {
        node: "dept_subgraph",
        step_key: "retrieve",
        step_label: "Searching internal documents",
        departments: ["risk"],
      },
      500,
    );
    expect(state.steps.find((s) => s.id === "retrieval")?.label).toBe(
      "Searching internal documents",
    );
    expect(state.lastStepLabel).toBe("Searching internal documents");
  });

  it("collapses with department count on complete", () => {
    const running = applyPipelineNodeEvent(
      createInitialPipeline(0),
      { node: "reconcile" },
      2_000,
    );
    const done = completePipeline(running, {
      now: 3_500,
      departments: ["risk"],
      departmentCount: 1,
      totalElapsedMs: 3_500,
    });

    expect(done.phase).toBe("collapsed");
    expect(done.totalElapsedMs).toBe(3_500);
    expect(done.departmentCount).toBe(1);
    expect(done.steps.every((s) => s.status === "done")).toBe(true);
  });

  it("applies pipeline start/end events for router", () => {
    const base = createInitialPipeline(1_000);
    const afterStart = applyPipelineEvent(
      base,
      { step_key: "router", phase: "start", node: "router", departments: [] },
      1_100,
    );
    expect(afterStart.steps.find((s) => s.id === "routing")?.status).toBe("active");
    expect(afterStart.usesPipelineEvents).toBe(true);

    const afterEnd = applyPipelineEvent(
      afterStart,
      {
        step_key: "router",
        phase: "end",
        node: "router",
        departments: ["risk", "grow_enablement"],
        step_elapsed_ms: 120,
      },
      1_220,
    );
    expect(afterEnd.steps.find((s) => s.id === "routing")?.status).toBe("done");
    expect(afterEnd.steps.find((s) => s.id === "routing")?.elapsedMs).toBe(120);
    expect(afterEnd.departments).toEqual(["risk", "grow_enablement"]);
  });

  it("tracks parallel dept branches via pipeline events", () => {
    let state = applyPipelineEvent(createInitialPipeline(0), {
      step_key: "router",
      phase: "end",
      node: "router",
      departments: ["risk", "bank_partnerships"],
    });

    state = applyPipelineEvent(state, {
      step_key: "retrieve",
      phase: "start",
      node: "retrieve",
      departments: ["risk"],
    });
    expect(state.deptBranches.risk?.status).toBe("active");
    expect(state.deptBranches.bank_partnerships?.status).toBeUndefined();

    state = applyPipelineEvent(state, {
      step_key: "retrieve",
      phase: "start",
      node: "retrieve",
      departments: ["bank_partnerships"],
    });
    expect(state.deptBranches.bank_partnerships?.status).toBe("active");

    state = applyPipelineEvent(state, {
      step_key: "retrieve",
      phase: "end",
      node: "retrieve",
      departments: ["risk"],
      step_elapsed_ms: 200,
    });
    expect(state.steps.find((s) => s.id === "retrieval")?.status).toBe("active");

    state = applyPipelineEvent(state, {
      step_key: "retrieve",
      phase: "end",
      node: "retrieve",
      departments: ["bank_partnerships"],
      step_elapsed_ms: 250,
    });
    expect(state.steps.find((s) => s.id === "retrieval")?.status).toBe("done");
    expect(state.steps.find((s) => s.id === "retrieval")?.elapsedMs).toBe(250);
  });

  it("ignores node events after pipeline events are received", () => {
    const withPipeline = applyPipelineEvent(createInitialPipeline(0), {
      step_key: "router",
      phase: "start",
      node: "router",
      departments: [],
    });
    const afterNode = applyPipelineNodeEvent(withPipeline, { node: "grade" }, 500);
    expect(afterNode.steps).toEqual(withPipeline.steps);
  });
});
