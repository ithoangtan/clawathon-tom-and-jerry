import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ConflictPanel } from "./ConflictPanel";
import type { Conflict } from "@/lib/types";
import { renderWithUser } from "@/test/test-utils";

const conflicts: Conflict[] = [
  {
    topic: "Escalation SLA for Level 2 incidents",
    sides: [
      {
        department: "risk",
        statement: "Level 2 must be resolved within 4 hours.",
        citation: {
          title: "Risk Escalation Policy",
          url: "https://confluence.example.com/risk",
        },
      },
      {
        department: "bank_partnerships",
        statement: "Level 2 SLA is 8 business hours.",
        citation: {
          title: "Partner Onboarding Guide",
          url: "https://confluence.example.com/bank",
        },
      },
    ],
  },
];

describe("ConflictPanel", () => {
  it("returns null when conflicts array is empty", () => {
    const { container } = renderWithUser(<ConflictPanel conflicts={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders conflict region with topic and department sides", () => {
    renderWithUser(<ConflictPanel conflicts={conflicts} />);

    expect(
      screen.getByRole("region", { name: "Conflicting sources detected" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Conflict 1 of 1")).toBeInTheDocument();
    expect(screen.getByText("Escalation SLA for Level 2 incidents")).toBeInTheDocument();
    expect(screen.getByText("Level 2 must be resolved within 4 hours.")).toBeInTheDocument();
    expect(screen.getByText("Level 2 SLA is 8 business hours.")).toBeInTheDocument();
    expect(screen.getByText("Risk")).toBeInTheDocument();
    expect(screen.getByText("Bank Partnerships")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Risk Escalation Policy" })).toHaveAttribute(
      "href",
      "https://confluence.example.com/risk",
    );
  });

  it("renders Vietnamese copy and department labels", () => {
    renderWithUser(<ConflictPanel conflicts={conflicts} />, { locale: "vi" });

    expect(screen.getByText("Phát hiện nguồn mâu thuẫn")).toBeInTheDocument();
    expect(screen.getByText("Mâu thuẫn 1/1")).toBeInTheDocument();
    expect(screen.getByText("Quản lý Rủi ro")).toBeInTheDocument();
    expect(screen.getByText("Đối tác Ngân hàng")).toBeInTheDocument();
  });

  it("applies department accent colors on side borders", () => {
    const { container } = renderWithUser(<ConflictPanel conflicts={conflicts} />);
    const bordered = container.querySelectorAll("[style*='border-color']");
    expect(bordered.length).toBeGreaterThanOrEqual(2);
    const colors = Array.from(bordered).map((el) => (el as HTMLElement).style.borderColor);
    expect(colors).toContain("rgb(230, 57, 70)");
    expect(colors).toContain("rgb(69, 123, 157)");
  });
});
