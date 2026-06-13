import { beforeEach, describe, expect, it } from "vitest";
import { useSidebarStore } from "./sidebarStore";

describe("sidebarStore", () => {
  beforeEach(() => {
    useSidebarStore.setState({ open: false });
    useSidebarStore.persist?.clearStorage?.();
  });

  it("defaults to closed", () => {
    expect(useSidebarStore.getState().open).toBe(false);
  });

  it("persists open state", () => {
    useSidebarStore.getState().setOpen(true);
    expect(useSidebarStore.getState().open).toBe(true);

    const raw = localStorage.getItem("zalopay-knowledge-sidebar");
    expect(raw).toContain('"open":true');
  });

  it("toggles open state", () => {
    useSidebarStore.getState().toggle();
    expect(useSidebarStore.getState().open).toBe(true);
    useSidebarStore.getState().toggle();
    expect(useSidebarStore.getState().open).toBe(false);
  });
});
