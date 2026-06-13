import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  gsap,
  REDUCED_MOTION_QUERY,
  runMessageEnter,
  runStaggerEnter,
} from "./gsap";
import { useSmoothScroll } from "@/hooks/useSmoothScroll";

function setReducedMotion(matches: boolean) {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: query === REDUCED_MOTION_QUERY ? matches : false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
}

function ScrollProbe({ tick }: { tick: number }) {
  const ref = useSmoothScroll([tick]);
  return (
    <div
      ref={ref}
      data-testid="scroll-container"
      style={{ height: 100, overflow: "auto" }}
    >
      <div style={{ height: 500 }}>content</div>
    </div>
  );
}

describe("gsap reduced motion", () => {
  beforeEach(() => {
    vi.spyOn(gsap, "from");
    vi.spyOn(gsap, "to");
    vi.spyOn(gsap, "set");
    vi.stubGlobal("requestAnimationFrame", (cb: FrameRequestCallback) => {
      cb(0);
      return 1;
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("runMessageEnter skips animation when prefers-reduced-motion is enabled", () => {
    setReducedMotion(true);
    const el = document.createElement("article");
    document.body.appendChild(el);

    const cleanup = runMessageEnter(el, "assistant");
    cleanup();

    expect(gsap.set).toHaveBeenCalledWith(
      el,
      expect.objectContaining({ opacity: 1, x: 0, y: 0, scale: 1 }),
    );
    expect(gsap.from).not.toHaveBeenCalled();
  });

  it("runMessageEnter animates entrance when motion is allowed", () => {
    const matchMediaRevert = vi.fn();
    vi.spyOn(gsap, "matchMedia").mockReturnValue({
      add: (_query, cb) => {
        cb({ conditions: { reduceMotion: false } });
        return { revert: matchMediaRevert } as never;
      },
      revert: matchMediaRevert,
    } as never);

    const el = document.createElement("article");
    document.body.appendChild(el);

    const cleanup = runMessageEnter(el, "user");

    expect(gsap.from).toHaveBeenCalledWith(
      el,
      expect.objectContaining({ opacity: 0, x: 18, y: 12, scale: 0.96 }),
    );
    cleanup();
    expect(matchMediaRevert).toHaveBeenCalled();
  });

  it("runStaggerEnter sets final state without stagger when reduced motion is on", () => {
    setReducedMotion(true);
    const items = [document.createElement("li"), document.createElement("li")];

    const cleanup = runStaggerEnter(items);

    expect(gsap.set).toHaveBeenCalledWith(
      items,
      expect.objectContaining({ opacity: 1, y: 0 }),
    );
    expect(gsap.from).not.toHaveBeenCalled();
    cleanup();
  });

  it("useSmoothScroll uses instant scroll when reduced motion is enabled", () => {
    setReducedMotion(true);
    const { rerender } = render(<ScrollProbe tick={1} />);
    const container = screen.getByTestId("scroll-container");

    Object.defineProperty(container, "scrollHeight", { value: 500, configurable: true });
    Object.defineProperty(container, "clientHeight", { value: 100, configurable: true });
    container.scrollTop = 0;

    rerender(<ScrollProbe tick={2} />);

    expect(container.scrollTop).toBe(400);
    expect(gsap.to).not.toHaveBeenCalled();
  });
});
