import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RefusalPanel } from "./RefusalPanel";
import { renderWithUser } from "@/test/test-utils";

describe("RefusalPanel", () => {
  it("renders doc-not-found refusal with amber styling", () => {
    renderWithUser(
      <RefusalPanel message="No relevant content found for this topic." />,
    );

    const alert = screen.getByRole("alert");
    expect(alert).toHaveClass("border-amber-200/90");
    expect(screen.getByRole("heading", { name: "Not covered in the docs" })).toBeInTheDocument();
    expect(screen.getByText(/No relevant content found/)).toBeInTheDocument();
    expect(
      screen.getByText(/Try rephrasing your question or contact the document owner/i),
    ).toBeInTheDocument();
  });

  it("renders access_denied refusal with rose styling and distinct copy", () => {
    renderWithUser(
      <RefusalPanel
        message="You cannot query Risk department documents."
        reason="access_denied"
      />,
    );

    const alert = screen.getByRole("alert");
    expect(alert).toHaveClass("border-rose-200/90");
    expect(screen.getByRole("heading", { name: "Access denied" })).toBeInTheDocument();
    expect(screen.getByText(/You cannot query Risk department documents/)).toBeInTheDocument();
    expect(
      screen.getByText(/Your role cannot query this department's knowledge/i),
    ).toBeInTheDocument();
  });

  it("renders Vietnamese access denial copy", () => {
    renderWithUser(
      <RefusalPanel message="Không có quyền." reason="access_denied" />,
      { locale: "vi" },
    );

    expect(screen.getByRole("heading", { name: "Không có quyền truy cập" })).toBeInTheDocument();
    expect(
      screen.getByText(/Vai trò của bạn không được phép truy vấn tài liệu bộ phận này/i),
    ).toBeInTheDocument();
  });

  it("renders out_of_scope refusal with distinct title and escalation body", () => {
    renderWithUser(
      <RefusalPanel
        message={
          "This question is outside indexed documentation (e.g. live or real-time data).\n\n" +
          "**Next step — ask a human:**\n- **Risk**: Teams channel `teams-risk-knowledge`"
        }
        reason="out_of_scope"
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Outside indexed documentation" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/live or real-time data/i)).toBeInTheDocument();
    expect(screen.getByText(/teams-risk-knowledge/)).toBeInTheDocument();
    expect(
      screen.getByText(/I only answer from internal docs/i),
    ).toBeInTheDocument();
  });

  it("strips duplicate lead line when body repeats the refusal title", () => {
    renderWithUser(
      <RefusalPanel message="Not covered in the docs.\n\nNo relevant content found for this topic." />,
    );

    expect(screen.getByRole("heading", { name: "Not covered in the docs" })).toBeInTheDocument();
    expect(screen.getByText(/No relevant content found/)).toBeInTheDocument();
    expect(screen.getAllByText("Not covered in the docs")).toHaveLength(1);
  });
});
