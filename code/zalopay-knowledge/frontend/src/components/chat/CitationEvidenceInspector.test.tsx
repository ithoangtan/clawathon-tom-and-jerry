import { CitationEvidenceInspector } from "@/components/chat/CitationEvidenceInspector";
import { renderWithUser } from "@/test/test-utils";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { Citation } from "@/lib/types";

const citations: Citation[] = [
  {
    title: "Settlement Runbook",
    url: "https://confluence.example.com/runbook",
    excerpt: "Settlement must be reconciled daily with partner banks.",
    source_type: "confluence",
    lifecycle_state: "active",
    last_modified: "2024-03-01T12:00:00.000Z",
    section: "Overview",
  },
  {
    title: "Legacy Policy",
    url: "https://confluence.example.com/old",
    excerpt: "Deprecated guidance.",
    source_type: "confluence",
    deprecated: true,
    successor_url: "https://confluence.example.com/new",
    last_modified: "2023-01-01T12:00:00.000Z",
  },
];

describe("CitationEvidenceInspector", () => {
  it("renders excerpt, badges, and open CTA in panel mode", () => {
    renderWithUser(
      <CitationEvidenceInspector
        state={{ citations, selectedIndex: 1 }}
        open
        variant="panel"
        onClose={() => {}}
        onSelectIndex={() => {}}
      />,
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Settlement must be reconciled daily with partner banks.")).toBeInTheDocument();
    expect(screen.getByText("Confluence")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open in Confluence" })).toBeInTheDocument();
  });

  it("shows deprecated banner and successor link", () => {
    renderWithUser(
      <CitationEvidenceInspector
        state={{ citations, selectedIndex: 2 }}
        open
        variant="panel"
        onClose={() => {}}
        onSelectIndex={() => {}}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Deprecated document");
    expect(screen.getByRole("link", { name: /See updated version/ })).toHaveAttribute(
      "href",
      "https://confluence.example.com/new",
    );
    expect(screen.getByText("Deprecated")).toBeInTheDocument();
  });

  it("calls onClose and onSelectIndex", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    const onSelectIndex = vi.fn();

    renderWithUser(
      <CitationEvidenceInspector
        state={{ citations, selectedIndex: 1 }}
        open
        variant="panel"
        onClose={onClose}
        onSelectIndex={onSelectIndex}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Close evidence panel" }));
    expect(onClose).toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "View source 2" }));
    expect(onSelectIndex).toHaveBeenCalledWith(2);
  });
});
