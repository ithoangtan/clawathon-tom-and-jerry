import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { PipelineProgress } from "./PipelineProgress";
import {
  applyPipelineNodeEvent,
  completePipeline,
  createInitialPipeline,
} from "@/lib/pipelineSteps";
import { renderWithUser } from "@/test/test-utils";

describe("PipelineProgress", () => {
  it("renders BE step_label when provided", () => {
    let progress = createInitialPipeline();
    progress = applyPipelineNodeEvent(progress, {
      node: "router",
      step_key: "router",
      step_label: "Routing to departments",
    });
    progress = applyPipelineNodeEvent(progress, {
      node: "dept_subgraph",
      step_key: "retrieve",
      step_label: "Searching internal documents",
      departments: ["risk", "bank_partnerships"],
    });

    renderWithUser(<PipelineProgress progress={progress} />);

    expect(screen.getByText("Routing to departments")).toBeInTheDocument();
    expect(screen.getByText("Searching internal documents")).toBeInTheDocument();
    expect(screen.getByText("Risk")).toBeInTheDocument();
    expect(screen.getByText("Bank Partnerships")).toBeInTheDocument();
    expect(screen.getByText(/Thinking/i)).toBeInTheDocument();
  });

  it("renders vertical stepper with active step labels", () => {
    let progress = createInitialPipeline();
    progress = applyPipelineNodeEvent(progress, { node: "router" });
    progress = applyPipelineNodeEvent(progress, {
      node: "retrieve",
      departments: ["risk", "bank_partnerships"],
    });

    renderWithUser(<PipelineProgress progress={progress} />);

    expect(screen.getByText("Agent Center routing")).toBeInTheDocument();
    expect(screen.getByText("Per-department retrieval")).toBeInTheDocument();
    expect(screen.getByText("Risk")).toBeInTheDocument();
    expect(screen.getByText("Bank Partnerships")).toBeInTheDocument();
    expect(screen.getByText(/Thinking/i)).toBeInTheDocument();
  });

  it("shows collapsed summary after completion", () => {
    const progress = completePipeline(createInitialPipeline(), {
      now: 4_200,
      totalElapsedMs: 4_200,
      departments: ["risk", "grow_enablement"],
      departmentCount: 2,
    });

    renderWithUser(<PipelineProgress progress={progress} />);
    expect(screen.getByText(/Processed in 4.2s · 2 departments/i)).toBeInTheDocument();
  });

  it("calls onCollapsedDismiss after timeout", () => {
    vi.useFakeTimers();
    const onCollapsedDismiss = vi.fn();
    const progress = completePipeline(createInitialPipeline(), {
      now: 2_000,
      totalElapsedMs: 2_000,
      departments: ["risk"],
      departmentCount: 1,
    });

    renderWithUser(
      <PipelineProgress progress={progress} onCollapsedDismiss={onCollapsedDismiss} />,
    );

    vi.advanceTimersByTime(3_000);
    expect(onCollapsedDismiss).toHaveBeenCalled();
    vi.useRealTimers();
  });
});
