import { describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";
import { screen } from "@testing-library/react";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { renderWithUser } from "@/test/test-utils";
import { useUserStore } from "@/store/userStore";

describe("LanguageSwitcher", () => {
  it("switches locale immediately without saving settings", async () => {
    const user = userEvent.setup();
    renderWithUser(<LanguageSwitcher />, { locale: "en" });

    await user.click(screen.getByRole("button", { name: "Switch to Vietnamese" }));

    expect(useUserStore.getState().locale).toBe("vi");
    expect(screen.getByRole("button", { name: "Chuyển sang tiếng Việt" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("exposes a language group label", () => {
    renderWithUser(<LanguageSwitcher />, { locale: "vi" });

    expect(screen.getByRole("group", { name: "Ngôn ngữ" })).toBeInTheDocument();
  });
});
