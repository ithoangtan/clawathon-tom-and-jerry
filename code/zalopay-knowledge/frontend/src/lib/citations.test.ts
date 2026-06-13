import { describe, expect, it } from "vitest";
import {
  docTypeLabel,
  formatExcerpt,
  isCitationDeprecated,
  openSourceLabel,
} from "@/lib/citations";
import type { Citation } from "@/lib/types";

const base: Citation = {
  title: "Policy",
  url: "https://example.com",
  lifecycle_state: "active",
};

describe("citations helpers", () => {
  it("detects deprecated citations", () => {
    expect(isCitationDeprecated(base)).toBe(false);
    expect(isCitationDeprecated({ ...base, deprecated: true })).toBe(true);
    expect(isCitationDeprecated({ ...base, lifecycle_state: "deprecated" })).toBe(true);
  });

  it("truncates long excerpts", () => {
    const long = "a".repeat(500);
    const result = formatExcerpt(long);
    expect(result).toHaveLength(401);
    expect(result?.endsWith("…")).toBe(true);
  });

  it("returns null for empty excerpt", () => {
    expect(formatExcerpt("")).toBeNull();
    expect(formatExcerpt(undefined)).toBeNull();
  });

  it("labels open source by type", () => {
    expect(openSourceLabel("confluence", "en")).toBe("Open in Confluence");
    expect(openSourceLabel("gdrive", "vi")).toBe("Mở trong Drive");
  });

  it("labels doc types via i18n", () => {
    expect(docTypeLabel("confluence", "en")).toBe("Confluence");
    expect(docTypeLabel(null, "en")).toBe("Document");
  });
});
