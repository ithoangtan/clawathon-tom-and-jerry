import type { Department } from "./types";

/** Canonical UI steps for the LangGraph pipeline progress stepper. */
export type PipelineStepId =
  | "routing"
  | "retrieval"
  | "grade"
  | "verify"
  | "synthesis";

export type StepStatus = "pending" | "active" | "done";

export interface PipelineStepState {
  id: PipelineStepId;
  status: StepStatus;
  startedAt?: number;
  completedAt?: number;
  /** Elapsed ms for this step (from BE or derived). */
  elapsedMs?: number;
  /** BE `step_label` when provided; UI falls back to i18n. */
  label?: string;
}

export interface DeptBranchState {
  department: Department;
  status: StepStatus;
}

export type PipelinePhase = "running" | "collapsed" | "hidden";

export interface PipelineProgressState {
  startedAt: number;
  completedAt?: number;
  totalElapsedMs?: number;
  departmentCount: number;
  steps: PipelineStepState[];
  departments: Department[];
  deptBranches: Record<string, DeptBranchState>;
  phase: PipelinePhase;
  /** Raw node name from the latest SSE event (fallback label). */
  lastNode?: string;
  /** Latest BE `step_label` from SSE (fallback for live status). */
  lastStepLabel?: string;
  /** True once a structured ``pipeline`` SSE event has been applied. */
  usesPipelineEvents?: boolean;
  /** `${step_key}:${department}` completions for parallel dept branches. */
  deptStepCompletions?: Record<string, boolean>;
}

export const PIPELINE_STEP_ORDER: PipelineStepId[] = [
  "routing",
  "retrieval",
  "grade",
  "verify",
  "synthesis",
];

const STEP_INDEX: Record<PipelineStepId, number> = {
  routing: 0,
  retrieval: 1,
  grade: 2,
  verify: 3,
  synthesis: 4,
};

/** Optional BE `step_key` → UI step (stream_events.py + pipeline.py). */
export const STEP_KEY_TO_STEP: Record<string, PipelineStepId> = {
  ingest_context: "routing",
  router: "routing",
  retrieve: "retrieval",
  grade: "grade",
  synthesize: "verify",
  verify: "verify",
  reconcile: "synthesis",
  respond: "synthesis",
  // Legacy / alternate keys
  agent_center_routing: "routing",
  per_dept_retrieval: "retrieval",
  grade_relevance: "grade",
  claim_verification: "verify",
  answer_synthesis: "synthesis",
};

/** LangGraph node name → UI step (graceful fallback when `step_key` absent). */
export const NODE_TO_STEP: Record<string, PipelineStepId> = {
  ingest_context: "routing",
  router: "routing",
  retrieve: "retrieval",
  dept_subgraph: "retrieval",
  grade: "grade",
  synthesize: "verify",
  verify: "verify",
  reconcile: "synthesis",
  respond: "synthesis",
};

export const STEP_I18N_KEY: Record<PipelineStepId, string> = {
  routing: "pipelineStepRouting",
  retrieval: "pipelineStepRetrieval",
  grade: "pipelineStepGrade",
  verify: "pipelineStepVerify",
  synthesis: "pipelineStepSynthesis",
};

const DEPARTMENT_KEYS = new Set<string>([
  "risk",
  "grow_enablement",
  "bank_partnerships",
]);

function isDepartment(value: unknown): value is Department {
  return typeof value === "string" && DEPARTMENT_KEYS.has(value);
}

function parseDepartments(data: Record<string, unknown>): Department[] {
  const raw = data.departments;
  if (!Array.isArray(raw)) return [];
  return raw.filter(isDepartment);
}

function resolveStepId(data: Record<string, unknown>): PipelineStepId | null {
  const stepKey = data.step_key;
  if (typeof stepKey === "string" && stepKey in STEP_KEY_TO_STEP) {
    return STEP_KEY_TO_STEP[stepKey];
  }
  const node = data.node;
  if (typeof node === "string" && node in NODE_TO_STEP) {
    return NODE_TO_STEP[node];
  }
  return null;
}

function cloneSteps(steps: PipelineStepState[]): PipelineStepState[] {
  return steps.map((s) => ({ ...s }));
}

function advanceToStep(
  steps: PipelineStepState[],
  target: PipelineStepId,
  now: number,
  elapsedMs?: number,
  stepLabel?: string,
): PipelineStepState[] {
  const next = cloneSteps(steps);
  const targetIdx = STEP_INDEX[target];

  for (let i = 0; i < next.length; i++) {
    const step = next[i];
    if (i < targetIdx) {
      if (step.status !== "done") {
        step.status = "done";
        step.completedAt = step.completedAt ?? now;
        if (step.startedAt != null && step.elapsedMs == null) {
          step.elapsedMs = now - step.startedAt;
        }
      }
    } else if (i === targetIdx) {
      if (step.status === "pending") {
        step.status = "active";
        step.startedAt = now;
      }
      if (typeof elapsedMs === "number") {
        step.elapsedMs = elapsedMs;
      }
      if (stepLabel) {
        step.label = stepLabel;
      }
    } else if (step.status === "active") {
      step.status = "done";
      step.completedAt = now;
      if (step.startedAt != null && step.elapsedMs == null) {
        step.elapsedMs = now - step.startedAt;
      }
    }
  }

  return next;
}

function markAllDone(steps: PipelineStepState[], now: number): PipelineStepState[] {
  return steps.map((step) => {
    if (step.status === "done") return step;
    const completedAt = now;
    const elapsedMs =
      step.elapsedMs ??
      (step.startedAt != null ? completedAt - step.startedAt : undefined);
    return {
      ...step,
      status: "done" as const,
      completedAt,
      elapsedMs,
    };
  });
}

function deptStepCompletionKey(stepKey: string, dept: Department): string {
  return `${stepKey}:${dept}`;
}

function markDeptStepCompletion(
  completions: Record<string, boolean>,
  stepKey: string,
  departments: Department[],
): Record<string, boolean> {
  if (departments.length === 0) return completions;
  const next = { ...completions };
  for (const dept of departments) {
    next[deptStepCompletionKey(stepKey, dept)] = true;
  }
  return next;
}

function allDeptsCompletedStep(
  departments: Department[],
  stepKey: string,
  completions: Record<string, boolean>,
): boolean {
  if (departments.length === 0) return true;
  return departments.every((dept) => completions[deptStepCompletionKey(stepKey, dept)]);
}

function completeStepAt(
  steps: PipelineStepState[],
  target: PipelineStepId,
  now: number,
  elapsedMs?: number,
): PipelineStepState[] {
  const next = cloneSteps(steps);
  const step = next[STEP_INDEX[target]];
  if (!step || step.status === "done") return next;

  step.status = "done";
  step.completedAt = now;
  if (typeof elapsedMs === "number") {
    step.elapsedMs = elapsedMs;
  } else if (step.startedAt != null) {
    step.elapsedMs = now - step.startedAt;
  }
  return next;
}

const DEPT_PIPELINE_STEP_KEYS = new Set(["retrieve", "grade", "synthesize", "verify"]);

function updateDeptBranchesFromPipeline(
  branches: Record<string, DeptBranchState>,
  stepKey: string,
  phase: "start" | "end",
  departments: Department[],
): Record<string, DeptBranchState> {
  if (departments.length === 0 || !DEPT_PIPELINE_STEP_KEYS.has(stepKey)) {
    return branches;
  }

  const next: Record<string, DeptBranchState> = { ...branches };
  for (const dept of departments) {
    const prev = next[dept];
    if (phase === "start") {
      next[dept] = { department: dept, status: "active" };
    } else if (stepKey === "verify") {
      next[dept] = { department: dept, status: "done" };
    } else {
      next[dept] = { department: dept, status: prev?.status === "done" ? "done" : "active" };
    }
  }
  return next;
}

function parsePipelinePhase(value: unknown): "start" | "end" | null {
  return value === "start" || value === "end" ? value : null;
}

function parseStepKey(value: unknown): string | null {
  return typeof value === "string" && value in STEP_KEY_TO_STEP ? value : null;
}

function syncDeptBranches(
  branches: Record<string, DeptBranchState>,
  departments: Department[],
  activeStep: PipelineStepId | null,
): Record<string, DeptBranchState> {
  if (departments.length === 0) return branches;

  const next: Record<string, DeptBranchState> = { ...branches };
  const retrievalDone = activeStep != null && STEP_INDEX[activeStep] > STEP_INDEX.retrieval;
  const retrievalActive = activeStep === "retrieval";

  for (const dept of departments) {
    const prev = next[dept];
    let status: StepStatus = prev?.status ?? "pending";
    if (retrievalDone) {
      status = "done";
    } else if (retrievalActive) {
      status = "active";
    }
    next[dept] = { department: dept, status };
  }
  return next;
}

export function createInitialPipeline(now = Date.now()): PipelineProgressState {
  const steps: PipelineStepState[] = PIPELINE_STEP_ORDER.map((id) => ({
    id,
    status: "pending" as StepStatus,
  }));
  steps[0] = { ...steps[0], status: "active", startedAt: now };

  return {
    startedAt: now,
    departmentCount: 0,
    steps,
    departments: [],
    deptBranches: {},
    phase: "running",
  };
}

export function applyPipelineNodeEvent(
  state: PipelineProgressState,
  data: Record<string, unknown>,
  now = Date.now(),
): PipelineProgressState {
  if (state.usesPipelineEvents) {
    return state;
  }
  const stepId = resolveStepId(data);
  const incomingDepts = parseDepartments(data);
  const departments =
    incomingDepts.length > 0
      ? Array.from(new Set([...state.departments, ...incomingDepts]))
      : state.departments;

  const node = typeof data.node === "string" ? data.node : undefined;
  const elapsedMs =
    typeof data.elapsed_ms === "number" ? data.elapsed_ms : undefined;
  const stepLabel =
    typeof data.step_label === "string" ? data.step_label : undefined;

  let steps = state.steps;
  if (stepId) {
    steps = advanceToStep(steps, stepId, now, elapsedMs, stepLabel);
  }

  const activeStep =
    stepId ??
    ([...steps].reverse().find((s) => s.status === "active")?.id ?? null);

  const deptBranches = syncDeptBranches(state.deptBranches, departments, activeStep);

  return {
    ...state,
    steps,
    departments,
    deptBranches,
    departmentCount: Math.max(state.departmentCount, departments.length),
    totalElapsedMs: elapsedMs ?? state.totalElapsedMs,
    lastNode: node ?? state.lastNode,
    lastStepLabel: stepLabel ?? state.lastStepLabel,
  };
}

/** Apply a structured ``pipeline`` SSE event (start/end phases, per-dept branches). */
export function applyPipelineEvent(
  state: PipelineProgressState,
  data: Record<string, unknown>,
  now = Date.now(),
): PipelineProgressState {
  const stepKey = parseStepKey(data.step_key);
  const phase = parsePipelinePhase(data.phase);
  if (!stepKey || !phase) return { ...state, usesPipelineEvents: true };

  const stepId = STEP_KEY_TO_STEP[stepKey];
  const incomingDepts = parseDepartments(data);
  const departments =
    incomingDepts.length > 0
      ? Array.from(new Set([...state.departments, ...incomingDepts]))
      : state.departments;

  const node = typeof data.node === "string" ? data.node : undefined;
  const elapsedMs =
    typeof data.elapsed_ms === "number" ? data.elapsed_ms : undefined;
  const stepElapsedMs =
    typeof data.step_elapsed_ms === "number" ? data.step_elapsed_ms : undefined;

  let steps = state.steps;
  let deptStepCompletions = state.deptStepCompletions ?? {};

  if (phase === "start") {
    steps = advanceToStep(steps, stepId, now);
  } else {
    const scopedDepts = incomingDepts.length > 0 ? incomingDepts : departments;
    const isGlobalStep = stepKey === "router" || scopedDepts.length === 0;

    if (isGlobalStep) {
      steps = completeStepAt(steps, stepId, now, stepElapsedMs);
    } else {
      deptStepCompletions = markDeptStepCompletion(
        deptStepCompletions,
        stepKey,
        incomingDepts,
      );
      if (allDeptsCompletedStep(departments, stepKey, deptStepCompletions)) {
        steps = completeStepAt(steps, stepId, now, stepElapsedMs);
      }
    }
  }

  const deptBranches = updateDeptBranchesFromPipeline(
    state.deptBranches,
    stepKey,
    phase,
    incomingDepts,
  );

  return {
    ...state,
    steps,
    departments,
    deptBranches,
    deptStepCompletions,
    departmentCount: Math.max(state.departmentCount, departments.length),
    totalElapsedMs: elapsedMs ?? state.totalElapsedMs,
    lastNode: node ?? state.lastNode,
    usesPipelineEvents: true,
  };
}

export function completePipeline(
  state: PipelineProgressState,
  options?: {
    now?: number;
    totalElapsedMs?: number;
    departmentCount?: number;
    departments?: Department[];
  },
): PipelineProgressState {
  const now = options?.now ?? Date.now();
  const departments =
    options?.departments && options.departments.length > 0
      ? options.departments
      : state.departments;
  const departmentCount = Math.max(
    options?.departmentCount ?? 0,
    departments.length,
    state.departmentCount,
  );
  const totalElapsedMs =
    options?.totalElapsedMs ?? Math.max(0, now - state.startedAt);

  const deptBranches = syncDeptBranches(
    state.deptBranches,
    departments,
    "synthesis",
  );

  return {
    ...state,
    steps: markAllDone(state.steps, now),
    departments,
    deptBranches,
    departmentCount,
    completedAt: now,
    totalElapsedMs,
    phase: "collapsed",
  };
}

export function hidePipeline(state: PipelineProgressState): PipelineProgressState {
  return { ...state, phase: "hidden" };
}

export function formatPipelineElapsed(seconds: number): string {
  if (seconds < 10) return seconds.toFixed(1);
  return String(Math.round(seconds));
}

export function stepElapsedMs(step: PipelineStepState, now: number): number | null {
  if (typeof step.elapsedMs === "number") return step.elapsedMs;
  if (step.status === "active" && step.startedAt != null) {
    return now - step.startedAt;
  }
  if (step.status === "done" && step.startedAt != null && step.completedAt != null) {
    return step.completedAt - step.startedAt;
  }
  return null;
}
