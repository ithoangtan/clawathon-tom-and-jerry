import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ClarifyingQuestionCard } from "./ClarifyingQuestionCard";
import { DepartmentTargetBar } from "./DepartmentTargetBar";
import { renderWithUser } from "@/test/test-utils";
import type { ChatResponse } from "@/lib/types";
import type { Department } from "@/lib/types";

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

function renderDepartmentTargetBar(
  props: Partial<{
    selected: Department[];
    autoRoute: boolean;
    onChange: (departments: Department[]) => void;
    onAutoRouteChange: (autoRoute: boolean) => void;
  }> = {},
) {
  const onChange = props.onChange ?? vi.fn();
  const onAutoRouteChange = props.onAutoRouteChange ?? vi.fn();

  return renderWithUser(
    <DepartmentTargetBar
      selected={props.selected ?? []}
      autoRoute={props.autoRoute ?? true}
      onChange={onChange}
      onAutoRouteChange={onAutoRouteChange}
    />,
  );
}

describe("DepartmentTargetBar", () => {
  it("shows auto-route chip and add button when auto-route is active", () => {
    renderDepartmentTargetBar({ autoRoute: true });

    const chip = document.querySelector(".dept-auto-route-chip");
    expect(chip).toHaveAttribute("aria-pressed", "true");
    expect(chip).toHaveTextContent(/Auto-route/i);
    expect(screen.getByRole("button", { name: /Turn off auto-route/i })).toHaveClass(
      "dept-target-tag-remove",
    );
    expect(screen.getByRole("button", { name: /Add department/i })).toBeInTheDocument();
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("turns off auto-route and opens picker when add is clicked during auto-route", async () => {
    const user = userEvent.setup();
    const onAutoRouteChange = vi.fn();
    renderDepartmentTargetBar({ autoRoute: true, onAutoRouteChange });

    await user.click(screen.getByRole("button", { name: /Add department/i }));

    expect(onAutoRouteChange).toHaveBeenCalledWith(false);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("turns off auto-route via inline remove on the active chip", async () => {
    const user = userEvent.setup();
    const onAutoRouteChange = vi.fn();
    renderDepartmentTargetBar({ autoRoute: true, onAutoRouteChange });

    await user.click(screen.getByRole("button", { name: /Turn off auto-route/i }));
    expect(onAutoRouteChange).toHaveBeenCalledWith(false);
  });

  it("opens picker modal from the add button when auto-route is off", async () => {
    const user = userEvent.setup();
    renderDepartmentTargetBar({ autoRoute: false });

    await user.click(screen.getByRole("button", { name: /Add department/i }));

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByRole("searchbox")).toBeInTheDocument();
  });

  it("adds a department from the picker and keeps the modal open", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    renderDepartmentTargetBar({ autoRoute: false, onChange });

    await user.click(screen.getByRole("button", { name: /Add department/i }));
    await user.click(screen.getByRole("button", { name: /Select Risk/i }));

    expect(onChange).toHaveBeenCalledWith(["risk"]);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("shows selected departments as tags when pinned", () => {
    renderDepartmentTargetBar({ autoRoute: false, selected: ["risk"] });

    const chip = document.querySelector(".dept-target-tag-chip");
    expect(chip).toHaveTextContent("Risk");
    expect(screen.getByRole("button", { name: /Remove Risk/i })).toHaveClass(
      "dept-target-tag-remove",
    );
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("removes pinned department via inline remove", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    renderDepartmentTargetBar({ autoRoute: false, selected: ["risk"], onChange });

    await user.click(screen.getByRole("button", { name: /Remove Risk/i }));
    expect(onChange).toHaveBeenCalledWith([]);
  });

  it("enables auto-route when the inactive chip is clicked", async () => {
    const user = userEvent.setup();
    const onAutoRouteChange = vi.fn();
    renderDepartmentTargetBar({
      autoRoute: false,
      selected: ["risk"],
      onAutoRouteChange,
    });

    await user.click(screen.getByRole("button", { name: /Enable auto-route/i }));
    expect(onAutoRouteChange).toHaveBeenCalledWith(true);
  });

  it("closes picker modal with Escape", async () => {
    const user = userEvent.setup();
    renderDepartmentTargetBar({ autoRoute: false });

    await user.click(screen.getByRole("button", { name: /Add department/i }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    await user.keyboard("{Escape}");
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
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
