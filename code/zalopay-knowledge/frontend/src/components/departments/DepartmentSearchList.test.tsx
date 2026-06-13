import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DepartmentPickerModal } from "./DepartmentPickerModal";
import { DepartmentTargetTag } from "./DepartmentTargetTag";
import { DepartmentSearchList } from "./DepartmentSearchList";
import type { DepartmentMeta } from "@/lib/departments";
import { renderWithUser } from "@/test/test-utils";
import type { Department } from "@/lib/types";

const scaleCatalog: DepartmentMeta[] = Array.from({ length: 24 }, (_, index) => ({
  key: `dept_${index}` as Department,
  name_en: `Department ${index}`,
  name_vi: `Phòng ban ${index}`,
  accent_color: "#336699",
  channel_hint: `teams-dept-${index}`,
  head_manager_en: `Manager ${index}`,
  head_manager_vi: `Quản lý ${index}`,
  description_en: `Internal documentation scope ${index}.`,
  description_vi: `Phạm vi tài liệu nội bộ ${index}.`,
}));

describe("DepartmentSearchList", () => {
  it("renders searchable rows with name, head, and description snippet", () => {
    renderWithUser(
      <DepartmentSearchList selected={[]} onChange={vi.fn()} departments={scaleCatalog} />,
    );

    expect(screen.getByRole("option", { name: /Department 0/i })).toBeInTheDocument();
    expect(screen.getByText("Manager 0")).toBeInTheDocument();
    expect(screen.getByText(/Internal documentation scope 0/)).toBeInTheDocument();
  });

  it("filters results by head manager and description", async () => {
    const user = userEvent.setup();
    renderWithUser(
      <DepartmentSearchList selected={[]} onChange={vi.fn()} departments={scaleCatalog} />,
    );

    await user.type(screen.getByRole("searchbox"), "Manager 17");
    expect(screen.getAllByRole("option")).toHaveLength(1);
    expect(screen.getByText("Department 17")).toBeInTheDocument();

    await user.clear(screen.getByRole("searchbox"));
    await user.type(screen.getByRole("searchbox"), "scope 3");
    expect(screen.getAllByRole("option")).toHaveLength(1);
    expect(screen.getByText("Department 3")).toBeInTheDocument();
  });

  it("supports multi-select toggling", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    renderWithUser(
      <DepartmentSearchList
        selected={[]}
        onChange={onChange}
        departments={scaleCatalog.slice(0, 3)}
      />,
    );

    await user.click(screen.getByRole("option", { name: /Department 0/i }));
    expect(onChange).toHaveBeenCalledWith(["dept_0"]);
  });

  it("shows empty state when nothing matches", async () => {
    const user = userEvent.setup();
    renderWithUser(
      <DepartmentSearchList selected={[]} onChange={vi.fn()} departments={scaleCatalog} />,
    );

    await user.type(screen.getByRole("searchbox"), "zzzz-no-match");
    expect(screen.getByText(/No departments match/i)).toBeInTheDocument();
  });

  it("uses scroll container for long lists", () => {
    const { container } = render(
      <DepartmentSearchList selected={[]} onChange={vi.fn()} departments={scaleCatalog} />,
    );

    const listbox = container.querySelector('[role="listbox"]');
    expect(listbox?.className).toMatch(/max-h-/);
    expect(listbox?.className).toMatch(/overflow-y-auto/);
  });
});

describe("DepartmentPickerModal", () => {
  it("filters, selects, and deselects departments without closing", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    renderWithUser(
      <DepartmentPickerModal
        open
        onClose={vi.fn()}
        selected={["dept_2"]}
        onChange={onChange}
        departments={scaleCatalog.slice(0, 4)}
      />,
    );

    await user.type(screen.getByRole("searchbox"), "Department 2");
    await user.click(screen.getByRole("button", { name: /Deselect Department 2/i }));

    expect(onChange).toHaveBeenCalledWith([]);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("filters and selects departments without closing", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    renderWithUser(
      <DepartmentPickerModal
        open
        onClose={vi.fn()}
        selected={[]}
        onChange={onChange}
        departments={scaleCatalog.slice(0, 4)}
      />,
    );

    await user.type(screen.getByRole("searchbox"), "Department 2");
    await user.click(screen.getByRole("button", { name: /Select Department 2/i }));

    expect(onChange).toHaveBeenCalledWith(["dept_2"]);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("expands one row at a time with details and select action", async () => {
    const user = userEvent.setup();
    renderWithUser(
      <DepartmentPickerModal
        open
        onClose={vi.fn()}
        selected={[]}
        onChange={vi.fn()}
        departments={scaleCatalog.slice(0, 3)}
      />,
    );

    const rows = screen.getAllByRole("option");
    await user.click(rows[0]);
    expect(rows[0]).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("button", { name: "Select" })).toBeInTheDocument();

    await user.click(rows[1]);
    expect(rows[0]).toHaveAttribute("aria-expanded", "false");
    expect(rows[1]).toHaveAttribute("aria-expanded", "true");
  });
});

describe("DepartmentTargetTag", () => {
  it("keeps inline remove button at the trailing edge of the chip", () => {
    const onRemove = vi.fn();
    renderWithUser(<DepartmentTargetTag deptKey="risk" onRemove={onRemove} />);

    const chip = document.querySelector(".dept-target-tag-chip");
    const removeBtn = screen.getByRole("button", { name: /Remove Risk/i });

    expect(chip).toContainElement(removeBtn);
    expect(removeBtn).toHaveClass("dept-target-tag-remove");
  });

  it("shows rich tooltip on focus and removes via inline button", async () => {
    const user = userEvent.setup();
    const onRemove = vi.fn();
    renderWithUser(<DepartmentTargetTag deptKey="risk" onRemove={onRemove} />);

    await user.tab();
    const tooltip = screen.getByRole("tooltip");
    expect(tooltip).toBeInTheDocument();
    expect(tooltip.parentElement).toBe(document.body);
    expect(tooltip).toHaveClass("dept-tag-tooltip--portal");
    expect(screen.getByText(/Lan Nguyen/)).toBeInTheDocument();
    expect(tooltip.querySelector(".dept-target-tag-remove")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Remove Risk/i }));
    expect(onRemove).toHaveBeenCalledWith("risk");
  });
});
