import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Badge } from "./Badge";
import { Button } from "./Button";
import { Card } from "./Card";
import { FreshnessBadge } from "./FreshnessBadge";
import { LoadingSpinner } from "./LoadingSpinner";
import { EmptyState, ErrorState } from "./StateViews";
import { renderWithUser } from "@/test/test-utils";

describe("Badge", () => {
  it("renders children with default tone", () => {
    render(<Badge>Default</Badge>);
    const badge = screen.getByText("Default");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute("data-tone", "default");
  });

  it("applies tone classes", () => {
    render(<Badge tone="success">OK</Badge>);
    expect(screen.getByText("OK")).toHaveAttribute("data-tone", "success");
  });

  it("merges custom className", () => {
    render(<Badge className="custom-class">Tagged</Badge>);
    expect(screen.getByText("Tagged")).toHaveClass("custom-class");
  });
});

describe("Button", () => {
  it("renders label and handles click", async () => {
    const user = userEvent.setup();
    let clicked = false;
    render(<Button onClick={() => { clicked = true; }}>Click me</Button>);
    await user.click(screen.getByRole("button", { name: "Click me" }));
    expect(clicked).toBe(true);
  });

  it("disables when loading", () => {
    render(<Button loading>Save</Button>);
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });

  it("applies variant styles", () => {
    render(<Button variant="danger">Delete</Button>);
    expect(screen.getByRole("button", { name: "Delete" })).toHaveClass("bg-red-600");
  });
});

describe("Card", () => {
  it("renders children with default padding", () => {
    render(<Card>Content</Card>);
    expect(screen.getByText("Content")).toHaveClass("p-5");
  });

  it("supports padding variants", () => {
    render(<Card padding="lg">Large</Card>);
    expect(screen.getByText("Large")).toHaveClass("p-6");
  });
});

describe("FreshnessBadge", () => {
  it("shows never synced when no last success", () => {
    renderWithUser(<FreshnessBadge lastSuccessAt={null} freshnessHours={null} />);
    expect(screen.getByText("Never synced")).toBeInTheDocument();
  });

  it("shows fresh with hours when recently synced", () => {
    renderWithUser(<FreshnessBadge lastSuccessAt="2024-01-01" freshnessHours={5} />);
    expect(screen.getByText(/Fresh/)).toBeInTheDocument();
    expect(screen.getByText(/5h ago/)).toBeInTheDocument();
  });

  it("shows stale label in Vietnamese", () => {
    renderWithUser(
      <FreshnessBadge lastSuccessAt="2024-01-01" freshnessHours={48} />,
      { locale: "vi" },
    );
    expect(screen.getByText(/Cũ/)).toBeInTheDocument();
  });
});

describe("LoadingSpinner", () => {
  it("renders default loading label", () => {
    renderWithUser(<LoadingSpinner />);
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("renders custom label", () => {
    renderWithUser(<LoadingSpinner label="Fetching data" />);
    expect(screen.getByText("Fetching data")).toBeInTheDocument();
  });
});

describe("EmptyState", () => {
  it("renders title and description", () => {
    render(<EmptyState title="No data" description="Try again later" />);
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByText("No data")).toBeInTheDocument();
    expect(screen.getByText("Try again later")).toBeInTheDocument();
  });
});

describe("ErrorState", () => {
  it("renders message and retry button", async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    renderWithUser(<ErrorState message="Failed to load" onRetry={onRetry} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Failed to load");
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });
});
