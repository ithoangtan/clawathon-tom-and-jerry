import { CopyButton } from "@/components/markdown/CopyButton";
import { renderWithUser } from "@/test/test-utils";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

describe("CopyButton", () => {
  it("copies text to clipboard and shows copied state", async () => {
    const user = userEvent.setup();
    renderWithUser(<CopyButton text="hello world" label="Copy snippet" />);

    const button = screen.getByRole("button", { name: "Copy snippet" });
    await user.click(button);

    expect(await screen.findByRole("button", { name: "Copied!" })).toBeInTheDocument();
  });
});
