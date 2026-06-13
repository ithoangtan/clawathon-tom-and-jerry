import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { FeedbackBar } from "./FeedbackBar";
import { api } from "@/lib/apiClient";

vi.mock("@/lib/apiClient", () => ({
  api: {
    feedback: vi.fn(),
  },
}));

describe("FeedbackBar", () => {
  beforeEach(() => {
    vi.mocked(api.feedback).mockReset();
  });

  it("submits thumbs up with optional comment on click", async () => {
    vi.mocked(api.feedback).mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(<FeedbackBar feedbackId="fb-test-1" />);

    await user.type(
      screen.getByLabelText(/Optional comment/i),
      "Very clear answer",
    );
    await user.click(screen.getByRole("button", { name: "Thumbs up" }));

    await waitFor(() => {
      expect(api.feedback).toHaveBeenCalledWith(
        {
          feedback_id: "fb-test-1",
          rating: "up",
          comment: "Very clear answer",
        },
        expect.objectContaining({ role: expect.any(String) }),
      );
    });

    expect(screen.getByRole("status")).toHaveTextContent("Thanks for your feedback!");
  });

  it("submits thumbs down without comment", async () => {
    vi.mocked(api.feedback).mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(<FeedbackBar feedbackId="fb-test-2" />);
    await user.click(screen.getByRole("button", { name: "Thumbs down" }));

    await waitFor(() => {
      expect(api.feedback).toHaveBeenCalledWith(
        {
          feedback_id: "fb-test-2",
          rating: "down",
          comment: null,
        },
        expect.any(Object),
      );
    });
  });

  it("shows error and retry on failure", async () => {
    vi.mocked(api.feedback)
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce(undefined);
    const user = userEvent.setup();

    render(<FeedbackBar feedbackId="fb-test-3" />);
    await user.click(screen.getByRole("button", { name: "Thumbs up" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Network error");

    await user.click(screen.getByRole("button", { name: "Retry" }));

    await waitFor(() => {
      expect(api.feedback).toHaveBeenCalledTimes(2);
    });
  });
});
