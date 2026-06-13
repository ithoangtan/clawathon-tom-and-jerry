import { MarkdownRenderer } from "@/components/markdown/MarkdownRenderer";
import { renderWithUser } from "@/test/test-utils";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { Citation } from "@/lib/types";

const baseCitation: Citation = {
  title: "Settlement Runbook",
  url: "https://confluence.example.com/runbook",
  section: "Overview",
  source_type: "confluence",
  last_modified: "2024-03-01T12:00:00.000Z",
  deprecated: false,
  lifecycle_state: "active",
};

describe("MarkdownRenderer", () => {
  it("renders headings, lists, and blockquotes", () => {
    const md = `# Title\n\n## Section\n\n- Item one\n- Item two\n\n> A quoted note`;
    renderWithUser(<MarkdownRenderer content={md} />);

    expect(screen.getByRole("heading", { level: 1, name: "Title" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Section" })).toBeInTheDocument();
    expect(screen.getByText("Item one")).toBeInTheDocument();
    expect(screen.getByText("A quoted note")).toBeInTheDocument();
  });

  it("renders GFM tables and strikethrough", () => {
    const md = `| Col A | Col B |\n| --- | --- |\n| a | b |\n\n~~removed~~`;
    renderWithUser(<MarkdownRenderer content={md} />);

    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByText("removed")).toBeInTheDocument();
    expect(screen.getByText("removed").closest("del")).toBeInTheDocument();
  });

  it("renders code blocks with language label and copy button", async () => {
    const user = userEvent.setup();
    const md = "```python\nprint('hello')\n```";
    renderWithUser(<MarkdownRenderer content={md} />);

    expect(screen.getByText("Python")).toBeInTheDocument();
    const codeEl = document.querySelector("code.language-python");
    expect(codeEl).toBeTruthy();
    expect(within(codeEl as HTMLElement).getByText("print")).toBeInTheDocument();
    expect(within(codeEl as HTMLElement).getByText("'hello'")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Copy code" }));
    expect(await screen.findByRole("button", { name: "Copied!" })).toBeInTheDocument();
  });

  it("renders inline code", () => {
    const md = "Use `kubectl apply` to deploy.";
    renderWithUser(<MarkdownRenderer content={md} />);
    expect(screen.getByText("kubectl apply")).toBeInTheDocument();
  });

  it("opens external links safely", () => {
    const md = "[Docs](https://example.com/docs)";
    renderWithUser(<MarkdownRenderer content={md} />);
    const link = screen.getByRole("link", { name: "Docs" });
    expect(link).toHaveAttribute("href", "https://example.com/docs");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("turns [n] markers into citation links", () => {
    const md = "See policy details [1] for more.";
    renderWithUser(<MarkdownRenderer content={md} citations={[baseCitation]} />);
    const link = screen.getByRole("link", { name: /Citation 1/ });
    expect(link).toHaveAttribute("href", baseCitation.url);
  });

  it("turns [n] markers into buttons when onCitationClick is set", async () => {
    const user = userEvent.setup();
    const onCitationClick = vi.fn();
    const md = "See policy details [1] for more.";
    renderWithUser(
      <MarkdownRenderer
        content={md}
        citations={[baseCitation]}
        onCitationClick={onCitationClick}
      />,
    );
    await user.click(screen.getByRole("button", { name: /Citation 1/ }));
    expect(onCitationClick).toHaveBeenCalledWith(1);
  });
});
