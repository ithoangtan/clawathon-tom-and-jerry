/**
 * departments.ts — UI catalog derived from app/common/departments.py
 *
 * Data is exported to departments.data.json via scripts/export_departments.py.
 * Run that script after editing the Python registry.
 */

import type { Department, Lang } from "./types";
import catalog from "./departments.data.json";

export interface DepartmentMeta {
  key: Department;
  name_en: string;
  name_vi: string;
  accent_color: string;
  channel_hint: string;
  head_manager_en: string;
  head_manager_vi: string;
  description_en: string;
  description_vi: string;
}

export const DEPARTMENTS = catalog.departments as DepartmentMeta[];

export const ROLES = catalog.roles as readonly string[];

export function getDepartment(key: Department): DepartmentMeta {
  const dept = DEPARTMENTS.find((d) => d.key === key);
  if (!dept) throw new Error(`Unknown department: ${key}`);
  return dept;
}

export function departmentLabel(key: Department, locale: Lang): string {
  const dept = getDepartment(key);
  return departmentMetaLabel(dept, locale);
}

export function departmentMetaLabel(dept: DepartmentMeta, locale: Lang): string {
  return locale === "vi" ? dept.name_vi : dept.name_en;
}

export function departmentHeadManager(dept: DepartmentMeta, locale: Lang): string {
  return locale === "vi" ? dept.head_manager_vi : dept.head_manager_en;
}

export function departmentDescription(dept: DepartmentMeta, locale: Lang): string {
  return locale === "vi" ? dept.description_vi : dept.description_en;
}

/** Truncate long descriptions for compact list rows. */
export function descriptionSnippet(text: string, maxLen = 96): string {
  const trimmed = text.trim();
  if (trimmed.length <= maxLen) return trimmed;
  return `${trimmed.slice(0, maxLen - 1).trimEnd()}…`;
}

/** Case-insensitive filter across name, head manager, and description. */
export function filterDepartments(
  departments: DepartmentMeta[],
  query: string,
  locale: Lang,
): DepartmentMeta[] {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return departments;

  return departments.filter((dept) => {
    const haystack = [
      departmentMetaLabel(dept, locale),
      departmentHeadManager(dept, locale),
      departmentDescription(dept, locale),
      dept.key.replace(/_/g, " "),
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(normalized);
  });
}

export function roleLabel(role: string, locale: Lang): string {
  const labels: Record<string, { en: string; vi: string }> = {
    engineer: { en: "Engineer", vi: "Kỹ sư" },
    pm: { en: "Product Manager", vi: "Quản lý Sản phẩm" },
    ops: { en: "Operations", vi: "Vận hành" },
    risk: { en: "Risk / Compliance", vi: "Rủi ro / Tuân thủ" },
    business: { en: "Business", vi: "Kinh doanh" },
  };
  const entry = labels[role] ?? { en: role, vi: role };
  return locale === "vi" ? entry.vi : entry.en;
}

/** Registry-ordered department keys (for tests and fixtures). */
export const DEPARTMENT_KEYS: readonly Department[] = DEPARTMENTS.map((d) => d.key);
