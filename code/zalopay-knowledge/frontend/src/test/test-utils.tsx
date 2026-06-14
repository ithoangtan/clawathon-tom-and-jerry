import { render, type RenderOptions } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { useSessionStore } from "@/store/sessionStore";
import { useSidebarStore } from "@/store/sidebarStore";
import { useUserStore } from "@/store/userStore";
import type { UserContext } from "@/lib/types";

const defaultUserContext: UserContext = {
  userId: "user-test123",
  sessionId: "sess-test456",
  role: "engineer",
  homeDept: "risk",
  locale: "en",
};

export function resetSessionStore() {
  useSessionStore.setState({ threads: {}, sessionAction: null });
  useSessionStore.persist?.clearStorage?.();
}

export function resetUserStore(overrides: Partial<UserContext> = {}) {
  useUserStore.setState({ ...defaultUserContext, ...overrides });
  useUserStore.persist?.clearStorage?.();
}

export function resetSidebarStore() {
  useSidebarStore.setState({ open: false });
  useSidebarStore.persist?.clearStorage?.();
}

export function resetStores(overrides: Partial<UserContext> = {}) {
  resetUserStore(overrides);
  resetSessionStore();
  resetSidebarStore();
}

export function renderWithUser(ui: ReactElement, user: Partial<UserContext> = {}, options?: RenderOptions) {
  resetUserStore(user);
  return render(ui, options);
}

export function renderWithRouter(
  ui: ReactElement,
  initialPath = "/",
  user: Partial<UserContext> = {},
  options?: RenderOptions,
) {
  resetUserStore(user);
  return render(<MemoryRouter initialEntries={[initialPath]}>{ui}</MemoryRouter>, options);
}
