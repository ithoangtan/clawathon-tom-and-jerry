import { describe, expect, it, vi } from "vitest";
import {
  classNames,
  formatConfidence,
  formatDate,
  formatFreshnessHours,
  formatMs,
  formatPercent,
  freshnessLevel,
  generateSessionId,
  generateUserId,
} from "./format";

describe("formatPercent", () => {
  it("formats decimal as percentage with one decimal", () => {
    expect(formatPercent(0.081)).toBe("8.1%");
    expect(formatPercent(0)).toBe("0.0%");
    expect(formatPercent(1)).toBe("100.0%");
  });
});

describe("formatMs", () => {
  it("shows milliseconds below 1000", () => {
    expect(formatMs(250)).toBe("250 ms");
    expect(formatMs(999)).toBe("999 ms");
  });

  it("shows seconds at or above 1000", () => {
    expect(formatMs(1000)).toBe("1.0 s");
    expect(formatMs(2500)).toBe("2.5 s");
  });
});

describe("formatConfidence", () => {
  it("rounds to whole percent", () => {
    expect(formatConfidence(0.856)).toBe("86%");
    expect(formatConfidence(0.5)).toBe("50%");
  });
});

describe("formatDate", () => {
  it("returns em dash for nullish values", () => {
    expect(formatDate(null, "en")).toBe("—");
    expect(formatDate(undefined, "vi")).toBe("—");
  });

  it("formats valid ISO strings", () => {
    const result = formatDate("2024-06-15T10:30:00.000Z", "en");
    expect(result).not.toBe("—");
    expect(result).toContain("2024");
  });

  it("returns raw string on invalid date", () => {
    expect(formatDate("not-a-date", "en")).toBe("not-a-date");
  });
});

describe("formatFreshnessHours", () => {
  it("returns em dash for nullish", () => {
    expect(formatFreshnessHours(null)).toBe("—");
    expect(formatFreshnessHours(undefined)).toBe("—");
  });

  it("shows sub-hour freshness", () => {
    expect(formatFreshnessHours(0.5)).toBe("< 1h ago");
  });

  it("shows hours under 24", () => {
    expect(formatFreshnessHours(5)).toBe("5h ago");
  });

  it("shows days at 24h or more", () => {
    expect(formatFreshnessHours(48)).toBe("2d ago");
  });
});

describe("freshnessLevel", () => {
  it("returns red when never synced", () => {
    expect(freshnessLevel(null, null)).toBe("red");
    expect(freshnessLevel(undefined, 12)).toBe("red");
  });

  it("returns green within 24h", () => {
    expect(freshnessLevel("2024-01-01", 12)).toBe("green");
    expect(freshnessLevel("2024-01-01", 24)).toBe("green");
  });

  it("returns amber when synced but stale", () => {
    expect(freshnessLevel("2024-01-01", 25)).toBe("amber");
    expect(freshnessLevel("2024-01-01", null)).toBe("amber");
  });
});

describe("generateSessionId", () => {
  it("prefixes sess- and uses uuid", () => {
    vi.stubGlobal("crypto", { randomUUID: () => "abc-def-ghi" });
    expect(generateSessionId()).toBe("sess-abc-def-ghi");
    vi.unstubAllGlobals();
  });
});

describe("generateUserId", () => {
  it("prefixes user- and truncates uuid", () => {
    vi.stubGlobal("crypto", { randomUUID: () => "12345678-abcd-efgh" });
    expect(generateUserId()).toBe("user-12345678");
    vi.unstubAllGlobals();
  });
});

describe("classNames", () => {
  it("joins truthy parts and skips falsy", () => {
    expect(classNames("a", false, null, undefined, "b")).toBe("a b");
    expect(classNames()).toBe("");
  });
});
