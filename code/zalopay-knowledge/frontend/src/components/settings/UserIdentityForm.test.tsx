import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { UserIdentityForm } from "./UserIdentityForm";
import { getUserContext } from "@/store/userStore";
import { renderWithUser } from "@/test/test-utils";

describe("UserIdentityForm", () => {
  it("saves updated identity fields to the store", async () => {
    const user = userEvent.setup();
    renderWithUser(<UserIdentityForm />);

    const userIdInput = screen.getByLabelText(/User ID/i);
    fireEvent.change(userIdInput, { target: { value: "user-saved-99" } });

    fireEvent.change(screen.getByLabelText(/Role/i), { target: { value: "pm" } });
    await user.click(screen.getByRole("option", { name: /Grow Enablement/i }));
    fireEvent.change(screen.getByLabelText(/Language/i), { target: { value: "vi" } });

    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent("Đã lưu");
    });

    expect(getUserContext()).toMatchObject({
      userId: "user-saved-99",
      role: "pm",
      homeDept: "grow_enablement",
      locale: "vi",
    });
  });

  it("keeps save disabled until a field changes", () => {
    renderWithUser(<UserIdentityForm />);
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });

  it("renders Vietnamese labels when locale is vi", () => {
    renderWithUser(<UserIdentityForm />, { locale: "vi" });
    expect(screen.getByText("Danh tính của bạn")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Lưu" })).toBeDisabled();
  });
});
