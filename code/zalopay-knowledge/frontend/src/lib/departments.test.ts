import { describe, expect, it } from "vitest";
import {
  DEPARTMENTS,
  departmentHeadManager,
  departmentLabel,
  descriptionSnippet,
  filterDepartments,
  getDepartment,
  roleLabel,
  ROLES,
  type DepartmentMeta,
} from "./departments";
import type { Department } from "./types";

describe("departments", () => {
  it("exports all three departments", () => {
    expect(DEPARTMENTS).toHaveLength(3);
    expect(DEPARTMENTS.map((d) => d.key)).toEqual([
      "risk",
      "grow_enablement",
      "bank_partnerships",
    ]);
  });

  it("includes head manager and description metadata", () => {
    const risk = getDepartment("risk");
    expect(risk.head_manager_en).toBeTruthy();
    expect(risk.head_manager_vi).toBeTruthy();
    expect(risk.description_en).toBeTruthy();
    expect(risk.description_vi).toBeTruthy();
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

  it("truncates long descriptions", () => {
    const long = "a".repeat(120);
    expect(descriptionSnippet(long, 40)).toHaveLength(40);
    expect(descriptionSnippet(long, 40).endsWith("…")).toBe(true);
  });

  it("filters by department name", () => {
    const results = filterDepartments(DEPARTMENTS, "bank", "en");
    expect(results.map((d) => d.key)).toEqual(["bank_partnerships"]);
  });

  it("filters by head manager name", () => {
    const results = filterDepartments(DEPARTMENTS, "Nguyễn Thị Lan", "vi");
    expect(results.map((d) => d.key)).toEqual(["risk"]);
  });

  it("filters by description text", () => {
    const results = filterDepartments(DEPARTMENTS, "settlement", "en");
    expect(results.map((d) => d.key)).toEqual(["bank_partnerships"]);
  });

  it("returns all departments for empty query", () => {
    expect(filterDepartments(DEPARTMENTS, "   ", "en")).toHaveLength(DEPARTMENTS.length);
  });

  it("scales to 20+ departments without changing filter semantics", () => {
    const scaleCatalog: DepartmentMeta[] = Array.from({ length: 25 }, (_, index) => {
      const key = `dept_${index}` as Department;
      return {
        key,
        name_en: `Department ${index}`,
        name_vi: `Phòng ban ${index}`,
        accent_color: "#000000",
        channel_hint: `teams-dept-${index}`,
        head_manager_en: `Manager ${index}`,
        head_manager_vi: `Quản lý ${index}`,
        description_en: `Coverage area ${index} for internal docs.`,
        description_vi: `Phạm vi ${index} cho tài liệu nội bộ.`,
      };
    });

    expect(filterDepartments(scaleCatalog, "manager 19", "en")).toHaveLength(1);
    expect(filterDepartments(scaleCatalog, "phạm vi 22", "vi")).toHaveLength(1);
    expect(departmentHeadManager(scaleCatalog[0], "en")).toBe("Manager 0");
  });
});
