import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { AnswerCard } from "./AnswerCard";
import { ConfidenceBadge, DepartmentChip } from "./Badges";
import { CitationList } from "./CitationList";
import { StalenessBadge } from "./StalenessBadge";
import type { Citation } from "@/lib/types";
import { renderWithUser } from "@/test/test-utils";

const baseCitation: Citation = {
  title: "Settlement Runbook",
  url: "https://confluence.example.com/runbook",
  section: "Overview",
  source_type: "confluence",
  last_modified: "2024-03-01T12:00:00.000Z",
  deprecated: false,
  lifecycle_state: "active",
};

describe("ConfidenceBadge", () => {
  it("renders answered status and confidence", () => {
    renderWithUser(<ConfidenceBadge confidence={0.92} status="answered" />);
    expect(screen.getByText("Answered")).toBeInTheDocument();
    expect(screen.getByText(/Confidence: 92%/)).toBeInTheDocument();
  });

  it("renders partial status with warning tone", () => {
    renderWithUser(<ConfidenceBadge confidence={0.5} status="partial" />);
    expect(screen.getByText("Partial answer")).toBeInTheDocument();
  });

  it("renders refused status in Vietnamese", () => {
    renderWithUser(<ConfidenceBadge confidence={0.1} status="refused" />, { locale: "vi" });
    expect(screen.getByText("Không có thông tin trong tài liệu")).toBeInTheDocument();
  });
});

describe("DepartmentChip", () => {
  it("renders department label with accent color", () => {
    renderWithUser(<DepartmentChip deptKey="risk" />);
    const chip = screen.getByText("Risk");
    expect(chip).toBeInTheDocument();
    expect(chip).toHaveStyle({ backgroundColor: "#E63946" });
  });

  it("renders Vietnamese department name", () => {
    renderWithUser(<DepartmentChip deptKey="bank_partnerships" />, { locale: "vi" });
    expect(screen.getByText("Đối tác Ngân hàng")).toBeInTheDocument();
  });
});

describe("StalenessBadge", () => {
  it("returns null for active citations", () => {
    const { container } = renderWithUser(<StalenessBadge citation={baseCitation} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows deprecated warning when citation is deprecated", () => {
    const citation: Citation = {
      ...baseCitation,
      deprecated: true,
      successor_url: "https://confluence.example.com/v2",
    };
    renderWithUser(<StalenessBadge citation={citation} />);
    expect(screen.getByRole("note")).toBeInTheDocument();
    expect(screen.getByText("Deprecated document")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /See updated version/ })).toHaveAttribute(
      "href",
      "https://confluence.example.com/v2",
    );
  });

  it("shows warning for lifecycle_state deprecated", () => {
    const citation: Citation = {
      ...baseCitation,
      lifecycle_state: "deprecated",
    };
    renderWithUser(<StalenessBadge citation={citation} />, { locale: "vi" });
    expect(screen.getByRole("note")).toHaveTextContent("Tài liệu đã lỗi thời");
  });
});

describe("CitationList", () => {
  const citations: Citation[] = [
    baseCitation,
    {
      ...baseCitation,
      title: "KYC Policy",
      url: "https://drive.example.com/kyc.pdf",
      page: 3,
      source_type: "gdrive",
    },
    {
      ...baseCitation,
      title: "Risk Escalation",
      url: "https://confluence.example.com/risk",
      deprecated: true,
      successor_url: "https://confluence.example.com/risk-v2",
    },
    {
      ...baseCitation,
      title: "Partner SLA",
      url: "https://confluence.example.com/sla",
    },
  ];

  it("renders citation badges with index numbers", () => {
    renderWithUser(<CitationList citations={citations.slice(0, 2)} collapsible={false} />);
    expect(screen.getByRole("region", { name: "Sources" })).toBeInTheDocument();
    expect(screen.getByText("Sources (2)")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Settlement Runbook" })).toBeInTheDocument();
    const kycCard = screen.getByRole("link", { name: "KYC Policy" }).closest("li");
    expect(kycCard).toBeTruthy();
    expect(within(kycCard as HTMLElement).getByText(/Page:/)).toBeInTheDocument();
    expect(within(kycCard as HTMLElement).getByText("3")).toBeInTheDocument();
    const region = screen.getByRole("region", { name: "Sources" });
    expect(within(region).getAllByText(/Section:/)).toHaveLength(2);
    expect(within(region).getAllByText(/Updated:/)).toHaveLength(2);
  });

  it("collapses to three citations and expands on click", async () => {
    const user = userEvent.setup();
    const { container } = renderWithUser(<CitationList citations={citations} />);

    const links = screen.getAllByRole("link", { name: "Settlement Runbook" });
    expect(links).toHaveLength(1);
    expect(screen.queryByRole("link", { name: "Partner SLA" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Show all sources" }));
    expect(container.querySelectorAll('a[href="https://confluence.example.com/sla"]')).toHaveLength(1);
    expect(screen.getByText("Deprecated document")).toBeInTheDocument();
  });

  it("returns null when citations array is empty", () => {
    const { container } = renderWithUser(<CitationList citations={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe("AnswerCard", () => {
  const answeredResponse = {
    answer: "Policy requires approval [1].",
    citations: [baseCitation],
    source_departments: ["risk" as const],
    confidence: 0.88,
    feedback_id: "fb-1",
    status: "answered" as const,
  };

  it("renders markdown answer with copy button and citations", async () => {
    const user = userEvent.setup();
    renderWithUser(<AnswerCard response={answeredResponse} />);

    expect(screen.getByText(/Policy requires approval/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy response" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Settlement Runbook" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Copy response" }));
    expect(await screen.findByRole("button", { name: "Copied!" })).toBeInTheDocument();
  });

  it("shows refusal panel without citations when status is refused", () => {
    renderWithUser(
      <AnswerCard
        response={{
          ...answeredResponse,
          answer: "Not covered in the docs.\n\nNo relevant content found.",
          citations: [],
          source_departments: [],
          confidence: 0,
          status: "refused",
          feedback_id: "fb-2",
        }}
      />,
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Not covered in the docs" })).toBeInTheDocument();
    expect(screen.getByText(/No relevant content found/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Copy response" })).not.toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Sources" })).not.toBeInTheDocument();
  });
});
