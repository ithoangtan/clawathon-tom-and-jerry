import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, beforeEach, vi } from "vitest";

/** Shared clipboard mock for copy-button tests. */
export const clipboardWriteTextMock = vi.fn().mockResolvedValue(undefined);

function installClipboardMock() {
  clipboardWriteTextMock.mockClear();
  clipboardWriteTextMock.mockResolvedValue(undefined);
  try {
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: clipboardWriteTextMock },
      configurable: true,
      writable: true,
    });
  } catch {
    vi.stubGlobal("navigator", {
      ...navigator,
      clipboard: { writeText: clipboardWriteTextMock },
    });
  }
}

beforeEach(() => {
  localStorage.clear();
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal(
    "ResizeObserver",
    class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    },
  );
  installClipboardMock();
  Object.defineProperty(document, "execCommand", {
    value: vi.fn(() => true),
    configurable: true,
    writable: true,
  });
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve(
        new Response(JSON.stringify({}), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    ),
  );
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
