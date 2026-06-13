import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ClarifyingQuestionCard } from "./ClarifyingQuestionCard";
import { DepartmentTargetBar } from "./DepartmentTargetBar";
import { renderWithUser } from "@/test/test-utils";
import type { ChatResponse } from "@/lib/types";

const clarifyResponse: ChatResponse = {
  answer: "Which department are you asking about?",
  citations: [],
  source_departments: [],
  confidence: 0.3,
  feedback_id: "fb-clarify",
  status: "refused",
  clarifying_question: {
    prompt: "Which department are you asking about?",
    options: ["risk", "grow_enablement", "bank_partnerships"],
  },
};

describe("DepartmentTargetBar", () => {
  it("shows auto-route as selected when no departments pinned", () => {
    const onChange = vi.fn();
    renderWithUser(<DepartmentTargetBar selected={[]} onChange={onChange} />);

    const autoBtn = screen.getByRole("button", { name: /Auto-route/i });
    expect(autoBtn).toHaveAttribute("aria-pressed", "true");
  });

  it("toggles department selection and calls onChange", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    renderWithUser(<DepartmentTargetBar selected={[]} onChange={onChange} />);

    await user.click(screen.getByRole("button", { name: "Risk" }));
    expect(onChange).toHaveBeenCalledWith(["risk"]);
  });

  it("clears selection when auto-route is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    renderWithUser(
      <DepartmentTargetBar selected={["risk"]} onChange={onChange} />,
    );

    await user.click(screen.getByRole("button", { name: /Auto-route/i }));
    expect(onChange).toHaveBeenCalledWith([]);
  });
});

describe("ClarifyingQuestionCard", () => {
  it("renders prompt and department options", () => {
    const onSelect = vi.fn();
    renderWithUser(
      <ClarifyingQuestionCard
        question={clarifyResponse.clarifying_question!}
        onSelect={onSelect}
      />,
    );

    expect(
      screen.getByText("Which department are you asking about?"),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Risk" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Grow Enablement" }),
    ).toBeInTheDocument();
  });

  it("calls onSelect with the chosen department", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    renderWithUser(
      <ClarifyingQuestionCard
        question={clarifyResponse.clarifying_question!}
        onSelect={onSelect}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Risk" }));
    expect(onSelect).toHaveBeenCalledWith("risk");
  });
});

describe("useChat FR-1 wiring", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it("sends target_departments and user context headers on chat", async () => {
    const chatMock = vi.fn().mockResolvedValue({
      answer: "ok",
      citations: [],
      source_departments: ["risk"],
      confidence: 0.9,
      feedback_id: "fb-1",
      status: "answered",
    });
    vi.doMock("@/lib/apiClient", () => ({
      api: { chat: chatMock },
      ApiError: class ApiError extends Error {},
    }));

    const { useChat } = await import("@/hooks/useChat");
    const { getUserContext } = await import("@/store/userStore");

    function ChatProbe() {
      const { sendMessage, setTargetDepartments } = useChat();
      return (
        <div>
          <button type="button" onClick={() => setTargetDepartments(["risk"])}>
            pin
          </button>
          <button type="button" onClick={() => sendMessage("Pinned question?")}>
            send
          </button>
        </div>
      );
    }

    const user = userEvent.setup();
    renderWithUser(<ChatProbe />);
    await user.click(screen.getByRole("button", { name: "pin" }));
    await user.click(screen.getByRole("button", { name: "send" }));

    await waitFor(() => {
      expect(chatMock).toHaveBeenCalledWith(
        {
          question: "Pinned question?",
          target_departments: ["risk"],
        },
        getUserContext(),
      );
    });
  });
});
