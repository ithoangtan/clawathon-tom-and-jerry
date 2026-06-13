import { describe, expect, it } from "vitest";
import { DEPARTMENTS, departmentLabel, getDepartment, roleLabel, ROLES } from "./departments";

describe("departments", () => {
  it("exports all three departments", () => {
    expect(DEPARTMENTS).toHaveLength(3);
    expect(DEPARTMENTS.map((d) => d.key)).toEqual([
      "risk",
      "grow_enablement",
      "bank_partnerships",
    ]);
  });

  it("returns Vietnamese label", () => {
    expect(departmentLabel("risk", "vi")).toBe("Quản lý Rủi ro");
  });

  it("returns English label", () => {
    expect(departmentLabel("grow_enablement", "en")).toBe("Grow Enablement");
  });

  it("returns accent color from getDepartment", () => {
    expect(getDepartment("bank_partnerships").accent_color).toBe("#457B9D");
    expect(getDepartment("risk").channel_hint).toBe("teams-risk-knowledge");
  });

  it("throws for unknown department", () => {
    expect(() => getDepartment("unknown" as "risk")).toThrow("Unknown department");
  });

  it("returns role labels in both locales", () => {
    expect(roleLabel("engineer", "en")).toBe("Engineer");
    expect(roleLabel("engineer", "vi")).toBe("Kỹ sư");
    expect(roleLabel("pm", "en")).toBe("Product Manager");
  });

  it("falls back to raw role for unknown roles", () => {
    expect(roleLabel("custom", "en")).toBe("custom");
  });

  it("defines expected roles", () => {
    expect(ROLES).toContain("engineer");
    expect(ROLES).toContain("business");
  });
});
