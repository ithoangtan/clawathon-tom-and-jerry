import { render, type RenderOptions } from "@testing-library/react";
import type { ReactElement } from "react";
import { useUserStore } from "@/store/userStore";
import type { UserContext } from "@/lib/types";

const defaultUserContext: UserContext = {
  userId: "user-test123",
  sessionId: "sess-test456",
  role: "engineer",
  homeDept: "risk",
  locale: "en",
};

export function resetUserStore(overrides: Partial<UserContext> = {}) {
  useUserStore.setState({ ...defaultUserContext, ...overrides });
  useUserStore.persist?.clearStorage?.();
}

export function renderWithUser(ui: ReactElement, user: Partial<UserContext> = {}, options?: RenderOptions) {
  resetUserStore(user);
  return render(ui, options);
}
