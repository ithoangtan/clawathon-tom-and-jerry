import type { Department, Lang } from "./types";

/** Mirror of app/common/departments.py — single source for UI labels & colors. */
export interface DepartmentMeta {
  key: Department;
  name_en: string;
  name_vi: string;
  accent_color: string;
  channel_hint: string;
}

export const DEPARTMENTS: DepartmentMeta[] = [
  {
    key: "risk",
    name_en: "Risk",
    name_vi: "Quản lý Rủi ro",
    accent_color: "#E63946",
    channel_hint: "teams-risk-knowledge",
  },
  {
    key: "grow_enablement",
    name_en: "Grow Enablement",
    name_vi: "Phát triển Kinh doanh",
    accent_color: "#2A9D8F",
    channel_hint: "teams-grow-enablement-knowledge",
  },
  {
    key: "bank_partnerships",
    name_en: "Bank Partnerships",
    name_vi: "Đối tác Ngân hàng",
    accent_color: "#457B9D",
    channel_hint: "teams-bank-partnerships-knowledge",
  },
];

export const ROLES = ["engineer", "pm", "ops", "risk", "business"] as const;

export function getDepartment(key: Department): DepartmentMeta {
  const dept = DEPARTMENTS.find((d) => d.key === key);
  if (!dept) throw new Error(`Unknown department: ${key}`);
  return dept;
}

export function departmentLabel(key: Department, locale: Lang): string {
  const dept = getDepartment(key);
  return locale === "vi" ? dept.name_vi : dept.name_en;
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
