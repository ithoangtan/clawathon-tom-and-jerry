import { beforeEach, describe, expect, it, vi } from "vitest";
import { getUserContext, useUserStore } from "./userStore";

describe("userStore", () => {
  beforeEach(() => {
    localStorage.clear();
    useUserStore.setState({
      userId: "user-initial",
      sessionId: "sess-initial",
      role: "business",
      homeDept: "risk",
      locale: "en",
    });
  });

  it("exposes default-like state after reset", () => {
    const state = useUserStore.getState();
    expect(state.userId).toBe("user-initial");
    expect(state.role).toBe("business");
    expect(state.homeDept).toBe("risk");
    expect(state.locale).toBe("en");
  });

  it("updates userId via setUserId", () => {
    useUserStore.getState().setUserId("user-updated");
    expect(useUserStore.getState().userId).toBe("user-updated");
  });

  it("updates role via setRole", () => {
    useUserStore.getState().setRole("engineer");
    expect(useUserStore.getState().role).toBe("engineer");
  });

  it("updates homeDept via setHomeDept", () => {
    useUserStore.getState().setHomeDept("bank_partnerships");
    expect(useUserStore.getState().homeDept).toBe("bank_partnerships");
  });

  it("updates locale via setLocale", () => {
    useUserStore.getState().setLocale("vi");
    expect(useUserStore.getState().locale).toBe("vi");
  });

  it("generates new session id on newSession", () => {
    const before = useUserStore.getState().sessionId;
    vi.stubGlobal("crypto", { randomUUID: () => "new-session-uuid" });
    useUserStore.getState().newSession();
    expect(useUserStore.getState().sessionId).toBe("sess-new-session-uuid");
    expect(useUserStore.getState().sessionId).not.toBe(before);
    vi.unstubAllGlobals();
  });

  it("applies partial updates via update", () => {
    useUserStore.getState().update({ role: "pm", locale: "vi" });
    const state = useUserStore.getState();
    expect(state.role).toBe("pm");
    expect(state.locale).toBe("vi");
    expect(state.userId).toBe("user-initial");
  });

  it("getUserContext returns current context fields", () => {
    useUserStore.setState({
      userId: "user-ctx",
      sessionId: "sess-ctx",
      role: "ops",
      homeDept: "grow_enablement",
      locale: "vi",
    });

    expect(getUserContext()).toEqual({
      userId: "user-ctx",
      sessionId: "sess-ctx",
      role: "ops",
      homeDept: "grow_enablement",
      locale: "vi",
    });
  });
});
